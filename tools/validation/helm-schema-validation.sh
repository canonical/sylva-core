#!/usr/bin/env bash
set -e

HELM_NAME=${HELM_NAME:-$1}

if [[ -z ${HELM_NAME} ]]; then
  echo "Missing parameter.

  This script expect to find either:

  HELM_NAME environment variable defined with the name of the chart to validate

  or the name of the chart to validate pass as a parameter.

  helm-schema-validation.sh sylva-units

  "
  exit 1
fi

function helm() { $(/usr/bin/which helm) "$@" 2> >(grep -v 'found symbolic link' >&2); }

export BASE_DIR=$( cd "$(dirname "${BASH_SOURCE[0]}")/../.." ; pwd -P )

chart_dir=${BASE_DIR}/charts/${HELM_NAME}

RED='\033[0;31m'
NC='\033[0m'
echo -e "\e[0Ksection_start:`date +%s`:lint_schema\r\e[0K--------------- Lint Schema YAML file"
echo "Lint $chart_dir/values.schema.yaml ..."
yamllint --no-warnings -c ${BASE_DIR}/.gitlab/ci/configuration/yamllint.yaml $chart_dir/values.schema.yaml
echo "   DONE"
echo -e "\e[0Ksection_end:`date +%s`:lint_schema\r\e[0K"

echo -e "\e[0Ksection_start:`date +%s`:check_generation\r\e[0K--------------- Check that ${HELM_NAME}/values.schema.json was regenerated from values.schema.yaml ..."
${BASE_DIR}/tools/generate_json_schema.py -o /tmp/values.schema.json
if ! cmp -s /tmp/values.schema.json $chart_dir/values.schema.json ; then
  echo -e "${RED}$chart_dir/values.schema.json wasn't generated with $chart_dir/values.schema.yaml${NC}"
  exit 1
fi
echo "   DONE"
echo -e "\e[0Ksection_end:`date +%s`:check_generation\r\e[0K"

echo -e "\e[0Ksection_start:`date +%s`:validate_schema\r\e[0K--------------- Validate that the chart values schema contains a valid JSON Schema ..."
curl https://json-schema.org/draft/2020-12/schema -s -o /tmp/draft2020-12.json
python3 -m jsonschema -o pretty /tmp/draft2020-12.json -i /tmp/values.schema.json
echo "   DONE"
echo -e "\e[0Ksection_end:`date +%s`:validate_schema\r\e[0K"
