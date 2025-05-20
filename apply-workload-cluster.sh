#!/bin/bash
#
# This script can be used to install the workload clusters defined at path environment-values/workload-clusters/x using Kustomize
#
# This script will act on the kubectl context of a Sylva management cluster,
# if the 'management-cluster-kubeconfig' file is found, in which case it will use it, otherwise exit.

source $(dirname $(realpath $0))/tools/shell-lib/common.sh

apply_scripts_init

check_args "$@"

wc_namespace=$(basename ${ENV_PATH})

validate_input_values

check_apply_kustomizations

if [[ -f management-cluster-kubeconfig ]]; then
    export KUBECONFIG=${KUBECONFIG:-management-cluster-kubeconfig}
else
    echo_b "management-cluster-kubeconfig file is not present in ${PWD}"
    exit 1
fi

if ! (kubectl get nodes > /dev/null); then
    echo_b "Cannot access cluster, 'kubectl get nodes' gives:"
    kubectl get nodes
    exit 1
fi

check_management_kubeconfig

if ! (kubectl -n sylva-system get cm sylva-units-status > /dev/null); then
   echo_b "The sylva-units-status configmap doesn't exist. Please check the status of the management-cluster"
   exit 1
fi

echo_b "\U0001F4DC Install a sylva-units Helm release for workload cluster $wc_namespace"

suspend_sylva_units $wc_namespace

_kustomize ${ENV_PATH} | define_source | set_wc_namespace | kubectl apply -f -

echo_b "\U0001F3AF Trigger reconciliation of units"

# this is just to force-refresh on refreshed parameters
reconcile_sylva_units $wc_namespace

echo_b "\U000023F3 Wait for units to be ready"
sylvactl watch \
  --kubeconfig management-cluster-kubeconfig \
  --reconcile \
  --timeout $(ci_remaining_minutes_and_at_most ${APPLY_WC_WATCH_TIMEOUT_MIN:-30}) \
  ${SYLVACTL_SAVE:+--save apply-workload-cluster-timeline.html} \
  ${SYLVACTL_RECORD:+--record apply-workload-cluster-record.yaml} \
  -n $wc_namespace \
  Kustomization/$wc_namespace/sylva-units-status

if [[ -n ${CHECK_TEST_UNITS:-""} ]]; then
    echo_b "\U000023F3 Wait for test units to be ready"

    sylvactl watch \
      --kubeconfig management-cluster-kubeconfig \
      --reconcile \
      --exit-condition="message=values don't meet the specifications of the schema" \
      --timeout $(ci_remaining_minutes_and_at_most ${APPLY_WC_WATCH_TIMEOUT_MIN:-20}) \
      ${SYLVACTL_SAVE:+--save apply-workload-cluster-tests-timeline.html} \
      -n sylva-system \
      Kustomization/sylva-system/sylva-units-tests-status \
      || true # test-units failures are not critical
fi

display_final_messages
