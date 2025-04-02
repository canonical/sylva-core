#!/bin/env python
#
# Can be tested from outside a k8s cluster (assuming k8s creds are avail):
#
# OUT_OF_POD=true PINGMESH_CONFIG_PATH=test-pingmesh-config.yaml NAMESPACE=kube-system kustomize-units/pingmesh/pingmesh.py
#
# TODO:
# - add a "self test": did I register a destination pod for myself ?
# - add a "self test": did I register a destination node for my node ?
# - if not fail the livenessprobe
#
# PromQL: pingable{pingmesh_dest_type="pods"}

import asyncio
import collections
import os
import time
import subprocess
import copy
import logging
import contextlib
import threading
import yaml
import re
import kopf
import kubernetes
from kubernetes import client as k8s_client
import prometheus_client
import datetime

MY_NAMESPACE = os.environ.get('NAMESPACE','pingmesh')

############################### base config ######################################################

logger = logging.getLogger("pingmesh")

with open(os.environ.get('PINGMESH_CONFIG_PATH','/pingmesh-config.yaml'), 'r') as config_file:
  config = yaml.safe_load(config_file)

SELF_NODE_NAME = os.environ.get("NODENAME","unknown-node")

############################### main datastructures ##############################################

class Destination():
    def __init__(self, dest_type, name, remote, key=None, name_is_a_nodename=False, **kwargs) -> None:
        self.dest_type = dest_type
        self.name = name
        self.remote = remote  # IP or Hostname
        if key:
            self.key = key
        else:
            self.key = self.name
        self.name_is_a_nodename = name_is_a_nodename
        self.properties = kwargs
        self.metric_refs = set()

    def __hash__(self):
        return hash((self.dest_type, self.key))

    def __eq__(self, other):
        return self.dest_type == other.dest_type and self.key == other.key

    def __repr__(self):
        k_string = (f"[{self.key}]" if self.key != self.name else "")
        return f"<Destination {self.dest_type} - {self.name}{k_string} remote={self.remote} props={self.properties}>"

    def add_metric(self, parent_metric, metric):
        self.metric_refs.add( (parent_metric, metric._labelvalues) )

    def get_metric_labels(self):
        return {
            "pingmesh_dest_type": self.dest_type,
            "pingmesh_destination_name": self.name,
            "pingmesh_destination_remote": self.remote,
        }

    def __del__(self):
        if self.metric_refs:
            logger.info(f"deleting metrics for {self}")
            for parent_metric, label_values in self.metric_refs:
                logger.info(f"removing [{label_values}] from metric {parent_metric}")
                parent_metric.remove(*label_values)

class Destinations():
    # distinct destination having distict dest.key
    # two distinct destination can have same name
    #   (this is the case for pod-to-pod tests, where the destination name is the _node_ name)

    def __init__(self) -> None:
        self.dests_by_dest_type_and_key = dict()
        self.dests_by_remote = dict()
        self.dests_by_name = collections.defaultdict(set)

    def register_destination(self, destination):
        if (destination.dest_type, destination.key) not in self.dests_by_dest_type_and_key:
            self.dests_by_dest_type_and_key[destination.dest_type, destination.key] = destination
            self.dests_by_remote[destination.remote] = destination
            self.dests_by_name[destination.name].add(destination)
            logger.info(f"Added destination: {destination}")
        else:
            logger.info(f"we already had a destination registered for {destination}")

    def remove_destination(self, dest_type, key):
        try:
            dest = self.dests_by_dest_type_and_key[dest_type, key]
            del self.dests_by_dest_type_and_key[dest_type, key]
            del self.dests_by_remote[dest.remote]
            self.dests_by_name[dest.name].discard(dest)
            if len(self.dests_by_name[dest.name]) == 0:
                del self.dests_by_name[dest.name]
            logger.info(f"forgetting {dest}")
            del dest
        except KeyError as e:
            logger.info(f"destination already removed: {e}")
            pass

    def get_destination_by_remote(self, remote):
        return self.dests_by_remote.get(remote)

    def get_destinations_by_name(self, name):
        return self.dests_by_name.get(name,set())

    def get_remotes(self):
        for dest in self.dests_by_dest_type_and_key.values():
            yield dest.remote

destinations=Destinations()


