#!/bin/bash

# Grab some info in case of failure, essentially usefull to troubleshoot CI, fell free to add your own commands while troubleshooting

# list of kinds to dump
#
# for some resources, we add the apiGroup because there are resources
# with same names in CAPI and Rancher provisioning.cattle.io/management.cattle.io API groups
# we want the CAPI Cluster ones (e.g. Clusters.*cluster.x-k8s.io) rather than
# the Rancher one (e.g Clusters.provisioning.cattle.io)
additional_resources="
  Namespaces
  Roles
  RoleBindings
  ClusterRoles
  ClusterRoleBindings
  ServiceAccounts
  CustomResourceDefinitions
  MutatingWebhookConfigurations
  ValidatingWebhookConfigurations
  HelmReleases
  HelmRepositories
  HelmCharts.*source.toolkit.fluxcd.io
  GitRepositories
  OCIRepositories
  Kustomizations
  StatefulSets
  Jobs
  CronJobs
  PersistentVolumes
  PersistentVolumeClaims
  ConfigMaps
  Nodes
  Services
  Endpoints
  EndpointSlices
  Ingresses
  IngressClasses
  StorageClasses
  PodDisruptionBudgets
  HeatStacks
  ClusterSecretStores
  SecretStores
  ClusterExternalSecrets
  ExternalSecrets
  Keycloaks
  KeycloakClients
  Clusters.*cluster.x-k8s.io
  MachineDeployments
  Machines
  KubeadmControlPlanes
  KubeadmConfigTemplates
  KubeadmConfigs
  RKE2ControlPlanes
  RKE2ConfigTemplates
  RKE2Configs
  DockerClusters
  DockerMachineTemplates
  DockerMachines
  VSphereClusters.*infrastructure.cluster.x-k8s.io
  VSphereMachineTemplates.*infrastructure.cluster.x-k8s.io
  VSphereMachines.*infrastructure.cluster.x-k8s.io
  OpenStackClusters
  OpenStackMachineTemplates
  OpenStackMachines
  OpenStackServers
  Metal3Clusters
  Metal3MachineTemplates
  Metal3Machines
  Metal3DataTemplates
  Metal3Datas
  Metal3DataClaims
  TigeraStatuses.*operator.tigera.io
  Installations.*operator.tigera.io
  IPPools.*crd.projectcalico.org
  FelixConfigurations.*crd.projectcalico.org
  IPAddresses.*ipam.metal3.io
  IPClaims.*ipam.metal3.io
  IPPools.*ipam.metal3.io
  BaremetalHosts
  IPAddressPools.*metallb.io
  L2Advertisements.*metallb.io
  ServiceL2Statuses.*metallb.io
  Nodes.*longhorn.io
  Replicas.*longhorn.io
  Volumes.*longhorn.io
  VolumeAttachments.*longhorn.io
  Settings.*longhorn.io
  Engines.*longhorn.io
  InstanceManagers.*longhorn.io
  CleanupPolicies.*kyverno.io
  ClusterCleanupPolicies.*kyverno.io
  ClusterPolicies.*kyverno.io
  Policies.*kyverno.io
  PolicyExceptions.*kyverno.io
  UpdateRequests.*kyverno.io
  PolicyReports.*wgpolicyk8s.io
  ClusterPolicyReports.*wgpolicyk8s.io
  Tenants.*minio.min.io
  HelmCharts.*helm.cattle.io
  SriovIBNetworks
  SriovNetworkNodePolicies
  SriovNetworkNodeStates
  SriovNetworkPoolConfigs
  SriovNetworks
  SriovOperatorConfigs
  VirtualMachines.*kubevirt.io
  VirtualMachineInstances.*kubevirt.io
"

