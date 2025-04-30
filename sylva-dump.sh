#!/bin/bash

# This script can be used to dump sylva clusters state (bootstrap/management/workload)
# it generates an archive 'sylva-dump-YYYY-MM-DDThh-mm-ss.tar.gz' which may shared (in issue by example)

# It takes as first argument the name of workload cluster to dump (needed if there are several workload clusters managed by the current management cluster)

USER_PWD=$(pwd)
DUMPS_DIR="$USER_PWD/dumps"
CURRENT_DUMP_DIR="$USER_PWD/dumps/current-dump"

source $(dirname $(realpath $0))/tools/shell-lib/common.sh

ensure_sylva_toolbox

rm -rf "$CURRENT_DUMP_DIR"
mkdir -p "$CURRENT_DUMP_DIR"
cd "$CURRENT_DUMP_DIR"

if [[ -f management-cluster-kubeconfig ]]; then
  export KUBECONFIG=${KUBECONFIG:-management-cluster-kubeconfig}
  export MANAGEMENT_CLUSTER_NAME=$(kubectl get clusters.cluster.x-k8s.io -n sylva-system -oyaml | yq .items[0].metadata.name)
fi

export WORKLOAD_CLUSTER_NAME=${1:-}

echo_b "👀 Dumping sylva state"
${BASE_DIR}/tools/shell-lib/debug-on-exit.sh 2>&1 | tee sylva-dump.log

archive_name="$DUMPS_DIR/sylva-dump-$(date -u '+%Y%m%d-%H%M%S').tar.gz"
relative_archive_name=$(realpath -s --relative-to="$USER_PWD" "$archive_name")

echo_b "🎁 Creating archive $relative_archive_name"
ls
tar -czf "$archive_name" "."
echo "File $relative_archive_name is ready"
