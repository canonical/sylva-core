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

echo "--- deleting leftover root-dependency-<n> Kustomizations for older versions"
kubectl get Kustomization -l sylva-units.unit=root-dependency -o json | jq -r '.items[] | select(.metadata.annotations."sylva-units-helm-revision" != "'$HELM_REVISION'") | .metadata.name' \
    | xargs -r kubectl delete Kustomization || true

# this is a safeguard:
echo "--- deleting leftover root-dependency-<n> HelmReleases for older versions"
kubectl get HelmReleases -o json -l sylva-units.unit=root-dependency | jq -r '.items[] | select((.metadata.labels."sylva-units.version" // "") != "'$HELM_REVISION'") | .metadata.name' \
    | xargs -r kubectl delete HelmRelease || true

# this is a safeguard only relevant when upgrading from a version of sylva before https://gitlab.com/sylva-projects/sylva-core/-/merge_requests/3318
echo "--- deleting leftover root-dependency-<n>-cm ConfigMaps for older versions"
kubectl get ConfigMap -o json | jq -r '.items[] | select((.metadata.name | startswith("root-dependency-")) and (.metadata.labels."sylva-units.version" // "" != "'$HELM_REVISION'")) | .metadata.name' \
    | xargs -r kubectl delete ConfigMap || true

echo "--- waiting for Kustomizations to be labeled with sylva-units-helm-revision=$HELM_REVISION"

kubectl get Kustomizations -o name -l sylva-units/root-dependency-wait \
 | xargs -n1 -P500 \
     kubectl wait --timeout 10s \
                  --for=jsonpath="{.metadata.annotations.sylva-units-helm-revision}=$HELM_REVISION"