all_cluster_nodes = set()

all_pods = set()

############################### Static Destinations ##############################################

def register_static_destinations(config, destinations):
    for dest_name,dest_config in config["staticDestinations"].items():
        if dest_config is None:
            dest_config = dict()
        dest = Destination("static", dest_name, dest_config.get("ip", dest_name), **(dest_config.get("properties",{})))
        destinations.register_destination(dest)

############################### Kopf framework setup  ############################################

def kopf_thread(ready_flag: threading.Event,
                stop_flag: threading.Event,
                ):
    loop = asyncio.new_event_loop()
    # loop.set_exception_handler(kopf_loop_exception_handler) ######################## FIXME
    asyncio.set_event_loop(loop)
    with contextlib.closing(loop):

        kopf.configure(
            verbose=False, # log formatting
            debug=os.environ.get('KOPF_DEBUG','')
        )

        loop.run_until_complete(kopf.operator(
            namespace=MY_NAMESPACE,
            ready_flag=ready_flag,
            stop_flag=stop_flag,
            liveness_endpoint=("http://0.0.0.0/healthz" if not os.environ.get('OUT_OF_POD') else None),
        ))

def start_kopf_thread():
    ready_flag = threading.Event()
    stop_flag = threading.Event()
    thread = threading.Thread(target=kopf_thread, kwargs=dict(
        stop_flag=stop_flag,
        ready_flag=ready_flag,
    ))
    thread.start()
    ready_flag.wait()
    return (thread, stop_flag)

@kopf.on.startup()
def init_k8s(logger, **kwargs):
    if os.environ.get("OUT_OF_POD", False):
        logger.info("Running out of pod, loading from kubeconfig")
        kubernetes.config.load_kube_config()
    else:
        kubernetes.config.load_incluster_config()

@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    settings.posting.enabled = False
    settings.scanning.disabled = True

    # we need low-enough timers to catch lost API connections
    settings.watching.server_timeout = 60
    settings.watching.client_timeout = 120

@kopf.on.probe(id='now')
def get_current_timestamp(**kwargs):
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

# these handlers ensure that if the pod can't connect to k8s API
# the liveness probe will end up failing, and the pod will be restarted

@kopf.on.probe(id='nodes')
def fail_if_no_nodes_seen(**kwargs):
    if len(all_cluster_nodes) > 0:
        return len(all_cluster_nodes)
    else:
        raise Exception("failed probe, no cluster nodes seen yet")

@kopf.on.probe(id='pods')
def fail_if_no_pod_seen(**kwargs):
    if len(all_pods) > 0:
        return len(all_pods)
    else:
        raise Exception("failed probe, no pingmesh pod seen yet")

@kopf.on.probe(id="api")
def fail_api_access_failure(**kwargs):
    try:
        k8s_client.CoreV1Api().list_node()
    except:
        raise Exception("failed probe, API access")

############################### Kopf Hooks helpers ##############################################

def when_event_delete(event, **_):
    logger.info(f"event {event['type']} on {event['object']['kind']} {event['object']['metadata']['name']} {'has deletionTimestamp' if ('deletionTimestamp' in event['object']['metadata']) else ''}")
    return (event["type"] == "DELETED" or "deletionTimestamp" in event['object']['metadata'])

when_event_not_delete = lambda *args, **kwargs: not when_event_delete(*args,**kwargs)

############################### Kopf Hooks for Pods ##############################################

def forget_pod(pod_name):
    destinations.remove_destination("pods", pod_name)
    all_pods.discard(pod_name)

@kopf.on.event("pods.v1", labels=config.get("podLabelSelector",{}), when=when_event_not_delete)
def existing_pod(event, logger, name, status, meta, spec, **_):

    if "phase" not in status or status["phase"] != "Running":
        logger.info(f"forgetting pod {name}, which isn't running (status.phase: {status.get('phase')} / node: {spec['nodeName']})")
        forget_pod(name)
        return

    try:
        podName = name
        podIP = status["podIP"]
        nodeName = spec["nodeName"]
        all_pods.add(podName)
        destinations.register_destination(Destination("pods", nodeName, podIP, podName=podName, key=podName, name_is_a_nodename=True))
    except KeyError as e:
        logger.warning(f"pod {name}, can't find {e.args[0]}")

