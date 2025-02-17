#!/usr/bin/env bash

set -ueo pipefail

usage() {
    cat >&2 << EOF

Usage: $0 ENV_VALUE_DIR

Script to get expected kustomizations (= units) enabled from given sylva environment values.
It uses a customized preview cluster to make flux helm controller to compute sylva-units helm release and extract units kustomization names

EOF
    exit 1
}

SCRIPT_DIR=$(dirname $(realpath $0))
BASE_DIR=$(realpath "$SCRIPT_DIR/..")
OUTPUT_FILE=${OUTPUT_FILE:-$(mktemp)}

cd $BASE_DIR

source tools/shell-lib/common.sh
trap : EXIT  # No need to run debug-on-exit here

check_args

echo -e "\U0001F503 Preparing kind cluster"
./tools/kind/bootstrap-cluster.sh
ensure_flux

if [[ "$(kubectl get ns)" != *"sylva-units-preview"*  ]];then
    kubectl create ns sylva-units-preview
    kubectl create configmap -n sylva-units-preview shared-workload-clusters-settings --from-literal=values=
    kubectl create secret generic -n sylva-units-preview shared-workload-clusters-settings --from-literal=values=
fi

echo -e "\U0001F50E Deploying sylva-units values in preview mode"
validate_sylva_units force-workload

echo -e "🧐 Extracting generated units"
UNITS=$(kubectl get kustomization -n sylva-units-preview --selector 'sylva-units.unit' --output=yaml | yq '.items[] | .metadata.name')
echo "$UNITS" | tee $OUTPUT_FILE
echo ">> Unit list written in $OUTPUT_FILE"

cleanup_preview
