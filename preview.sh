#!/bin/bash

source $(dirname $(realpath $0))/tools/shell-lib/common.sh

apply_scripts_init

check_args "$@"

if ! command -v helm &>/dev/null; then
    echo "helm binary is required by this tool, please install it"
    exit 1
fi

validate_input_values

if [[ -f management-cluster-kubeconfig ]]; then
    echo_b "\U0001F503 Reusing management cluster"
    export KUBECONFIG=${KUBECONFIG:-management-cluster-kubeconfig}
else
    echo_b "\U0001F503 Preparing bootstrap cluster"
    ${BASE_DIR}/tools/kind/bootstrap-cluster.sh
fi

ensure_flux

echo_b "\U0001F4C1 Create & install sylva-units preview Helm release"
validate_sylva_units

echo_b "\U000023F3 Retrieve chart user values"
helm get values -n sylva-units-preview sylva-units

echo_b "\U000023F3 Retrieve the final set of values (after gotpl rendering)"
kubectl get secrets -n sylva-units-preview sylva-units-values -o template="{{ .data.values }}" | base64 -d

echo_b "\U0001F5D1 Delete preview chart and namespace"
cleanup_preview