function dump_additional_resources() {
    local cluster_dir=$1
    shift
    kubectl api-resources > $cluster_dir/api-resources.txt
    # shellcheck disable=SC2068
    for cr in $@; do
      {
      if ! [[  ${cr} =~ ^[A-Z][A-Za-z0-9]*s($|\.\*.*) ]]; then
          echo "dump_additional_resources issue: '${cr}' does not match the expected pattern, you should provide the capitalized (plural) NAME of the resource, not the KIND"
          echo 'For example, provided following results:'
          echo '$ k api-resources | grep "NAME\|clusterpolicies"'
          echo 'NAME                                         SHORTNAMES              APIVERSION                                   NAMESPACED   KIND'
          echo 'clusterpolicies                              cpol                    kyverno.io/v1                                false        ClusterPolicy'
          echo
          echo 'You should use "ClusterPolicies.*kyverno.io" or "ClusterPolicies", not "ClusterPolicy"'
          exit 1
      fi
      echo "Dumping resources $cr in the whole cluster"
      if kubectl api-resources | grep -qi $cr ; then
        kind=${cr/\*/}  # transform the .* used for matching kubectl api-resource, into a plain '.'
                        # (see Clusters.*cluster.x-k8s.io above)
        base_filename=$cluster_dir/${kind}

        if [[ $kind == HelmReleases || $kind == Kustomizations ]]; then
            flux get ${kind,,} -A > $base_filename.summary.txt
        else
            kubectl get $kind -A -o wide > $base_filename.summary.txt
        fi

        kubectl get $kind -A -o yaml --show-managed-fields > $base_filename.yaml
      fi
      } &
    done
    wait
}


function format_and_sort_events() {
  # this sorts events by lastTimestamp (when defined)
  include_ns=''
  if [[ $1 == "include-ns" ]]; then
    include_ns='.involvedObject.namespace // "-",'
  fi
  yq "[.items[] |
       [.firstTimestamp // .eventTime,
        .lastTimestamp // .series.lastObservedTime // .firstTimestamp // .eventTime,
	      .reportingComponent + \"-\" + .reportingInstance,
        .involvedObject.kind,
        $include_ns
        .involvedObject.name,
        .count // .series.count // 1,
        .reason,
        .message // \"\" | sub(\"\n\",\"\n        \")]
       ]
      | sort_by(.1)
      | @tsv"
}

function crust_gather_collect() {
  local cluster=$1

  echo "Checking if $cluster cluster is reachable"
  if ! timeout 10s kubectl get nodes > /dev/null 2>&1 ;then
    echo "$cluster cluster is unreachable - aborting crust_gather"
    return 0
  fi

  echo "Crust-gathering $cluster cluster in crust-gather/$cluster"

  mkdir -p "crust-gather/$cluster"
  crustgather collect --exclude-group="catalog.cattle.io" --exclude-kind=Secret -f crust-gather/$cluster &> "crust-gather/$cluster/crustgather.log"

  return 0
}


function remote_command {
    if [[ $IN_CI -eq 0 ]]; then
      echo "'remote_command' is available only from CI environments" >&2
      return 1
    fi

    local node=$1
    shift

    echo "running '$*' on $node ... " >&2

    # we assume that the 'sandbox-privileged-namespace' unit is enabled
    timeout 30s \
      kubectl -n sandbox debug node/$node \
      --request-timeout=5s \
      --profile=sysadmin \
      --image registry.gitlab.com/sylva-projects/sylva-elements/container-images/kube-job:v1.0.17 \
      -i -q -- \
      chroot /host \
      "$@"
}

