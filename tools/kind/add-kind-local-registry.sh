#!/bin/bash

set -xe

KIND_CLUSTER_NAME=$1
DOCKER_LOCAL_REGISTRY=$2

REGISTRY_DIR="/etc/containerd/certs.d/${DOCKER_LOCAL_REGISTRY}"
docker exec "${KIND_CLUSTER_NAME}" mkdir -p "${REGISTRY_DIR}"
cat <<EOF | docker exec -i "${KIND_CLUSTER_NAME}" cp /dev/stdin "${REGISTRY_DIR}/hosts.toml"
[host."http://${DOCKER_LOCAL_REGISTRY}"]
EOF