@kopf.on.event("pods.v1", labels=config.get("podLabelSelector",{}), when=when_event_delete)
def delete_pod(event, name, spec, **_):
    forget_pod(name)

def check_pods():
    api = k8s_client.CoreV1Api()
    all_pods_current = set([p.metadata.name for p in api.list_namespaced_pod(MY_NAMESPACE).items])
    for pod in (all_pods - all_pods_current):
        logger.info(f"pod {pod} does not exist anymore, forgetting")
        forget_pod(pod)

############################### Kopf Hooks for Nodes ##############################################

def forget_node(node_name):
    destinations.remove_destination("nodes", node_name)
    all_cluster_nodes.discard(node_name)

@kopf.on.event("nodes.v1", when=when_event_not_delete)
def existing_node(event, logger, name, status, meta, **_):

    if "deletionTimestamp" in meta:
        logger.info(f"node {name} being deleted, discarding")
        forget_node(name)
        return

    all_cluster_nodes.add(name)
    try:
        for entry in status["addresses"]:
            if entry["type"] == "InternalIP":
                nodeIP = entry["address"]
        if not nodeIP:
            logger.warning(f"no IP found for node {name}")
            return
        destinations.register_destination(Destination("nodes", name, nodeIP, name_is_a_nodename=True))
    except KeyError as e:
        logger.warning(f"node {name}, can't find {e.args[0]}")

@kopf.on.event("nodes.v1", when=when_event_delete)
def delete_node(event, logger, name, **_):
    forget_node(name)

def check_nodes():
    api = k8s_client.CoreV1Api()
    all_nodes_current = set([n.metadata.name for n in api.list_node().items])
    for node in (all_cluster_nodes - all_nodes_current):
        logger.info(f"node {node} does not exist anymore, forgetting")
        forget_node(node)

############################### fping ############################################################

def run_fping(test_name, test_config, destinations):
    remotes = list(destinations.get_remotes())
    logger.info(f"pinging {len(remotes)} destinations")
    fping_process = subprocess.run(["fping", "-C", "5", "-q", "--backoff", "1", "--timeout", "100"] + remotes,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT,
                                   universal_newlines=True)
    logger.debug(f"{test_name} results:\n{fping_process.stdout}")
    result_by_remote = dict()
    for line in fping_process.stdout.split('\n'):
        if not line:
            continue

        matches = re.match('^([^ ]+) +: (.+)+', line)

        if not matches:
            logger.warning(f"bogus fping result: {line}")
            continue

        remote = matches.group(1)

        if remote not in remotes:
            logger.warning(f"'{remote}' appears in fping output, although we didn't ask for it")
            continue

        results_str = matches.group(2)

        results = re.split(' +', results_str)

        if all([r == "-" for r in results]):
            result_by_remote[remote] = PINGABLE_NO
        else:
            result_by_remote[remote] = PINGABLE_YES

    for remote in [r for r in remotes if r not in result_by_remote.keys()]:
        result_by_remote[remote] = PINGABLE_UNKNOWN
        #logger.warning(f"no result in fping for {remote}")

    logger.info(f"Ping results:\n{yaml.dump(result_by_remote)}")
    return result_by_remote