function fetch_longhorn_support_bundle {
  local dump_dir=$1

  echo "==== Longhorn support bundle ========"

  if [[ -z $CI_JOB_ID ]]; then
    echo "(not in CI, not fetching Longhorn support bundle)"
    return
  fi

  echo "-- building an Ingress to access longhorn-backend ..."

  external_ip=$(KUBECONFIG= kubectl get services -n default kubernetes-external -o yaml | yq '.spec.externalIPs[0]')
  if [[ -z $external_ip ]]; then
    echo "!!!! failed to get external_ip"
    return
  fi

  longhorn_backend_hostname="longhorn-backend.$external_ip.nip.io"

  kubectl apply -f - <<EOB
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: longhorn-backend
  namespace: longhorn-system
spec:
  rules:
  - host: $longhorn_backend_hostname
    http:
      paths:
      - backend:
          service:
            name: longhorn-backend
            port:
              number: 9500
        path: /
        pathType: Prefix
EOB

  # code borrowed from https://longhorn.io/kb/troubleshooting-create-support-bundle-with-curl/
  ISSUE_URL=https://gitlab.com/sylva-projects/sylva-core/-/jobs/$CI_JOB_ID
  ISSUE_DESCRIPTION="Support bundle for Sylva CI Gitlab Job $CI_JOB_ID"
  BACKEND_URL_BASE="http://$longhorn_backend_hostname"

  echo "-- requesting a Longhorn support bundle via Longhorn API ($BACKEND_URL_BASE)..."

  # Request to create the support bundle
  echo "Requesting support bundle..."
  REQUEST_SUPPORT_BUNDLE=$(curl --retry 5 --retry-all-errors -sSX POST -H 'Content-Type: application/json' -d '{ "issueURL": "'"${ISSUE_URL}"'", "description": "'"${ISSUE_DESCRIPTION}"'" }' ${BACKEND_URL_BASE}/v1/supportbundles)

  ID=$( yq -p json -r '.id' <<< ${REQUEST_SUPPORT_BUNDLE} )
  if [[ $ID == "null" ]]; then
    echo "!!!! failed API call to create Longhorn support bundle (ID: $ID)"
    return
  fi

  SUPPORT_BUNDLE_NAME=$( yq -p json -r '.name' <<< ${REQUEST_SUPPORT_BUNDLE} )
  echo "Creating support bundle ${SUPPORT_BUNDLE_NAME} on Node ${ID}"

  cnt=0
  while [[ $(curl -sSX GET ${BACKEND_URL_BASE}/v1/supportbundles/${ID}/${SUPPORT_BUNDLE_NAME} | yq -p json -r '.state' ) != "ReadyForDownload" ]]; do
    echo "Progress: $(curl -sSX GET ${BACKEND_URL_BASE}/v1/supportbundles/${ID}/${SUPPORT_BUNDLE_NAME} | yq -p json -r '.progressPercentage' )%"
    sleep 5s

    if [[ $cnt -ge 20 ]]; then
      echo "stopping, waited for too long for support bundle to be ready to download"
      return
    fi
    cnt=$((cnt+1))
  done

  echo "downloading support bundle to $dump_dir/longhorn-support-bundle.zip"
  curl -X GET ${BACKEND_URL_BASE}/v1/supportbundles/${ID}/${SUPPORT_BUNDLE_NAME}/download --output $dump_dir/longhorn-support-bundle.zip
}

function _openstack() {
  local destination_file="$1"
  local kubectl_opts="$2"
  local openstack_args="$3"
  echo "running 'openstack $3' > $destination_file ..."

  tmp_clouds_yaml_d=$(mktemp -d -p $(pwd))
  trap "rm -rf $tmp_clouds_yaml_d" EXIT INT

  kubectl $kubectl_opts get secret cluster-cloud-config -o yaml | yq '.data."clouds.yaml"' | base64 -d > $tmp_clouds_yaml_d/clouds.yaml

  chmod og+rX -R $tmp_clouds_yaml_d

  docker run --rm \
    -v $tmp_clouds_yaml_d:/etc/openstack \
    --entrypoint sh \
    registry.gitlab.com/sylva-projects/sylva-elements/container-images/openstack-client:v0.0.19 \
    -c "openstack --os-cloud capo_cloud $openstack_args" > "$destination_file"
}


