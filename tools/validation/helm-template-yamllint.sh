#!/usr/bin/env bash

set -e
set -o pipefail

HELM_NAME=${HELM_NAME:-$1}

if [[ -z ${HELM_NAME} ]]; then
  echo "Missing parameter.

  This script expect to find either:

  HELM_NAME environment variable defined with the name of the chart to validate

  or the name of the chart to validate pass as a parameter.

  helm-template-yamllint.sh sylva-units

  "
  exit 1
fi

function helm() { $(/usr/bin/which helm) $@ 2> >(grep -v 'found symbolic link' >&2); }

export BASE_DIR=$( cd "$(dirname "${BASH_SOURCE[0]}")/../.." ; pwd -P )

chart_dir=${BASE_DIR}/charts/${HELM_NAME}


# for sylva-units, specifically we want to ensure that
# 'values.yaml' should not have any units.x.enabled fields, unless set to false
if [[ $HELM_NAME == "sylva-units" ]]; then
  units_default_enabled=$(yq '[.units | ... comments="" | to_entries | .[] | select((.value.enabled != null) and (.value.enabled != false) and (.value.enabled != "no"))] | map(.key)' $chart_dir/values.yaml)
  if [[ $units_default_enabled != '[]' ]]; then
    echo -e "The following units have .enabled defined in 'values.yaml' with a value which isn't 'no' or 'false':\n$units_default_enabled\n\n"
    echo "This is not allowed in sylva-units 'values.yaml':"
    echo "  - in 'values.yaml' all units are disabled by default, and we don't set 'units.xxx.enabled: true' there anymore"
    echo "  - when there is some conditionality to decide to enable a unit or not:"
    echo "    * either this is about necessary conditions, in that case units.xxx.enabled_conditions needs to be used"
    echo "    * or this is about wanting to have a unit be enabled _by default_ conditionally in the mgmt cluster:"
    echo "      in this case the condition will be put in 'units.xxx.enabled', but in 'management.values.yaml'"
    echo "  - 'workload-cluster.values.yaml' is the place where to set 'units.xxx.enabled' for units that we want to enable in workload clusters"
    echo
    exit -1
  fi
fi

echo -e "\e[0Ksection_start:`date +%s`:helm_dependency_build\r\e[0K--------------- helm dependency build"

helm dependency build $chart_dir

echo -e "\e[0Ksection_end:`date +%s`:helm_dependency_build\r\e[0K"

echo -e "\e[0Ksection_start:`date +%s`:helm_base_values\r\e[0K--------------- Checking default values with 'helm template' and 'yamllint' (for sylva-units chart all units enabled) ..."

# This applies only to sylva-units chart where we want to check that templating
# works fine with all units enabled
yq eval '{"units": .units | ... comments="" | to_entries | map({"key":.key,"value":{"enabled":true,"enabled_conditions":[]}}) | from_entries}' $chart_dir/values.yaml > /tmp/all-units-enabled.yaml

helm template ${HELM_NAME} $chart_dir --values /tmp/all-units-enabled.yaml \
| yamllint - -d "$(cat < ${BASE_DIR}/.gitlab/ci/configuration/yamllint.yaml) $(cat < ${BASE_DIR}/.gitlab/ci/configuration/yamllint-helm-template-rules)"

echo OK
echo -e "\e[0Ksection_end:`date +%s`:helm_base_values\r\e[0K"

test_dirs=$(find $chart_dir/test-values -mindepth 1 -maxdepth 1 -type d)
if [ -d $chart_dir/test-values ] && [ -n "$test_dirs" ] ; then
  for dir in $test_dirs ; do
    echo -e "\e[0Ksection_start:`date +%s`:helm_more_values\r\e[0K--------------- Checking values from test-values/$(basename $dir) with 'helm template' and 'yamllint' ..."

    set +e
    helm template ${HELM_NAME} $chart_dir $(ls $dir/*.y*ml | sort | grep -v test-spec.yaml | sed -e 's/^/--values /') \
      | yamllint - -d "$(cat < ${BASE_DIR}/.gitlab/ci/configuration/yamllint.yaml) $(cat < ${BASE_DIR}/.gitlab/ci/configuration/yamllint-helm-template-rules)"
    exit_code=$?
    set -e

    if [[ -f $dir/test-spec.yaml && $(yq .require-failure $dir/test-spec.yaml) == "true" ]]; then
        expected_exit_code=1
        error_message="This testcase is supposed to make 'helm template ..| yamllint ..' fail, but it actually succeeded."
        success_message="This negative testcase expectedly made 'helm template ..| yamllint ..' fail."
    else
        expected_exit_code=0
        error_message="Failure when running 'helm template ..| yamllint ..' on this test case."
    fi

    if [[ $exit_code -ne $expected_exit_code ]]; then
      echo $error_message
      exit -1
    else
      echo $success_message
    fi

    echo OK
    echo -e "\e[0Ksection_end:`date +%s`:helm_more_values\r\e[0K"
  done
fi

# for sylva-units, we also want to ensure things about the default values
# in particular that they use _patches, _components and _postRenderers
# instead of their equivalents without the '_'
if [[ $HELM_NAME == "sylva-units" ]]; then
  for value_file in $chart_dir/values.yaml $(ls $chart_dir/*.values.yaml); do
    echo -e "\e[0Ksection_start:`date +%s`:additional_check_$value_file\r\e[0K--------------- checking patches/components/postRenderers in $value_file ..."
    echo "--- "
    postRenderers=$(yq eval '[.units | to_entries | .[] | select(.value.helmrelease_spec.postRenderers)] | map(.key) | join(", ")' $value_file)
    if [[ -n $postRenderers ]]; then
      echo "Some units defined in $value_file use helmrelease_spec.postRenderers, although they should use helmrelease_spec._postRenderers instead: $postRenderers"
      exit -1
    fi

    components=$(yq eval '[.units | to_entries | .[] | select(.value.kustomization_spec.components)] | map(.key) | join(", ")' $value_file)
    if [[ -n $components ]]; then
      echo "Some units defined in $value_file use kustomization_spec.components, although they should use kustomization_spec._components instead: $components"
      exit -1
    fi

    patches=$(yq eval '[.units | to_entries | .[] | select(.value.kustomization_spec.patches)] | map(.key) | join(", ")' $value_file)
    if [[ -n $patches ]]; then
      echo "Some units defined in $value_file use kustomization_spec.patches, although they should use kustomization_spec._patches instead: $patches"
      exit -1
    fi

    echo -e "\e[0Ksection_end:`date +%s`:additional_check_$value_file\r\e[0K"
  done
fi
