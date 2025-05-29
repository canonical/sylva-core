#!/bin/bash

# Create a kind cluster with adapted configuration for sylva bootstrap:
# - If DOCKER_IP is set, it will bind cluster API to this address to make it reachable in CI
# - Otherwise it will mount /var/lib/docker.sock in kind cluster
# - If environment values files is passed as argument, or found at ${ENV_PATH}/values.yaml path, it will be parsed to
#     - mount /var/lib/docker.sock in kind cluster if capd is used
#     - instruct kind to use registry mirrors according to registry_mirrors configuration
# If a specific Kind cluster K8s version is needed, set the ENV variable KIND_CLUSTER_K8S_VERSION at runtime of bootstrap.sh

set -ue
set -o pipefail

export BASE_DIR="$(realpath $(dirname ${BASH_SOURCE[0]})/../..)"
export PATH=${BASE_DIR}/bin:${PATH}
KIND_CLUSTER_K8S_VERSION=${KIND_CLUSTER_K8S_VERSION:-}

for BINARY in kubectl kind helm yq; do
    if ! command -v $BINARY &>/dev/null; then
        echo "$BINARY is required by this tool, please install it"
        exit 1
    fi
done

# unset KUBECONFIG in case it would refer to management-cluster-kubeconfig,
# otherwise kind kubeconfig would be saved in this file (which may be overwritten by bootstrap.sh...)
[[ "${KUBECONFIG:-}" =~ management-cluster-kubeconfig$ ]] && unset KUBECONFIG
# Check if there is already a functional kind cluster
if kind get clusters 2>/dev/null | grep -q "^$KIND_CLUSTER_NAME\$"; then
    if ! kubectl --kubeconfig=<(kind get kubeconfig --name $KIND_CLUSTER_NAME 2>/dev/null) get nodes &>/dev/null; then
        echo "Found an existing kind cluster named $KIND_CLUSTER_NAME that does not seem to be functional"
        echo "Please delete it using \"kind delete cluster --name $KIND_CLUSTER_NAME\" and try again"
        exit 1
    elif [[ $(kubectl config current-context 2>/dev/null) == kind-${KIND_CLUSTER_NAME} ]]; then
        echo "Kind cluster $KIND_CLUSTER_NAME is already configured and used as current kubeconfig context"
        exit 0
    elif ! kubectl config use-context kind-${KIND_CLUSTER_NAME} &>/dev/null; then
        echo "Failed to use kind context kind-${KIND_CLUSTER_NAME} in current kubeconfig"
        echo "Please use KUBECONFIG in which it was defined, or delete kind cluster named ${KIND_CLUSTER_NAME}"
        exit 1
    else
        echo "Found an existing kind cluster named $KIND_CLUSTER_NAME, using it for bootstrap"
        exit 0
    fi
fi

KIND_CONFIG=$(cat <<EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
networking:
  podSubnet: "${KIND_POD_SUBNET}"
  serviceSubnet: "${KIND_SVC_SUBNET}"
nodes:
- role: control-plane
EOF
)

KIND_CONFIG_REGISTRY=$(cat <<EOF
containerdConfigPatchesJSON6902:
- '[{"op": "add", "path": "/plugins/io.containerd.grpc.v1.cri/registry", "value": {"config_path": "/etc/containerd/registry.d"}}]'
EOF
)

EXTRACTED_VALUES=$(_kustomize ${ENV_PATH} | python3 ${BASE_DIR}/tools/extractHelmReleaseValues.py --values-path .spec.valuesFrom)

# Try to retrieve registry config in values passed (in local values.yaml or through Kustomize) and prepare KIND_CONFIG consequently
if echo "$EXTRACTED_VALUES" | yq -e '.registry_mirrors.hosts_config | length > 0' &>/dev/null; then
    function helm() { $(/usr/bin/which helm) "$@" 2> >(grep -v 'found symbolic link' >&2); }
    export KIND_CONFIG_DIRECTORY=${BASE_DIR}/tools/kind/registry.d/
    mkdir -p $KIND_CONFIG_DIRECTORY
    rm -Rf $KIND_CONFIG_DIRECTORY/*
    KIND_CONFIG=$(echo -e "$KIND_CONFIG\n$KIND_CONFIG_REGISTRY" | yq)
    KIND_CONFIG=$(echo "$KIND_CONFIG" | yq '.nodes[0].extraMounts += [{"hostPath": env(KIND_CONFIG_DIRECTORY), "containerPath": "/etc/containerd/registry.d"}]')
    echo "$EXTRACTED_VALUES" | yq 'with_entries(select(.key == "registry_mirrors"))' |\
        helm template kind-registry-config ${BASE_DIR}/charts/sylva-units --show-only templates/extras/kind.yaml --values - | yq .script | bash
fi

# Try to retrieve bootstrap_ip config in values.yaml and expose ironic and os-image-server ports if defined
if echo "$EXTRACTED_VALUES" | yq -e '.metal3.bootstrap_ip'  &>/dev/null; then
    BOOTSTRAP_IP=$(echo "$EXTRACTED_VALUES" | yq -e '.metal3.bootstrap_ip')
    for port in "5050/TCP" "6180/TCP" "6185/TCP" "6385/TCP" "80/TCP" "443/TCP"; do
        KIND_CONFIG=$(echo "$KIND_CONFIG" | yq '.nodes[0].extraPortMappings += [{"containerPort": '${port%/*}', "hostPort": '${port%/*}', "listenAddress": "'$BOOTSTRAP_IP'", "protocol": "'${port#*/}'"}]')
    done