function cluster_info_dump() {
  local cluster=$1
  local dump_dir=$cluster-cluster-dump

  if [[ $cluster == "workload" ]]; then
    capi_cluster_namespace=$2
    capi_cluster_name=$3
  else  # management cluster:
    capi_cluster_namespace=sylva-system
    capi_cluster_name=${MANAGEMENT_CLUSTER_NAME:-management-cluster}
  fi

  mkdir $dump_dir

  echo "Dumping data for $cluster cluster in $dump_dir"

  # dump CAPI cluster state
  echo "Dumping clusterctl describe..."
  KUBECONFIG=$MGMT_KUBECONFIG clusterctl describe cluster \
    -n $capi_cluster_namespace $capi_cluster_name \
    --grouping=false --show-conditions all --echo \
    > $dump_dir/clusterctl-describe.txt

  if [[ -n ${CI_JOB_NAME} ]]; then
    openstack_machines=$(kubectl get OpenStackMachines -A -o go-template='{{range .items}}{{.metadata.namespace}}/{{.metadata.name}} {{ end }}' 2>/dev/null)
    if [[ -n $openstack_machines ]]; then
      vm_console_logs_dir=$dump_dir/openstack-vms-console-logs
      echo "Gathering info on OpenStack machines into $vm_console_logs_dir ..."
      for openstack_machine in $openstack_machines; do
          local osm_ns=${openstack_machine%/*}
          local vm_name=${openstack_machine#*/}
          mkdir -p $vm_console_logs_dir/$osm_ns

          if [[ -n $MGMT_KUBECONFIG ]]; then
            kubectl_opts="--kubeconfig $MGMT_KUBECONFIG "
          fi
          kubectl_opts="${kubectl_opts:-} -n $capi_cluster_namespace"

          echo "   Dumping 'openstack server show' for $osm_ns/$vm_name ..."
          _openstack $vm_console_logs_dir/$osm_ns/$vm_name.show.txt "$kubectl_opts" "server show $vm_name -f yaml | yq '.\"OS-EXT-SRV-ATTR:user_data\" = \"... omitted ...\"'"

          echo "   Dumping 'openstack console logs' for $osm_ns/$vm_name ..."
          _openstack $vm_console_logs_dir/$osm_ns/$vm_name.console-log.txt "$kubectl_opts" "console log show $vm_name"
      done
    fi
  fi

  echo "Checking if $cluster cluster is reachable"
  if ! timeout 10s kubectl get nodes > /dev/null 2>&1 ;then
    echo "$cluster cluster is unreachable - aborting dump"
    return 0
  fi

  KUBECONFIG=$MGMT_KUBECONFIG helm get manifest -n $capi_cluster_namespace sylva-units | yq 'select(.kind!="Secret")' > $dump_dir/sylva-units-helm-release-manifest.yaml

  kubectl cluster-info dump -A -o yaml --show-managed-fields --output-directory=$dump_dir

  # produce a readable ordered log of events for each namespace
  for events_yaml in $(find $dump_dir -name events.yaml); do
    format_and_sort_events < $events_yaml > ${events_yaml//.yaml}.log
  done

  # same in a single file
  kubectl get events -A -o yaml | format_and_sort_events include-ns > $dump_dir/events.log

  dump_additional_resources $dump_dir $additional_resources

  # dump pods
  kubectl get pods -o wide -A > $dump_dir/pods.summary.txt

  # dump CAPI infra secrets
  kubectl get secret -A --field-selector=type=infrastructure.cluster.x-k8s.io/secret                               > $dump_dir/Secrets-capi-infra.summary.txt
  kubectl get secret -A --field-selector=type=infrastructure.cluster.x-k8s.io/secret -o yaml --show-managed-fields > $dump_dir/Secrets-capi-infra.yaml
  # dump CAPI secrets
  kubectl get secret -A --field-selector=type=cluster.x-k8s.io/secret                               > $dump_dir/Secrets-capi.summary.txt
  kubectl get secret -A --field-selector=type=cluster.x-k8s.io/secret -o yaml --show-managed-fields > $dump_dir/Secrets-capi.yaml

  # dump BMH.spec.preprovisioningNetworkDataName secrets, used in a DHCP-less CAPM3 deployment, if present
  if kubectl get secret -A -o custom-columns=NAME:.metadata.name | grep "preprovisioning-netdata$" > /dev/null 2>&1 ;then
    kubectl get secret -A | grep -E "NAMESPACE|preprovisioning-netdata" > $dump_dir/Secrets-preprovisioning-netdata.summary.txt
    kubectl get secret -A -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name \
      | grep "preprovisioning-netdata$" \
      | while read namespace name; do
          echo "---"
          kubectl get secret $name -n $namespace -o yaml --show-managed-fields
        done > $dump_dir/Secrets-preprovisioning-netdata.yaml
  fi

  # list secrets
  kubectl get secret -A > $dump_dir/Secrets.summary.txt
  kubectl get secret -A -o yaml --show-managed-fields | yq '.items[].data="secrets data is purposefully not dumped" | .items[].metadata.annotations="secrets data is purposefully not dumped"' > $dump_dir/Secrets-censored.yaml

  # dump RKE2 node-password secrets
  kubectl -n kube-system get secrets -o yaml | yq '.items=[.items[] | select(.metadata.name | contains(".node-password.rke2"))]' > $dump_dir/Secrets-rke2-node-passwords.yaml

  # dump per-node system information
  echo "Dumping per-node system information..."
  for node in $(kubectl get nodes -o custom-columns='CLUSTER:.metadata.name' --no-headers); do
    {
      node_sysinfo_dumpdir=$dump_dir/system-info/$node
      mkdir -p $node_sysinfo_dumpdir

      echo "-- node $node"

      remote_command $node ss -apnm > $node_sysinfo_dumpdir/ss-apnm.log

      remote_command $node iptables -t nat -nvL > $node_sysinfo_dumpdir/iptables-nat-1-before-clear-counters.log
      # zeroing iptables counters (we'll retrieve counters below after waiting a bit)
      remote_command $node iptables -t nat -Z
      sleep 10
      remote_command $node iptables -t nat -nvL > $node_sysinfo_dumpdir/iptables-nat-2-after-clear-counters.log
    } &
  done

  wait

  if [[ $(kubectl get ns longhorn-system -o name || true) == "namespace/longhorn-system" ]]; then
    fetch_longhorn_support_bundle $dump_dir
  fi

  echo -e "\nDisplay cluster resources usage per node"
  # From https://github.com/kubernetes/kubernetes/issues/17512
  kubectl get nodes --no-headers | awk '{print $1}' | xargs -I {} sh -c 'echo {} ; kubectl describe node {} | grep Allocated -A 5 | grep -ve Event -ve Allocated -ve percent -ve -- ; echo '
}

echo "Start debug-on-exit at: $(date -Iseconds)"

echo -e "\nDocker containers"
docker ps
echo -e "\nDocker containers resources usage"
docker stats --no-stream --all

echo -e "\nSystem info"
free -h
df -h || true

# Unset KUBECONFIG to make sure that we are targetting kind cluster
unset KUBECONFIG

if [[ $(kind get clusters) =~ $KIND_CLUSTER_NAME ]]; then
  crust_gather_collect bootstrap &
  cluster_info_dump bootstrap
  echo -e "\nDump bootstrap node logs"
  docker ps -q -f name=control-plane* | xargs -I % -r docker exec % journalctl -e > bootstrap-cluster-dump/bootstrap_node.log

  wait
fi

# Try to guess management-cluster-kubeconfig path:
# - Use first argument if provided
# - Use BASE_DIR environment value if it is set (it is usually done by common.sh in CI)
# - Use relative path to current script location as BASE_DIR as a last option

BASE_DIR=${BASE_DIR:-$(realpath $(dirname $0)/../../)}
MGMT_KUBECONFIG=${1:-${BASE_DIR}/management-cluster-kubeconfig}

if [[ -f $MGMT_KUBECONFIG ]]; then
    export KUBECONFIG=${MGMT_KUBECONFIG}

    crust_gather_collect management &

    echo -e "\nGet nodes in management cluster"
    kubectl --request-timeout=3s get nodes

    cluster_info_dump management

    workload_cluster_name=$(kubectl --request-timeout=3s get cluster.cluster -A -o jsonpath='{ $.items[?(@.metadata.namespace != "sylva-system")].metadata.name }')
    if [[ -z "$workload_cluster_name" ]]; then
        echo -e "There's no workload cluster for this deployment. All done"
    else
        echo -e "We'll check next workload cluster $workload_cluster_name"
        workload_cluster_namespace=$(kubectl get cluster.cluster --all-namespaces -o=custom-columns=NAME:.metadata.name,NAMESPACE:.metadata.namespace | grep "$workload_cluster_name" | awk -F ' ' '{print $2}')
        kubectl -n $workload_cluster_namespace get secret $workload_cluster_name-kubeconfig -o jsonpath='{.data.value}' | base64 -d > $BASE_DIR/workload-cluster-kubeconfig

        if timeout 10s kubectl --kubeconfig=$BASE_DIR/workload-cluster-kubeconfig get nodes > /dev/null 2>&1; then
          export KUBECONFIG=$BASE_DIR/workload-cluster-kubeconfig
        else
          echo "failed to access cluster k8s API directly (this is expected with libvirt-metal) will try via Rancher..."
          # in case of baremetal emulation workload cluster is only accessible from Rancher
          # and rancher API certificates does not match expected (so kubectl must be used with insecure-skip-tls-verify)
          $BASE_DIR/tools/shell-lib/get-wc-kubeconfig-from-rancher.sh $workload_cluster_name $BASE_DIR/workload-cluster-kubeconfig-rancher
          yq -i e '.clusters[].cluster.insecure-skip-tls-verify = true' $BASE_DIR/workload-cluster-kubeconfig-rancher
          yq -i e 'del(.clusters[].cluster.certificate-authority-data)' $BASE_DIR/workload-cluster-kubeconfig-rancher
          export KUBECONFIG=$BASE_DIR/workload-cluster-kubeconfig-rancher
        fi

        crust_gather_collect workload &

        cluster_info_dump workload $workload_cluster_namespace $workload_cluster_name
    fi

  wait
fi

if [[ -d "crust-gather" ]]
then
  tar -czf crust-gather.tar.gz crust-gather

  [[ $IN_CI ]] && echo -e "Exec following command to serve crust-gather:\n\t./tools/serve-crustgather-artifact.sh -j $CI_JOB_ID"
fi
