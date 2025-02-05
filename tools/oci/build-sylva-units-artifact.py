#!/usr/bin/env python3
#
# This script will push to registry.gitlab.com an OCI registry artifact
# containing the 'sylva-units' Helm chart.
#
# The artifact is pushed as:
#  oci://registry.gitlab.com/sylva-projects/sylva-core/sylva-units:<tag>
#
# The pushed chart will contain a values override file, 'use-oci-registry.values.yaml'
# that can be used to override all external sources definitions (from source_templates and helm_repo_url)
# to make them points to OCI Registry artifacts.
#
#
# ### How to use ###
#
# The script accepts an optional parameter, HELM_CHART_VERSION which will be used as <tag> above if set as env var.
# By default the current commit id will be used as <tag>.
#
# If run manually, the tool can be used after having preliminarily done
# a 'helm registry login registry.gitlab.com' with suitable credentials.

import os
import shutil
import yaml
import re
from pathlib import Path
import atexit
import logging
import sys
# pylama:ignore=W0401
from artifact_utils import *

paths = ArtifactPaths()

# Set up environment and variables
script_dir = Path(__file__).parent
base_dir = script_dir.parent.parent

logger = logging.getLogger()

helm_chart_version = os.getenv(
    "HELM_CHART_VERSION",
    f"0.0.0-git-{run_command(['git', 'rev-parse', 'HEAD']).stdout[0:8]}",
)
logger.info(f'helm_chart_version: {helm_chart_version}')

# Copy the chart directory to the artifact directory and change into it
chart_source_dir = base_dir / 'charts' / 'sylva-units'
chart_dest_dir = paths.artifact_dir / 'sylva-units'
shutil.copytree(chart_source_dir, chart_dest_dir, ignore=shutil.ignore_patterns('test-values'))
os.chdir(chart_dest_dir)

values_yaml_path = chart_dest_dir / "values.yaml"
oci_values_yaml_path = chart_dest_dir / "use-oci-artifacts.values.yaml"

# Create a backup of the use-oci-artifacts.values.yaml file
backup_file_path = str(oci_values_yaml_path) + ".orig"

with open(oci_values_yaml_path, "r") as original_file:
    content = original_file.read()
with open(backup_file_path, "w") as backup_file:
    backup_file.write(content)


# Function to load YAML data from a file
def load_yaml(file_path):
    with open(file_path, "r") as file:
        return yaml.safe_load(file)


# Function to save YAML data to a file
def save_yaml(data, file_path):
    with open(file_path, "w") as file:
        yaml.dump(data, file)


def modify_chart_yaml(chart_yaml_path, version):
    chart_data = load_yaml(chart_yaml_path)
    chart_data["version"] = version
    save_yaml(chart_data, chart_yaml_path)


def merge_dictionaries(original, to_merge):
    for key, value in to_merge.items():
        if key in original:
            if isinstance(original[key], dict) and isinstance(value, dict):
                merge_dictionaries(original[key], value)
            else:
                pass
        else:
            original[key] = value


# ############################## package charts/sylva-units #########################################################
# Modify Chart.yaml
logger.info("Preparing chart...")
chart_yaml_path = chart_dest_dir / "Chart.yaml"
modify_chart_yaml(chart_yaml_path, helm_chart_version)

default_values_data = load_yaml(values_yaml_path)
oci_values_data = load_yaml(oci_values_yaml_path)

default_values_units = default_values_data["units"]

# ############################## sylva-units overrides to consume Helm charts from OCI artifacts ####################

logger.info("Preparing use-oci-artifacts.values.yaml values override file...")

# Here we build a values override file for sylva-units to allow to conveniently
# use sylva-units from OCI registry artifacts.

# The URLs used here match the location at which the script tools/oci/push-helm-charts-artifact.py
# creates them

# ********* Helm-based units relying on 'helm_repo_url' *********

# for those units, we just need to override the URL with the OCI registry URL
#
# Example:
#
# Unit definition:
#
#   cert-manager:
#     enabled: yes
#     helm_repo_url: https://charts.jetstack.io
#     helmrelease_spec:
#     chart:
#       spec:
#         chart: cert-manager
#         version: v1.11.0
#
# Produced override to use the OCI registry:
#
#    cert-manager:
#      helm_repo_url: '{{ .Values.sylva_core_oci_registry }}'
#
# Note that 'sylva_core_oci_registry' defaults to 'oci://registry.gitlab.com/sylva-projects/sylva-core'
# and can be overriden at deployment time


helm_repo_url_overriden_units = {}
for unit in default_values_units:
    if "helm_repo_url" in default_values_units[unit].keys():
        helm_repo_url_overriden_units.update(
            {unit: {"helm_repo_url": "{{ .Values.sylva_core_oci_registry }}"}}
        )


# Implement a workaround for issue: https://gitlab.com/sylva-projects/sylva-core/-/issues/253
# If we find a version with a 0 prefix
# rewrite the version by (a) prepeding a number before the z in x.y.z (for instance 9)
# and (b) keeping the original version in the free-form + field
# 3.25.001 would become 3.25.9001+v3.25.001

