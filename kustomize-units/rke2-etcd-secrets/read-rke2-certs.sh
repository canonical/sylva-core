#!/bin/bash

set -eu -o pipefail

pod_image=${pod_image:-alpine:3.16}

cluster_name=$1
if [[ -z "$cluster_name" ]]; then
    echo "first parameters needs to be the target cluster name"
    exit 1
fi

function secret_exists {
    secret_name=$1
    if [[ "$(kubectl get secret $secret_name -o name 2>/dev/null)" == "secret/$secret_name" ]]; then
        return 0
    else
        return 1
    fi
}

# check if something needs to be done
if (secret_exists $cluster_name-etcd) && (secret_exists $cluster_name-etcd); then
    echo "$cluster_name-etcd and $cluster_name-peer-etcd Secrets already exist, nothing to do"
    exit 0
fi

tmpdir=$(mktemp -d)
cd $tmpdir

# prepare exit trap
function exit_trap {
    echo "-- Exiting ..."
    echo "-- (target cluster) Delete privileged 'rke2-etcd-secrets' namespace"
    kubectl --kubeconfig workload-cluster-kubeconfig delete namespace rke2-etcd-secrets
    echo "-- Delete tmpdir ..."
    rm -rf $tmpdir
}
trap exit_trap EXIT

# prepare access to target cluster
echo "-- (management cluster) Retrieve target cluster kubeconfig"
kubectl get secret $cluster_name-kubeconfig -o jsonpath='{.data.value}' | base64 -d > workload-cluster-kubeconfig

export KUBECONFIG=workload-cluster-kubeconfig

echo "-- (target cluster) Create privileged 'rke2-etcd-secrets' namespace"

# create privileged namespace
kubectl apply --field-manager=rke2-etcd-secrets-kubectl -f - <<EOM
apiVersion: v1
kind: Namespace
metadata:
  name: rke2-etcd-secrets
  labels:
    pod-security.kubernetes.io/enforce: "privileged"
    pod-security.kubernetes.io/warn: "privileged"
    pod-security.kubernetes.io/audit: "privileged"
EOM

# find a control plane node
echo "-- (target cluster) Identify a control plane node"
workload_cluster_cp_node=$(kubectl get nodes -l node-role.kubernetes.io/control-plane=true -o json | jq -r '[.items[] | select(.status.conditions[] | select(.type == "Ready" and .status == "True"))] | first | .metadata.name')

if [[ -z $workload_cluster_cp_node ]]; then
   echo "no control plane node was found on workload cluster - exiting !"
   kubectl get nodes
   exit 1
fi

# get RKE2 certs with "kubectl debug node"

echo "... will fetch certs from $workload_cluster_cp_node"

echo "-- (target cluster) Download RKE2 etcd secrets from node"
kubectl debug node/$workload_cluster_cp_node \
      -n rke2-etcd-secrets \
      --image $pod_image \
      -q --attach=true -- \
      sh -c 'cd /host/var/lib/rancher/rke2/server/tls/etcd && tar c *-ca.*' \
  | tar xv

echo "-- (management cluster) Create $cluster_name-etcd and $cluster_name-peer-etcd Secrets"

# go back to ServiceAccount kubeConfig (management cluster)
unset KUBECONFIG

# create <cluster-name>-etcd and <cluster-name>-peer-etcd Secrets
function create_secret {
    file_prefix=$1
    secret_name=$2

    if secret_exists $secret_name; then
        echo "($secret_name Secret already exists)"
    else
        echo "... create $secret_name Secret"
        kubectl create secret generic $secret_name \
          --field-manager=rke2-etcd-secrets-kubectl \
          --type=cluster.x-k8s.io/secret \
          --from-file=tls.crt=$file_prefix-ca.crt \
          --from-file=tls.key=$file_prefix-ca.key
    fi
    echo "... labelling $secret_name Secret for CAPI"
    kubectl label --field-manager=rke2-etcd-secrets-kubectl --overwrite \
      secret $secret_name cluster.x-k8s.io/cluster-name=$cluster_name
}

create_secret server $cluster_name-etcd
create_secret peer $cluster_name-peer-etcd