def set_metric_from_results(destinations, test_name, result_by_remote):
    node_pingable = collections.defaultdict(dict) # map from a remote to a map of destination to results

    base_labels = {
        "pingmesh_test": test_name,
        "pingmesh_source_name": SELF_NODE_NAME
    }
    for dest_remote, result in result_by_remote.items():
        #for _unused_dest_name,(dest_remote,result) in node_pingable_by_dest.items():
        destination = destinations.get_destination_by_remote(dest_remote)

        if not destination:
            # skip this destination, it must have been removed from 'destinations'
            # in parallel with ping result processing
            continue

        # set pingable_metric for each destination
        labels = copy.deepcopy(base_labels)
        labels.update(destination.get_metric_labels())
        metric = pingable_metric.labels(**labels)
        destination.add_metric(pingable_metric, metric)
        metric.set(result)

        # populate node_pingable if relevant
        if destination.name_is_a_nodename:
            node_name = destination.name
            # a given node may correspond to multiple destinations
            # this is the case for pod-to-pod tests, because during daemonset
            # rolling updates, there are windows of time with two pods (hence 2 remotes, 2 destinations)
            # on a given node
            #
            # in that case, we'll consider that the node is pingable
            # as soon as there is one destination that is pingable
            #
            # hence we don't set the metric if there already is a positive
            # result for the same destination
            if node_pingable[destination.dest_type].get(node_name) == PINGABLE_YES:
                continue

            node_pingable[destination.dest_type][node_name]  = result

    # summarize pingability to the whole cluster in aggregated metrics
    for dest_type,dests_pingable in node_pingable.items():
        labels = copy.deepcopy(base_labels)
        labels["pingmesh_dest_type"] = dest_type

        # we compute ratio and all-pingable with in mind the fact
        # that a self-ping should always work, so "all" means "all others"
        # and not being able to ping any other nodes means that the connectivity
        # ratio is 0
        pingable_count = sum([dests_pingable.get(node_name) == PINGABLE_YES for node_name in all_cluster_nodes if node_name != SELF_NODE_NAME])
        other_nodes_count = len(all_cluster_nodes) - 1

        if other_nodes_count > 0:
            pingable_ratio = (1.0*pingable_count)/other_nodes_count
            all_pingable = (pingable_count == other_nodes_count)
            all_pingable_metric.labels(**labels).set(PINGABLE_YES if all_pingable else PINGABLE_NO)
            connectivity_ratio_metric.labels(**labels).set(pingable_ratio)
        else:
            all_pingable_metric.labels(**labels).set(PINGABLE_UNKNOWN)
            connectivity_ratio_metric.labels(**labels).set(-1)

############################### Prometheus metrics ###############################################

PINGABLE_YES = 1
PINGABLE_NO = 0
PINGABLE_UNKNOWN = -1
pingable_metric = prometheus_client.Gauge(
    "pingmesh_pingable", "destination replies to pings (-1 unknown, 0 no, 1 yes)",
    labelnames=[
        "pingmesh_test",
        "pingmesh_dest_type",
        "pingmesh_source_name",
        "pingmesh_destination_name",
        "pingmesh_destination_remote"
    ]
)

all_pingable_metric = prometheus_client.Gauge(
    "pingmesh_all_pingable", "whether or not all destinations on all cluster nodes replied to pings (-1 unknown, 0 no, 1 yes)",
    labelnames=[
        "pingmesh_test",
        "pingmesh_dest_type",
        "pingmesh_source_name",
    ]
)

connectivity_ratio_metric = prometheus_client.Gauge(
    "pingmesh_connectivity_ratio", "ratio of destinations on all cluster nodes that reply to pings (-1 if zero nodes are known)",
    labelnames=[
        "pingmesh_test",
        "pingmesh_dest_type",
        "pingmesh_source_name",
    ]
)


############################### Main  ############################################################

def main():
    print("Starting pingmesh")

    logging.getLogger("kubernetes.client").setLevel(logging.WARNING)

    print(f"config:\n\n{yaml.dump(config)}")

    # Start the Kopf framework and let it initialise.
    logger.info("Starting Kopf")
    (kopf_thread, kopf_stop_flag) = start_kopf_thread()
    logger.info("Kopf is started")

    logger.info("starting Prometheus exporter HTTP server")
    prometheus_client.start_http_server(8000)
    logger.info("started Prometheus exporter HTTP server")

    register_static_destinations(config, destinations)

    # main loop
    time.sleep(10)
    while True:
        try:
            # because Kopf will not regenerate events for the deletion that may happen
            # during a reconnection, we need to periodically check if the nodes and pods
            # we know still exist
            check_pods()
            check_nodes()

            # trigger tests

            for test_name,test_config in config["tests"].items():
                if test_config["type"] == "fping":
                    result_by_remote = run_fping(test_name, test_config, destinations)
                    set_metric_from_results(destinations, test_name, result_by_remote)

            time.sleep(config.get("testPeriodSeconds",10))
        except KeyboardInterrupt:
            break
        except kubernetes.client.exceptions.ApiException:
            logger.exception("Kubernetes API error, will retry")

    # Gracefully terminate Kopf framework
    logger.info(f"Exiting Kopf")
    kopf_stop_flag.set()
    kopf_thread.join()


if __name__ == '__main__':
    main()