fi

# Inject nomasquerade service if libvirt-metal is enabled
if echo "$EXTRACTED_VALUES" | yq -e '.libvirt_metal.nodes | length > 0' &>/dev/null; then
    export MASQ_SERVICE_PATH=${BASE_DIR}/tools/kind/systemd/nomasquerade.service
    KIND_CONFIG=$(echo "$KIND_CONFIG" | yq '.nodes[0].extraMounts += [{"hostPath": env(MASQ_SERVICE_PATH), "containerPath": "/etc/systemd/system/nomasquerade.service"}]')
    export MASQ_SCRIPT_PATH=${BASE_DIR}/tools/kind/systemd/iptables.sh
    KIND_CONFIG=$(echo "$KIND_CONFIG" | yq '.nodes[0].extraMounts += [{"hostPath": env(MASQ_SCRIPT_PATH), "containerPath": "/usr/local/bin/iptables.sh"}]')
    LIBVIRT_METAL_ENABLED=1
fi

# Use docker-in-docker address as api endpoint when running in docker-in-docker
if [[ -n "${DOCKER_IP:-}" ]]; then
    KIND_CONFIG=$(echo "$KIND_CONFIG" | yq '.networking.apiServerPort = 6443 | .networking.apiServerAddress = env(DOCKER_IP)')
elif echo "$EXTRACTED_VALUES" | yq -e '.cluster.capi_providers.infra_provider == "capd"' &>/dev/null; then
    KIND_CONFIG=$(echo "$KIND_CONFIG" | yq '.nodes[0].extraMounts += [{"hostPath": "/var/run/docker.sock", "containerPath": "/var/run/docker.sock"}]')
fi

KIND_CONFIG_LOCAL_REGISTRY=$(cat <<EOF
containerdConfigPatches:
- |-
  [plugins."io.containerd.grpc.v1.cri".registry]
    config_path = "/etc/containerd/certs.d"
EOF
)
if [[ "${DOCKER_LOCAL_REGISTRY}" != "" ]]; then
  KIND_CONFIG=$(echo -e "$KIND_CONFIG\n$KIND_CONFIG_LOCAL_REGISTRY" | yq)
fi

echo -e "Creating kind cluster with following config:\n$KIND_CONFIG"

if echo "$EXTRACTED_VALUES" | yq -e '.registry_mirrors.hosts_config."docker.io".[0].mirror_url' &>/dev/null; then
    DOCKER_REGISTRY_MIRROR=$(echo "$EXTRACTED_VALUES" | yq -e '.registry_mirrors.hosts_config."docker.io".[0].mirror_url' | sed 's~http[s]*://~~g')

    # Remove version path from mirror url if present
    if [[ $DOCKER_REGISTRY_MIRROR =~ /v[0-9]+/ ]]; then
        DOCKER_REGISTRY_MIRROR=$(echo "$DOCKER_REGISTRY_MIRROR" | sed 's~/v[0-9]\+/~/~g')
    fi
fi
if [[ -n "$KIND_CLUSTER_K8S_VERSION" ]]; then
    if [[ ! "$KIND_CLUSTER_K8S_VERSION" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        echo -e "Error: KIND_CLUSTER_K8S_VERSION must match pattern 'vX.Y.Z' (e.g., v1.31.0)."
        exit 1
    fi
    KIND_IMAGE="${DOCKER_REGISTRY_MIRROR:+$DOCKER_REGISTRY_MIRROR/}kindest/node:$KIND_CLUSTER_K8S_VERSION"
else
    KINDEST_VERSION=$(strings $(which kind) |grep kindest/node:v | sed -e 's~.*\(kindest/node:.*\)@.*~\1~')
    KIND_IMAGE="${DOCKER_REGISTRY_MIRROR:+$DOCKER_REGISTRY_MIRROR/}$KINDEST_VERSION"
fi


echo "$KIND_CONFIG" | kind create cluster --name "$KIND_CLUSTER_NAME" ${KIND_IMAGE:+--image "$KIND_IMAGE"} --config=-

if [[ -n ${LIBVIRT_METAL_ENABLED:-} ]]; then
    docker exec ${KIND_CLUSTER_NAME}-control-plane systemctl --now enable nomasquerade.service
    if [[ "${DOCKER_LOCAL_REGISTRY}" != "" ]]; then
        bash ${BASE_DIR}/tools/kind/add-kind-local-registry.sh "$KIND_CLUSTER_NAME"-control-plane "${DOCKER_LOCAL_REGISTRY}"
    fi
fi