regexp_overrides = {}
version_pattern = r"\.0[0-9]"
sub_pattern = r"(.?[0-9]+)\.([0-9]+)\.(0[0-9]+)([\+\-].*)?"
replacement_pattern = r"\1.\2.9\3\4+\1.\2.\3\4"

for unit in default_values_units:
    if "helm_repo_url" in default_values_units[unit]:
        # Extract the version string
        version = (
            default_values_units[unit]
            .get("helmrelease_spec", {})
            .get("chart", {})
            .get("spec", {})
            .get("version", "")
        )  # noqa: E501
        # Check if the version matches the pattern
        if re.search(version_pattern, version):
            new_version = re.sub(sub_pattern, replacement_pattern, version)
            regexp_overrides.update(
                {
                    unit: {
                        "helm_repo_url": "{{ .Values.sylva_core_oci_registry }}",
                        "helmrelease_spec": {
                            "chart": {"spec": {"version": new_version}}
                        },
                    }
                }
            )
        if "helm_chart_versions" in default_values_units[unit]:
            new_chart_versions = {}
            for version_key, version_value in default_values_units[unit][
                "helm_chart_versions"
            ].items():
                if re.search(version_pattern, version_key):
                    new_version = re.sub(sub_pattern, replacement_pattern, version_key)
                    new_chart_versions.update(
                        {new_version: version_value, version_key: None}
                    )
                    # We hardcode the old version to null to avoid being parsed
                    # and failed by the rules in templates/units.yaml
                else:
                    new_chart_versions.update({version_key: version_value})
            regexp_overrides.update(
                {
                    unit: {
                        "helm_repo_url": "{{ .Values.sylva_core_oci_registry }}",
                        "helm_chart_versions": new_chart_versions,
                    }
                }
            )

# ********* Helm-based units relying on 'repo' *********

# For such units, we:
# * replace 'repo: xxx' by 'helm_repo_url'
# * inject the version found in source_templates.xxx.spec.ref.tag into the unit helmrelease_spec.chart.spec.version
#
# Example:
#
# For unit 'local-path-provisioner'...
#
# source_templates:
#   local-path-provisioner:
#     kind: GitRepository
#     spec:
#       url: https://github.com/rancher/local-path-provisioner.git
#       ref:
#         tag: v0.0.23
# units:
#   local-path-provisioner:
#     enabled: yes
#     repo: local-path-provisioner
#     helmrelease_spec:
#       chart:
#         spec:
#           chart: deploy/chart/local-path-provisioner
#
# ...We produce this override:
#
#   local-path-provisioner:
#     repo: null
#     helm_repo_url: '{{ .Values.sylva_core_oci_registry }}'
#     helmrelease_spec:
#       chart:
#         spec:
#           # chart is substituted at runtime by helm_chart_artifact_name
#           # or, if it is not defined, the last item of helmrelease_spec.chart.spec.chart
#           # in this example: "local-path-provisioner"
#           #chart: deploy/chart/local-path-provisioner
#
#           version: v0.0.23


default_values_source_templates = default_values_data["source_templates"]
repo_overrides = {}
for unit in default_values_units:
    if (
        "repo" in default_values_units[unit] and "helmrelease_spec" in default_values_units[unit]
    ):
        repo_overrides.update(
            {
                unit: {
                    "repo": None,
                    "helm_repo_url": "{{ .Values.sylva_core_oci_registry }}",
                    "helmrelease_spec": {
                        "chart": {
                            "spec": {
                                "version": chart_version_from_repo(
                                    default_values_source_templates[
                                        default_values_units[unit]["repo"]])
                            }
                        }
                    },
                }
            }
        )


# ##################### update oci_values_data and write changes to file #############################
merge_dictionaries(oci_values_data["units"], helm_repo_url_overriden_units)
merge_dictionaries(oci_values_data["units"], regexp_overrides)
merge_dictionaries(oci_values_data["units"], repo_overrides)

save_yaml(oci_values_data, oci_values_yaml_path)

if os.getenv("ONLY_PRODUCE_USE_OCI_ARTIFACTS_VALUES", ""):
    output_file = chart_source_dir / "use-oci-artifacts-final.values.yaml"
    logger.info(f"ONLY_PRODUCE_USE_OCI_ARTIFACTS_VALUES is set, will only produce {output_file}")
    save_yaml(oci_values_data, output_file)
    sys.exit(0)

# ############################## wrap up Helm packaging  #######################################
os.chdir(chart_dest_dir)  # Ensure we are in the correct directory
run_command(
    ["helm", "package", "--version", helm_chart_version, str(chart_dest_dir)]
)

# ############################## pushing the artifact to registry ###################################################
tgz_file = f"sylva-units-{helm_chart_version}.tgz"
artifact_name = "sylva-units"
artifact_version = helm_chart_version

atexit.register(cleanup, paths)

process_artifact_helm(artifact_name, artifact_version, tgz_file, paths)
