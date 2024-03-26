#!/bin/bash
#
# This script can be used to:
# * install the system on an already existing k8s cluster built in an ad-hoc way
#   (in that case, Flux will be installed if not already present)
# * update the system on a cluster where it is already installed with the bootstrap mechanism
#
# This script will act on whatever is the current kubectl config unless
# the 'management-cluster-kubeconfig' file is found, in which case it will use it.

source $(dirname $0)/tools/shell-lib/common.sh

check_args

validate_input_values

check_apply_kustomizations

if [[ -f management-cluster-kubeconfig ]]; then
    export KUBECONFIG=${KUBECONFIG:-management-cluster-kubeconfig}
fi

if ! (kubectl get nodes > /dev/null); then
    echo_b "Cannot access cluster, 'kubectl get nodes' gives:"
    kubectl get nodes
    exit 1
fi

check_management_kubeconfig

ensure_flux

echo_b "\U0001F4DC Update sylva-units Helm release and associated resources"

fix_sylva_units_existing_source

_kustomize ${ENV_PATH} | \
  define_source | \
  kubectl apply -f -

echo_b "\U0001F3AF Trigger reconciliation of units"

# this is just to force-refresh on refreshed parameters
reconcile_sylva_units

echo_b "\U000023F3 Wait for units to be ready"

sylvactl watch \
  --kubeconfig management-cluster-kubeconfig \
  --reconcile \
  --timeout $(ci_remaining_minutes_and_at_most ${APPLY_WATCH_TIMEOUT_MIN:-20}) \
  ${SYLVACTL_SAVE:+--save apply-management-cluster-timeline.html} \
  -n sylva-system \
  Kustomization/sylva-system/sylva-units-status

display_final_messages
