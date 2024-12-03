#!/bin/bash
pod_image=${pod_image:-alpine:3.16}  # image to use for remote commands (kubectl debug node)

set -eu -o pipefail

tmpdir=$(mktemp -d)

# prepare exit trap
function exit_trap {
    echo -e "\n-- Exiting, delete tmpdir ..."
    rm -rf $tmpdir
}
trap exit_trap EXIT

function secret_exists {
    local ns=$1
    local secret_name=$2
    if [[ "$(kubectl -n $ns get secret $secret_name -o name 2>/dev/null)" == "secret/$secret_name" ]]; then
        return 0
    else
        return 1
    fi
}

function create_secret {
    local ns=$1
    local secret_name=$2
    local file_prefix=$3

    if secret_exists $ns $secret_name; then
        echo "---   ($secret_name Secret already exists)"
    else
        echo "--- ... create $secret_name Secret"
        kubectl -n $ns create secret generic $secret_name \
            --field-manager=rke2-etcd-secrets-kubectl \
            --type=cluster.x-k8s.io/secret \
            --from-file=tls.crt=$file_prefix-ca.crt \
            --from-file=tls.key=$file_prefix-ca.key
    fi
    echo "--- ... labelling $secret_name Secret for CAPI"
    kubectl -n $ns label secret $secret_name \
        --field-manager=rke2-etcd-secrets-kubectl --overwrite \
        cluster.x-k8s.io/cluster-name=$cluster_name
}

function migrate_cluster {
    if [[ $# -ne 3 ]]; then
        echo " !! migrate_cluster requires 3 parameters, but only 2 were given: $*"
        return 1
    fi

    local ns=$1
    local cluster_name=$2
    local rke2cp=$3

    # check if something needs to be done
    if (secret_exists $ns $cluster_name-etcd) && (secret_exists $ns $cluster_name-peer-etcd); then
        echo "--- <cluster_name>-etcd and <cluster_name>-peer-etcd Secrets already exist, nothing to do"
        # label (if not already labelled)
        kubectl label -n $ns RKE2ControlPlane $rke2cp \
            sylva/rke2-etcd-secrets-migrate=not-needed || true
        return 0
    fi

    # label the RKE2ControlPlane object (informational)
    kubectl -n $ns label --overwrite RKE2ControlPlane $rke2cp \
        sylva/rke2-etcd-secrets-migrate=attempted

    cluster_tmpdir=$tmpdir/$ns-$cluster_name
    mkdir $cluster_tmpdir
    cd $cluster_tmpdir

    # prepare access to target cluster
    echo "--- (management cluster) Retrieve target cluster kubeconfig"
    kubectl -n $ns get secret $cluster_name-kubeconfig -o jsonpath='{.data.value}' | base64 -d > $cluster_name-kubeconfig

    ######################### kubectl actions below happen *in the target cluster* #############################
    export KUBECONFIG=$cluster_name-kubeconfig

    echo "--- (target cluster) Create privileged 'rke2-etcd-secrets' namespace"

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

    function cleanup_target_cluster_priv_ns {
        echo "--- (target cluster) Delete privileged 'rke2-etcd-secrets' namespace"
        kubectl --kubeconfig $cluster_name-kubeconfig delete namespace rke2-etcd-secrets
    }

    set +e

    # find a control plane node
    echo "--- (target cluster) Identify a control plane node"
    workload_cluster_cp_node=$(kubectl get nodes -l node-role.kubernetes.io/control-plane=true -o json | jq -r '[.items[] | select(.status.conditions[] | select(.type == "Ready" and .status == "True"))] | first | .metadata.name')

    if [[ -z $workload_cluster_cp_node ]]; then
        echo "--- *** no control plane node was found on workload cluster !"
        kubectl get nodes
        cleanup_target_cluster_priv_ns
        return 1
    fi

    # get RKE2 certs with "kubectl debug node"

    echo "--- ... will fetch certs from $workload_cluster_cp_node"

    echo "--- (target cluster) Download RKE2 etcd secrets from node"
    kubectl debug node/$workload_cluster_cp_node \
        -n rke2-etcd-secrets \
        --image $pod_image \
        -q --attach=true -- \
        sh -c 'cd /host/var/lib/rancher/rke2/server/tls/etcd && tar c *-ca.*' \
      | tar xv

    if [[ $? != 0 ]]; then
        echo "--- *** issue while fetching certs - exiting !"
        cleanup_target_cluster_priv_ns
        return 1
    fi

    set -e

    cleanup_target_cluster_priv_ns

    ######################### go back to ServiceAccount kubeConfig (management cluster) #############################

    unset KUBECONFIG

    echo "--- (management cluster) Create $cluster_name-etcd and $cluster_name-peer-etcd Secrets"

    # create <cluster-name>-etcd and <cluster-name>-peer-etcd Secrets

    create_secret $ns $cluster_name-etcd server
    create_secret $ns $cluster_name-peer-etcd peer

    # label the RKE2ControlPlane object (informational)
    kubectl -n $ns label --overwrite RKE2ControlPlane $rke2cp \
        sylva/rke2-etcd-secrets-migrate=done
}



error=0

function _get_ids {
    jq -r '.items[] | [.metadata.namespace, .metadata.labels."cluster.x-k8s.io/cluster-name", .metadata.name] | join(" ")'
}

# loop on all RKE2ControlPlane objects and process the corresponding clusters:
# - first start with the ones we didn't try yet (to avoid the case where a cluster always triggers a failure, and then all other clusters would never be processed)
# - pursue with the ones that we want to retry (random order)
_clusters=$(kubectl get rke2controlplane -A -o json -l 'sylva/rke2-etcd-secrets-migrate notin(attempted)' | _get_ids; \
            kubectl get rke2controlplane -A -o json -l 'sylva/rke2-etcd-secrets-migrate=attempted' | _get_ids | shuf)
while read namespace cluster_name rke2cp; do
    echo -e "\n============ processing $namespace $cluster_name ===============\n"
    migrate_cluster $namespace $cluster_name $rke2cp
    if [[ $? -ne 0 ]]; then
        error=1
    fi
    echo
done <<<"$_clusters"

if [[ $error -eq 0 ]]; then
    # annotate the parent sylva-units HelmRelease object
    # (meant for future use, to determine that the migration of all clusters was done)
    kubectl -n sylva-system annotate --overwrite HelmRelease sylva-units \
        sylva/rke2-etcd-secrets-migrate=done
fi

exit $error
