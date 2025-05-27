#!/bin/bash
#
# This script can be used to:
# * install the system on an already existing k8s cluster built in an ad-hoc way
#   (in that case, Flux will be installed if not already present)
# * update the system on a cluster where it is already installed with the bootstrap mechanism
#
# This script will act on whatever is the current kubectl config unless
# the 'management-cluster-kubeconfig' file is found, in which case it will use it.

source $(dirname $(realpath $0))/tools/shell-lib/common.sh

apply_scripts_init

check_args "$@"

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

ensure_sylva_units_operator

echo_b "\U0001F4DC Update sylva-units Helm release and associated resources"

suspend_sylva_units

_kustomize ${ENV_PATH} | define_source | kubectl apply -f -

echo_b "\U0001F3AF Trigger reconciliation of units"

# this is just to force-refresh on refreshed parameters
reconcile_sylva_units sylva-system

echo_b "\U000023F3 Wait for units to be ready"

sylvactl watch \
  --kubeconfig management-cluster-kubeconfig \
  --reconcile \
  --timeout $(ci_remaining_minutes_and_at_most ${APPLY_WATCH_TIMEOUT_MIN:-20}) \
  ${SYLVACTL_SAVE:+--save apply-management-cluster-timeline.html} \
  ${SYLVACTL_RECORD:+--record apply-management-cluster-record.yaml} \
  -n sylva-system \
  Kustomization/sylva-system/sylva-units-status

if [[ -n ${CHECK_TEST_UNITS:-""} ]]; then
    echo_b "\U000023F3 Wait for test units to be ready"

    sylvactl watch \
      --kubeconfig management-cluster-kubeconfig \
      --reconcile \
      --exit-condition="message=values don't meet the specifications of the schema" \
      --timeout $(ci_remaining_minutes_and_at_most ${APPLY_WATCH_TIMEOUT_MIN:-20}) \
      ${SYLVACTL_SAVE:+--save apply-management-cluster-tests-timeline.html} \
      -n sylva-system \
      Kustomization/sylva-system/sylva-units-tests-status \
      || true # test-units failures are not critical
fi

display_final_messages
