#!/usr/bin/env bash

set -ueo pipefail

usage() {
    cat >&2 << EOF

Usage: $0 [--additional-objects YAMl_OBJECTS] [--additional-helm-args HELM_ARGS]* ENV_VALUE_DIR

Script to get expected kustomizations (= units) enabled with a given sylva environment values.
It uses:
- 'kustomize build' to get objects injected into the cluster
- 'yq' to parse HelmRelease and associated ConfigMaps/Secrets
- 'helm template' to render Helmrelease and get generated kustomizations

-o, --additional-objects         YAML formatted configmaps/secrets objects containing external values to be computed
-a, --additional-helm-args       Additional helm argument (could be used several times)

EOF
    exit 1
}

SCRIPT_DIR=$(dirname $(realpath $0))
BASE_DIR=$(realpath "$SCRIPT_DIR/..")
SYLVA_CHART_DIR=$(realpath "$BASE_DIR/charts/sylva-units")

ADDITIONAL_OBJECTS=""
ADDITIONAL_HELM_ARGS=""

# Parse args
while [[ $# -gt 0 ]]
do
    key="$1"
    case "${key}" in
        -o|--additional-objects)
            ADDITIONAL_OBJECTS=${2}
            if ! yq . <<< "$ADDITIONAL_OBJECTS" &>/dev/null; then
                echo >&2 "[ERROR] ADDITIONAL_OBJECTS must be valid yaml"
                usage
            fi
            shift
            ;;
        -a|--additional-helm-args)
            ADDITIONAL_HELM_ARGS="$ADDITIONAL_HELM_ARGS ${2}"
            shift
            ;;
        *)
            if [ -d "${1}" ] && [ -f "${1}/kustomization.yaml" ];then
                ENV_VALUE_DIR=${1}
            else
                echo >&2 "[ERROR] ${1} doesn't seem to be a kustomization directory"
                usage
            fi
            ;;
    esac
    shift
done

if [ -z ${ENV_VALUE_DIR-} ]; then
    echo >&2 "[ERROR] ENV_VALUE_DIR must be specified"
    usage
fi

generated_yaml=$(kustomize build --load-restrictor LoadRestrictionsNone ${ENV_VALUE_DIR} | yq .)
full_yaml=$(echo -e "${ADDITIONAL_OBJECTS}\n---\n${generated_yaml}")
helmrelease=$(yq 'select(.kind == "HelmRelease")|select(.metadata.name == "sylva-units")' <<< "$generated_yaml")
secrets=$(yq 'select(.kind == "Secret")' <<< "$full_yaml")
configmaps=$(yq 'select(.kind == "ConfigMap")' <<< "$full_yaml")

helm_values_args=""

chart_values=$(yq '.spec.chart.spec.valuesFiles.[]' <<< "$helmrelease")
for file in $chart_values; do
    if [ -f "${SYLVA_CHART_DIR}/${file}" ]; then
        helm_values_args="$helm_values_args --values ${SYLVA_CHART_DIR}/${file}"
    elif [ -f "${BASE_DIR}/${file}" ]; then
        helm_values_args="$helm_values_args --values ${BASE_DIR}/${file}"
    else
        echo >&2 "[ERROR] chart values file $file not found"
        exit 1
    fi
done

if [ -z "$TEMPDIR" ]; then
    TEMPDIR=$(mktemp -d)
else
    mkdir -p "$TEMPDIR"
fi

hr_valuesFrom_count=$(yq '.spec.valuesFrom | length' <<< "$helmrelease")
for (( i=0; i<hr_valuesFrom_count; i++ )); do
    data_store=$(i=$i yq -P '.spec.valuesFrom[env(i)]' <<< "$helmrelease")
    name=$(yq '.name' <<< "$data_store")
    key=$(yq '.valuesKey' <<< "$data_store")
    kind=$(yq '.kind' <<< "$data_store")
    optional=$(yq '.optional' <<< "$data_store")
    if [[ "$kind" == "ConfigMap" ]]; then
        data=$(name=$name key=$key yq -P 'select(.metadata.name == env(name)) | .data.[env(key)]' <<< "$configmaps")
    fi
    if [[ "$kind" == "Secret" ]]; then
        data=$(name=$name key=$key yq -P 'select(.metadata.name == env(name)) | .data.[env(key)]' <<< "$secrets" | base64 -d | yq .)
    fi
    if [ -n "$data" ]; then
        file="${TEMPDIR}/valuesFrom${kind}${i}.yaml"
        echo "$data" > "$file"
        helm_values_args="$helm_values_args --values ${file}"
    else
        echo >&2 "[WARNING] $kind/$name not found (or empty) - optional = $optional"
    fi
done

echo >&2 "[INFO] Display enabled kustomization list"
echo >&2 "[INFO] Check ${TEMPDIR}/helm_template_debug.log if needed"
sylva_generated=$(helm template test-release ${SYLVA_CHART_DIR} ${helm_values_args} ${ADDITIONAL_HELM_ARGS} --debug --skip-schema-validation 2>${TEMPDIR}/helm_template_debug.log)

yq 'select(.kind == "Kustomization") | {.metadata.name: .} | . as $item ireduce ({}; . * $item) | .[] | key'  <<< "$sylva_generated"
