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
  HelmReleases
  HelmRepositories
  HelmCharts
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
  Ingresses
  IngressClasses
  HeatStacks
  ClusterSecretStore
  SecretStore
  ClusterExternalSecret
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
  Metal3Clusters
  Metal3MachineTemplates
  Metal3Machines
  Metal3DataTemplates
  BaremetalHosts
  Nodes.*longhorn.io
  Replicas.*longhorn.io
  Volumes.*longhorn.io
  VolumeAttachments.*longhorn.io
  Settings.*longhorn.io
  Engines.*longhorn.io
  InstanceManagers.*longhorn.io
  CleanupPolicy.*kyverno.io
  ClusterCleanupPolicy.*kyverno.io
  ClusterPolicy.*kyverno.io
  Policy.*kyverno.io
  PolicyException.*kyverno.io
  UpdateRequest.*kyverno.io
  PolicyReport.*wgpolicyk8s.io
  ClusterPolicyReport.*wgpolicyk8s.io
"

function dump_additional_resources() {
    local cluster_dir=$1
    shift
    for cr in $@; do
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
    done
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

  # dump CAPI cluster state
  echo "Dumping clusterctl describe..."
  KUBECONFIG=$MGMT_KUBECONFIG clusterctl describe cluster \
    -n $capi_cluster_namespace $capi_cluster_name \
    --grouping=false --show-conditions all --echo \
    > $dump_dir/clusterctl-describe.txt

  echo "Checking if $cluster cluster is reachable"
  if ! timeout 10s kubectl get nodes > /dev/null 2>&1 ;then
    echo "$cluster cluster is unreachable - aborting dump"
    return 0
  fi
  echo "Dumping resources for $cluster cluster in $dump_dir"

  kubectl cluster-info dump -A -o yaml --show-managed-fields --output-directory=$dump_dir

  # produce a readable ordered log of events for each namespace
  for events_yaml in $(find $dump_dir -name events.yaml); do
    format_and_sort_events < $events_yaml > ${events_yaml//.yaml}.log
  done

  # same in a single file
  kubectl get events -A -o yaml | format_and_sort_events include-ns > $dump_dir/events.log

  dump_additional_resources $dump_dir $additional_resources

  # dump pods
  kubectl get pods -o wide -A | tee $dump_dir/pods.summary.txt

  # dump CAPI secrets
  kubectl get secret -A --field-selector=type=infrastructure.cluster.x-k8s.io/secret                               > $dump_dir/Secrets-capi.summary.txt
  kubectl get secret -A --field-selector=type=infrastructure.cluster.x-k8s.io/secret -o yaml --show-managed-fields > $dump_dir/Secrets-capi.yaml

  # list secrets
  kubectl get secret -A > $dump_dir/Secrets.summary.txt
  kubectl get secret -A -o yaml --show-managed-fields | yq '.items[].data="secrets data is purposefully not dumped" | .items[].metadata.annotations="secrets data is purposefully not dumped"' > $dump_dir/Secrets-censored.yaml

  # dump RKE2 node-password secrets
  kubectl -n kube-system get secrets -o yaml | yq '.items=[.items[] | select(.metadata.name | contains(".node-password.rke2"))]' > $dump_dir/Secrets-rke2-node-passwords.yaml

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
  cluster_info_dump bootstrap
  echo -e "\nDump bootstrap node logs"
  docker ps -q -f name=control-plane* | xargs -I % -r docker exec % journalctl -e > bootstrap-cluster-dump/bootstrap_node.log
fi

# Try to guess management-cluster-kubeconfig path:
# - Use first argument if provided
# - Use BASE_DIR environment value if it is set (it is usually done by common.sh in CI)
# - Use relative path to current script location as BASE_DIR as a last option

BASE_DIR=${BASE_DIR:-$(realpath $(dirname $0)/../../)}
MGMT_KUBECONFIG=${1:-${BASE_DIR}/management-cluster-kubeconfig}

if [[ -f $MGMT_KUBECONFIG ]]; then
    export KUBECONFIG=${MGMT_KUBECONFIG}

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

        cluster_info_dump workload $workload_cluster_namespace $workload_cluster_name
    fi
fi
