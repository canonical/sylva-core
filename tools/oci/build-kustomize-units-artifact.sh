#!/bin/bash
#
# This script will push to registry.gitlab.com an OCI registry artifact
# containing the content of 'kustomize-units' directory, after replacing
# all remote resources present in 'kustomization.yaml' files by an
# equivalent file included in the artifact.
#
# The artifact is pushed as:
#  oci://registry.gitlab.com/sylva-projects/sylva-core/kustomize-units:<tag>
#
# The script accepts an optional parameter, which will be used as <tag> above.
# By default the current commit id will be used as <tag>.
#
# If run manually, the tool can be used after having preliminarily done
# a 'docker login registry.gitlab.com' with suitable credentials.
#
# Requirements:
# - kustomize (for 'kustomize build')
# - flux (used to push the artifact)

set -eu
set -o pipefail

BASE_DIR="$(realpath $(dirname $0)/../..)"

OCI_REGISTRY_ARTIFACT="${OCI_REGISTRY:-oci://registry.gitlab.com/sylva-projects/sylva-core}/kustomize-units"

function process_kustomization {
    # processes a kustomization.yaml (given as $1):
    # - make a copy of the kustomization, keeping only 'resources'
    # - render the kustomization with 'kustomize build'
    # - replaces 'resources' in the original kustomization by the
    #   result of the rendering
    local kustomization=$1

    kdir=$(dirname $kustomization)

    mv $kustomization ${kustomization}.orig

    cat > $kustomization << EOF
apiVersion: $(yq -r .apiVersion ${kustomization}.orig)
kind: $(yq -r .kind ${kustomization}.orig)
EOF

    yq '{"resources": .resources}' $kustomization.orig >> $kustomization

    echo -n "  locally rendering remote resources..."
    kustomize build $kdir -o $kdir/local-resources.yaml
    echo "OK"

    mv $kustomization.orig $kustomization

    yq -i '.resources = ["local-resources.yaml"]' $kustomization
}

# if we run in a gitlab CI job, then we use the CI_REPOSITORY_URL provided by gitlab job environment
if [[ -n ${CI_REPOSITORY_URL:-} ]]; then
  artifact_source="${CI_REPOSITORY_URL/gitlab-ci-token*@/}"
else
  artifact_source="$(git config --get remote.origin.url)"
fi
artifact_revision="$(git branch --show-current)/$(git rev-parse HEAD)"
artifact_tag="${1:-$(git rev-parse --short HEAD)}"

processed_kustomize_units=$(mktemp -d -t sylva-core-kustomize-units-XXXXXX)
trap "rm -rf $processed_kustomize_units" EXIT INT


cp -r $BASE_DIR/kustomize-units $processed_kustomize_units

echo "(working in $processed_kustomize_units)"
echo

cd $processed_kustomize_units

for kustomization in $(find kustomize-units -type f | grep -E '.*/kustomization[.]ya?ml' | sort); do
    if (yq -r .resources[] $kustomization | grep  -E '(https?|ssh)://' > /dev/null); then
        echo "* $(dirname $kustomization), processing ..."
        process_kustomization $kustomization
    else
        echo "* $(dirname $kustomization): no remote resource, skipping"
    fi
done

grep -rnsE -- '- +(https?|ssh)://' && (echo "There are remaining remote URLs in some kustomization!" ; exit 1)

echo
echo "Pushing kustomize-units artifact to OCI registry..."

# if we run in a gitlab CI job, then we use the credentials provided by gitlab job environment
if [[ -n ${CI_REGISTRY_USER:-} ]]; then
    creds="--creds $CI_REGISTRY_USER:$CI_REGISTRY_PASSWORD"
fi

flux push artifact $OCI_REGISTRY_ARTIFACT:$artifact_tag \
	--path=. \
	--source=$artifact_source \
	--revision=$artifact_revision \
    ${creds:-}
