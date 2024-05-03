#!/bin/bash

# Script name: helm-validate.sh
# Description: A script to validate Helm charts using helm-schema-validation.sh or helm-template-yamllint.sh
# renovate: datasource=docker
HELM_TOOLBOX_IMAGE=${HELM_TOOLBOX_IMAGE:-registry.gitlab.com/sylva-projects/sylva-elements/container-images/helm-toolbox:1.0.1}

BASE_DIR=$(realpath $(dirname $0)/../../)


# Check if the required arguments are passed
if [ -z "$1" ] || [ -z "$2" ]; then
  echo "Usage: $0 <chart-directory> <option-script> "
  echo "option-script is schema-validation or yamllint"
  exit 1
fi

# Get the directory and validation script passed as arguments
CHART_DIR=${CHART_DIR:-$BASE_DIR/charts/sylva-units}
OPT_SCRIPT=$2

# Check if the directory exists
if [ ! -d "$CHART_DIR" ]; then
  echo "The specified directory does not exist: $CHART_DIR"
  exit 1
fi

if [ "$OPT_SCRIPT" == "schema-validation" ]; then
  VALIDATION_SCRIPT="helm-schema-validation.sh"
elif [ "$OPT_SCRIPT" == "yamllint" ]; then
  VALIDATION_SCRIPT="helm-template-yamllint.sh"
else
  echo >&2 "Invalid option-script parameter specified: $OPT_SCRIPT"
  echo >&2 "Allowed values are 'schema-validation' or 'yamllint'"
  exit 1
fi

# Run the selected Helm validation script using Docker
docker run --rm \
  -v $BASE_DIR:/vol \
  -w /vol \
  $HELM_TOOLBOX_IMAGE \
  $VALIDATION_SCRIPT \
  $CHART_DIR