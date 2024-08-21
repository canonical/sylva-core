#!/bin/bash
#
# See 'root-dependency' unit for context about what this script does.
#
# This script checks that all Kustomizations have been
# freshly updated for the current revision of the Helm release of sylva-units
# and are waiting on their dependency on the corresponding 'root-dependency-<n>'
# Kustomization to be ready.
#
# We apply the following criteria:
# - (a Kustomization named root-dependency-* is ignored)
# - Kustomization has 'root-dependency-$HELM_REVISION' in spec.dependsOn

set -e
set -o pipefail


# how long to wait for all Kustomizations to meet the criteria
# (we shouldn't need to wait for long, except that if k8s API is slow
#  it may require some time for kubectl to see all Kustomizations, and
#  unfortunately it may declare that a Kustomization didn't meet the wait
#  criteria even if just didn't had time to see it)
WAIT_TIMEOUT=${WAIT_TIMEOUT:-60s}

# we setup an exit trap to display the status of all Kustomization
# if one of the 'kubectl wait' fails
function error_trap() {
    echo "--- summary of resources"
    kubectl get Kustomizations -l sylva-units/root-dependency-wait
}
trap error_trap ERR

echo "--- waiting for Kustomizations to be labeled with sylva-units-helm-revision=$HELM_REVISION"

kubectl wait Kustomization -l sylva-units/root-dependency-wait --timeout $WAIT_TIMEOUT \
  --for=jsonpath="{.metadata.annotations.sylva-units-helm-revision}=$HELM_REVISION"
