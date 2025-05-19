#!/bin/bash

source $(dirname $(realpath $0))/tools/shell-lib/common.sh

apply_scripts_init

# called like ./bootstrap.sh --bootstrap-proxies-from-env environment-values/foo ensures the proxies environment variables
# (http_proxy, https_proxy, no_proxy) from bootstrap env are used. Otherwise, ones from local values.yaml or Kustomize build are used
for arg in "$@"; do
    if [[ $arg == "--bootstrap-proxies-from-values" ]]; then
        BOOTSTRAP_PROXIES_FROM_VALUES=true
    else
        remaining_args+=("$arg")
    fi
done

set -- "${remaining_args[@]}"

check_args "$@"

if ! [[ "${BOOTSTRAP_PROXIES_FROM_VALUES:-false}" = "true" ]]; then
    echo "Will use HTTP proxy settings from provided values instead of shell environment"    
    # Try to retrieve proxies config in values passed (in local values.yaml or through Kustomize) and export them for bootstrap cluster
    EXTRACTED_VALUES=$(_kustomize ${ENV_PATH} | python3 ${BASE_DIR}/tools/extractHelmReleaseValues.py --values-path .spec.valuesFrom)
    EVALUATED_PROXIES=$(echo "$EXTRACTED_VALUES" | yq 'with_entries(select(.key == "proxies"))' |\
            helm template bootstrap-cluster-proxies charts/sylva-units --show-only templates/extras/bootstrap-cluster-proxies.yaml --values - | yq .evaluated_proxies)
    export http_proxy="$(yq .http_proxy <<< $EVALUATED_PROXIES)"
    export https_proxy="$(yq .https_proxy <<< $EVALUATED_PROXIES)"
    export no_proxy="$(yq .no_proxy <<< $EVALUATED_PROXIES)"
fi

if [[ ${KUBECONFIG:-} =~ management-cluster-kubeconfig ]]; then
    echo -e "KUBECONFIG seems to point to the management cluster, which doesn't sound ok for 'bootstrap.sh'\n(KUBECONFIG=$KUBECONFIG)"
    exit 1
fi

validate_input_values

check_pivot_has_ran

echo_b "\U0001F503 Preparing bootstrap cluster"
${BASE_DIR}/tools/kind/bootstrap-cluster.sh

ensure_flux

echo_b "\U0001F50E Validate sylva-units values for management cluster"
validate_sylva_units force-management

echo_b "\U0001F5D1 Delete preview chart and namespace for management cluster"
cleanup_preview


set_current_namespace sylva-system

echo_b "\U0001F4DC Install sylva-units Helm release and associated resources"
_kustomize ${ENV_PATH} | \
  define_source | \
  inject_bootstrap_values | \
  kubectl apply -f -

echo_b "\U0001F3AF Trigger reconciliation of units"
# this is just to force-refresh on refreshed parameters
reconcile_sylva_units sylva-system skip-root-dependency-wait

# Attempt to retrieve management-cluster-kubeconfig in background
retrieve_kubeconfig &
KUBECONFIG_PID=$!

echo_b "\U000023F3 Wait for bootstrap units and management cluster to be ready"
sylvactl watch \
  --reconcile \
  --timeout $(ci_remaining_minutes_and_at_most ${BOOTSTRAP_WATCH_TIMEOUT_MIN:-30}) \
  ${SYLVACTL_SAVE:+--save bootstrap-timeline.html} \
  ${SYLVACTL_RECORD:+--record bootstrap-record.yaml} \
  -n sylva-system \
  Kustomization/sylva-system/management-sylva-units

if kill $KUBECONFIG_PID &>/dev/null; then
    echo_b "\U00002717 Failed to retrieve management-cluster kubeconfig"
    exit 1
fi

echo_b "\U000023F3 Wait for units installed on management cluster to be ready"
sylvactl watch \
  --reconcile \
  --kubeconfig management-cluster-kubeconfig \
  --timeout $(ci_remaining_minutes_and_at_most ${MGMT_WATCH_TIMEOUT_MIN:-45}) \
  ${SYLVACTL_SAVE:+--save management-cluster-timeline.html} \
  ${SYLVACTL_RECORD:+--record management-cluster-record.yaml} \
  -n sylva-system \
  Kustomization/sylva-system/sylva-units-status

if [[ -n ${CHECK_TEST_UNITS:-""} ]]; then
    echo_b "\U000023F3 Wait for test units installed on management cluster to be ready"
    sylvactl watch \
      --kubeconfig management-cluster-kubeconfig \
      --reconcile \
      --timeout $(ci_remaining_minutes_and_at_most ${MGMT_WATCH_TIMEOUT_MIN:-20}) \
      ${SYLVACTL_SAVE:+--save apply-management-cluster-tests-timeline.html} \
      -n sylva-system \
      Kustomization/sylva-system/sylva-units-tests-status \
      || true # test-units failures are not critical
fi

display_final_messages
