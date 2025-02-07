#!/bin/bash

## This script aims to get logs directly from cluster nodes for debug purposes
## It is designed to work for sylva CI deployments which are using 
## `run_http_server_for_log_collect.yaml` values file

set -eu
set -o pipefail

# activate sylva toolbox
. bin/env || true

unset http_proxy
unset https_proxy

TARGET_CLUSTER=$1
if [[  $TARGET_CLUSTER != "management"  ]] && [[ $TARGET_CLUSTER != "workload" ]]; then
  >&2 echo "[ERROR] First parameter should be 'management' or 'workload'"
  exit 1
fi

echo ""
echo "# Start collecting logs on nodes for $TARGET_CLUSTER cluster"

TARGET_LOG_DIR=./$TARGET_CLUSTER-cluster-dump/node_logs
mkdir -p $TARGET_LOG_DIR

# Check if any cluster name contains "bootstrap", otherwise default to "sylva"
if [[ $(kind get clusters -q) =~ bootstrap ]]; then
  KIND_CLUSTER_NAME=$(kind get clusters -q | grep bootstrap)
else
  KIND_CLUSTER_NAME="sylva"
fi

unset KUBECONFIG
# If bootstrap cluster is present we assume pivot is not done or this is a capm3-virt deployment
if [[ $(kind get clusters -q) =~ ${KIND_CLUSTER_NAME} ]]; then
  echo "bootstrap cluster detected"
  BOOTSTRAP_ALIVE="true"
  kubectl config view --raw > bootstrap-cluster-kubeconfig

  if [[ $TARGET_CLUSTER == "management" ]]; then
    MACHINE_COUNT_IN_BOOTSTRAP=$(kubectl get -n sylva-system machines.cluster.x-k8s.io -ojson | yq '.items | length')
    if [[ $MACHINE_COUNT_IN_BOOTSTRAP -gt 0 ]]; then
      echo "Machine ressources found in Bootstrap cluster, assuming pivot is not done"
    else
      echo "No machine ressources found in Bootstrap cluster, assuming pivot is done"
      export KUBECONFIG=management-cluster-kubeconfig
    fi
  else
    echo "Looking for a workload cluster, assuming management cluster is up"
    export KUBECONFIG=management-cluster-kubeconfig
  fi

else
  echo "No bootstrap cluster detected"
  export KUBECONFIG=management-cluster-kubeconfig
fi

# Creating service in bootstrap cluster pointing on given IP adddress
# It would be usefull to access nodes in capm3-virt deployment
if [[ ${BOOTSTRAP_ALIVE:-} == "true" ]]; then
  bootstrap_cluster_ip=$(docker container inspect ${KIND_CLUSTER_NAME}-control-plane | yq '.[0].NetworkSettings.Networks.kind.IPAddress')
  echo "
---
apiVersion: v1
kind: Service
metadata:
  name: machine-dump
  namespace: sylva-system
spec:
  ports:
    - name: dump
      protocol: TCP
      port: 25888
      targetPort: 25888
  externalIPs:
  - $bootstrap_cluster_ip
---
apiVersion: discovery.k8s.io/v1
kind: EndpointSlice
metadata:
  name: machine-dump
  namespace: sylva-system
  labels:
    kubernetes.io/service-name: machine-dump
addressType: IPv4
ports:
  - name: dump
    appProtocol: http
    protocol: TCP
    port: 25888
endpoints:
  - addresses:
    - 1.2.3.4 # fake address, will be patched when real machine IPs will be retrieved
  " | kubectl apply --kubeconfig=bootstrap-cluster-kubeconfig --force -f -
fi



# Retrieve machines namespace
if [[ $TARGET_CLUSTER == "management" ]]; then
  MACHINES_NS="sylva-system"
else
  MACHINES_NS=$(kubectl --request-timeout=3s get cluster.cluster -A -oyaml | yq '.items[] | select(.metadata.namespace != "sylva-system").metadata.namespace' | sort | uniq )
  if [[ -z "$MACHINES_NS" ]]; then
    echo -e "There's no workload cluster."
    exit 1
  fi
fi

download_port=25888

function get_download_ip {
    # Get IP address for each machine
    machine_kind=$(kubectl -n ${clusterns} get $machine_name -ojsonpath='{.spec.infrastructureRef.kind}')
    if [[ $machine_kind == "Metal3Machine" ]]; then
      metal3machine=$(kubectl -n ${clusterns} get $machine_name -ojsonpath='{.spec.infrastructureRef.name}')
      network_data_secret=$(kubectl get m3m/$metal3machine -n ${clusterns} -ojsonpath='{.status.networkData.name}')
      machine_ip=$(kubectl get secret/$network_data_secret -n ${clusterns} -ojsonpath='{.data.networkData}'| base64 -d | yq '.networks[0].ip_address')
      echo ">> machine_ip=$machine_ip"
    else
      machine_ip=$(kubectl -n ${clusterns} get $machine_name -ojsonpath='{.status.addresses[0].address}' )
    fi

    # download logs using machine IP and port 25888 where miniserve should be listening
    echo ">> Machine IP = $machine_ip"
    if [[ $machine_kind == "Metal3Machine" ]]; then
      let "download_port++"
      # In case of capm3-virt node's machine Ip are not directly accessible
      # we are creating service in bootstrap cluster to access it
      kubectl patch endpointslices machine-dump -n sylva-system --kubeconfig=bootstrap-cluster-kubeconfig \
        --patch '{"endpoints": [{"addresses": ["'$machine_ip'"]}]}'
      kubectl patch services machine-dump -n sylva-system --kubeconfig=bootstrap-cluster-kubeconfig \
        --type='json' --patch '[{"op": "replace", "path": "/spec/ports/0/port", "value": '$download_port' }]'
      download_ip="${bootstrap_cluster_ip}"
    else
      download_ip="${machine_ip}"
    fi
}

function download_files {
    echo ">> Download_URL = http://${download_ip}:${download_port}/"
    curl -sSL --fail-with-body --retry 10 --retry-max-time 10 --retry-connrefused http://${download_ip}:${download_port}/ --connect-timeout 2 -o /dev/null \
    && curl -sSL --fail-with-body "http://${download_ip}:${download_port}/?download=tar_gz" --connect-timeout 2 -o "${TARGET_LOG_DIR}/${machine_name##*/}.tar.gz" \
    && echo " >>> OK" \
    || echo " >>> Fail"
    echo ""
}

# Loop through namespaces and machines
for clusterns in ${MACHINES_NS}; do
  echo "> In namespace '$clusterns'"
  MACHINES=$(kubectl -n ${clusterns} get machines.cluster.x-k8s.io -o name)

  if [[ -z "$MACHINES" ]]; then
    echo " There are no machines."
    continue
  fi

    for machine_name in $MACHINES; do
    echo "> Cluster= $(kubectl -n ${clusterns} get clusters.cluster.x-k8s.io -o name) in namespace ${clusterns}"
    export machine_name=$machine_name
    echo "> Machine = $machine_name"
    set +e
    get_download_ip
    if [ -z "$machine_ip" ]; then
        echo "> No machine_ip found, skipping..."
        continue
    fi
    download_files
    set -e
  done
done

echo "## Done !"
echo ""
