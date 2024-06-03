#!/usr/bin/env python

import itertools
import json
import os
import random
import re
import sys
import urllib.request
import yaml

"""
This script is used in CI for generating list of deployment jobs
"""

SCRIPT_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
BASE_DIR = os.path.abspath(f"{SCRIPT_DIR}/../../..")
TEMPLATE_FILE = os.path.abspath(
    f"{BASE_DIR}/.gitlab/ci/main-pipeline-deployment-tests.template.yml"
)

CHILD_PIPELINE_COUNT_LIMIT = 8

# Make randomization stable for a single MR
random.seed(os.getenv("CI_MERGE_REQUEST"))


def parse_mr_description():
    MR_DESCRIPTION = os.getenv("CI_MERGE_REQUEST_DESCRIPTION")

    DEPLOYMENT_PIPELINE_DEFINITON = os.getenv("DEPLOYMENT_PIPELINE_DEFINITON")
    if DEPLOYMENT_PIPELINE_DEFINITON:
        return DEPLOYMENT_PIPELINE_DEFINITON.split("|")

    if MR_DESCRIPTION is None or os.getenv("CI_PIPELINE_SOURCE") == 'pipeline':
        with open(".gitlab/merge_request_templates/Default.md", 'r') as f:
            MR_DESCRIPTION = f.read()

    if os.getenv("CI_MERGE_REQUEST_DESCRIPTION_IS_TRUNCATED") == "true":
        print(
            "[INFO] MR description is longer than 2700 characters and truncated in CI variable\n[INFO] Retrieving MR description from API",
            file=sys.stderr
        )
        url = f"{os.getenv('CI_API_V4_URL')}/projects/{os.getenv('CI_PROJECT_ID')}/merge_requests/{os.getenv('CI_MERGE_REQUEST_IID')}"
        mr = json.loads(urllib.request.urlopen(url).read())
        MR_DESCRIPTION = mr["description"]

    option1_config_pattern = re.compile(r"-- OPTION 1 DEFINITION START --((?:.|\n|\r\n)*)-- OPTION 1 DEFINITION END --", re.MULTILINE)
    option1_config = option1_config_pattern.findall(MR_DESCRIPTION)
    option2_config_pattern = re.compile(r"-- OPTION 2 DEFINITION START --((?:.|\n|\r\n)*)-- OPTION 2 DEFINITION END --", re.MULTILINE)
    option2_config = option2_config_pattern.findall(MR_DESCRIPTION)

    selected_deployments = []

    if len(option1_config) == 1 and "[x] Enable option 1" in MR_DESCRIPTION:
        selected_deployments_opt1 = []

        selected_infra_providers = re.compile(r"\n\- \[x\] infra provider: ([\w\d\+-]*)").findall(option1_config[0])
        if len(selected_infra_providers) == 0:
            possible_infra_providers = re.compile(r"\n\- \[ \] infra provider: ([\w\d\+-]*)").findall(option1_config[0])
            selected_infra_providers = [random.choice(possible_infra_providers)]

        selected_bootstrap_providers = re.compile(r"\n\- \[x\] bootstrap provider: ([\w\d\+-]*)").findall(option1_config[0])
        if len(selected_bootstrap_providers) == 0:
            possible_bootstrap_providers = re.compile(r"\n\- \[ \] bootstrap provider: ([\w\d\+-]*)").findall(option1_config[0])
            selected_bootstrap_providers = [random.choice(possible_bootstrap_providers)]

        selected_node_os = re.compile(r"\n\- \[x\] node os: ([\w\d\+-]*)").findall(option1_config[0])
        if len(selected_node_os) == 0:
            possible_os = re.compile(r"\n\- \[ \] node os: ([\w\d\+-]*)").findall(option1_config[0])
            selected_node_os = [random.choice(possible_os)]

        selected_artifact_sources = re.compile(r"\n\- \[x\] artifact source: ([\w\d\+-]*)").findall(option1_config[0])
        if len(selected_artifact_sources) == 0:
            possible_artifact_sources = re.compile(r"\n\- \[ \] artifact source: ([\w\d\+-]*)").findall(option1_config[0])
            selected_artifact_sources = [random.choice(possible_artifact_sources)]

        selected_mgmt_ha = re.compile(r"\n\- \[x\] management cluster availability mode: ([\w\d\+-]*)").findall(option1_config[0])
        if len(selected_mgmt_ha) == 0:
            possible_mgmt_ha = re.compile(r"\n\- \[ \] management cluster availability mode: ([\w\d\+-]*)").findall(option1_config[0])
            selected_mgmt_ha = [random.choice(possible_mgmt_ha)]

        selected_wkld_ha = re.compile(r"\n\- \[x\] workload cluster availability mode: ([\w\d\+-]*)").findall(option1_config[0])
        if len(selected_wkld_ha) == 0:
            possible_wkld_ha = re.compile(r"\n\- \[ \] workload cluster availability mode: ([\w\d\+-]*)").findall(option1_config[0])
            selected_wkld_ha = [random.choice(possible_wkld_ha)]

        selected_variant = re.compile(r"\n\- \[x\] deployment variant: ([\w\d\+-]*)").findall(option1_config[0])
        if len(selected_variant) == 0:
            possible_variant = re.compile(r"\n\- \[ \] deployment variant: ([\w\d\+-]*)").findall(option1_config[0])
            selected_variant = [random.choice(possible_variant)]

        selected_scenarios = re.compile(r"\n\- \[x\] scenario: ([\w\d\+-]*)").findall(option1_config[0])
        if len(selected_scenarios) == 0:
            possible_scenarios = re.compile(r"\n\- \[ \] scenario: ([\w\d\+-]*) .*[D|d]efault").findall(option1_config[0])
            selected_scenarios = [random.choice(possible_scenarios)]

        selected_optional_units = re.compile(r"\n\- \[x\] optional unit: ([\w\d\+-]*)").findall(option1_config[0])
        selected_global_options = re.compile(r"\n\- \[x\] global option: ([\w\d\+-]*)").findall(option1_config[0])

        selected_deployment_matrix = set(
            itertools.product(
                selected_infra_providers,
                selected_bootstrap_providers,
                selected_node_os,
                selected_artifact_sources,
                selected_mgmt_ha,
                selected_wkld_ha,
                selected_scenarios,
                selected_variant,
            )
        )
        for d in selected_deployment_matrix:
            infra = d[0]
            bootstrap = d[1]
            node_os = d[2]
            artifact_source = d[3]
            mgmt_ha = d[4]
            wkld_ha = d[5]
            scenario = d[6]
            variant = d[7]

            if infra == "capd":
                selected_global_options += ["skip-tests"]
                mgmt_ha = "mgmt-single-node"
                scenario = "mgmt-only-no-update"

            # Simplify options
            if artifact_source == "git":
                artifact_source = ""  # git is default, no need to add it in job name
            if variant == "none":
                variant = ""  # no need to add it
            if variant == "capo-fip" and infra != "capo":
                variant = ""  # incompatible variant
            if "mgmt-only" in scenario:
                wkld_ha = ""
            if mgmt_ha == "mgmt-single-node" and scenario in ["mgmt-rolling-update", "migration"]:
                print(f"[ERROR] deployment {d}: scenario not compatible with mgmt-single-node", file=sys.stderr)
                continue
            if wkld_ha == "wkld-single-node" and scenario in ["wkld-rolling-update", "migration"]:
                print(f"[ERROR] deployment {d}: scenario not compatible with wkld-single-node", file=sys.stderr)
                continue

            deployment_options = [artifact_source, mgmt_ha, wkld_ha, scenario, variant] + selected_optional_units + selected_global_options
            deployment_options = list(set(deployment_options))  # avoid duplicates

            while "" in deployment_options:
                deployment_options.remove("")

            selected_deployments_opt1.append(f"☁{infra} 🚀{bootstrap} 🎸{node_os} 🛠{','.join(deployment_options)}")
        print(f"Computed deployments (opt 1): {selected_deployments_opt1}", file=sys.stderr)
        selected_deployments += selected_deployments_opt1

    if len(option2_config) == 1 and "[x] Enable option 2" in MR_DESCRIPTION:
        selected_deployments_opt2 = re.compile(r"\n\- \[x\](.*)").findall(option2_config[0])
        print(f"Forced deployments (opt 2): {selected_deployments_opt2}", file=sys.stderr)
        selected_deployments += selected_deployments_opt2

    return selected_deployments


def generate_ci_job_struct(job_names):
    ci_jobs = {}

    for job in job_names:
        allowed_infra = os.getenv("ALLOWED_DEPLOYMENT_INFRA", "capd,capo,capm3-virt")
        infra = re.compile(r"☁([\w\d-]+)").findall(job)
        if len(infra) != 1 or infra[0] not in allowed_infra:
            print(f"[ERROR] deployment {job}: infra not allowed", file=sys.stderr)
            continue

        ci_jobs[job] = {"extends": [".default-deploy-config", f".{infra[0]}"]}

        if "allow-failure" in job or "ci_allow_failure" in os.getenv("CI_MERGE_REQUEST_LABELS", ""):
            ci_jobs[job]["allow_failure"] = True

        if "skip-tests" in job:
            ci_jobs[job].setdefault("variables", {})
            ci_jobs[job]["variables"]["SKIP_TESTS"] = "true"

        if "mgmt-only-no-update" in job:
            ci_jobs[job].setdefault("variables", {})
            ci_jobs[job]["variables"]["UPDATE_MGMT_CLUSTER"] = "false"
            ci_jobs[job]["variables"]["DEPLOY_WORKLOAD_CLUSTER"] = "false"
            ci_jobs[job]["variables"]["UPDATE_WORKLOAD_CLUSTER"] = "false"

        if "mgmt+wkld-no-update" in job:
            ci_jobs[job].setdefault("variables", {})
            ci_jobs[job]["variables"]["UPDATE_MGMT_CLUSTER"] = "false"
            ci_jobs[job]["variables"]["DEPLOY_WORKLOAD_CLUSTER"] = "true"
            ci_jobs[job]["variables"]["UPDATE_WORKLOAD_CLUSTER"] = "false"

        if "mgmt+wkld-simple-update" in job:
            ci_jobs[job].setdefault("variables", {})
            ci_jobs[job]["variables"]["UPDATE_MGMT_CLUSTER"] = "true"
            ci_jobs[job]["variables"]["DEPLOY_WORKLOAD_CLUSTER"] = "true"
            ci_jobs[job]["variables"]["UPDATE_WORKLOAD_CLUSTER"] = "true"
            ci_jobs[job]["variables"]["MGMT_UPDATE_ADDITIONAL_VALUES"] = "${SYLVA_CI_VALUES_FOLDER}/simple-update.yml"
            ci_jobs[job]["variables"]["WC_UPDATE_ADDITIONAL_VALUES"] = "${SYLVA_CI_VALUES_FOLDER}/simple-update.yml"

        if "mgmt-rolling-update" in job:
            ci_jobs[job].setdefault("variables", {})
            ci_jobs[job]["variables"]["UPDATE_MGMT_CLUSTER"] = "true"
            ci_jobs[job]["variables"]["DEPLOY_WORKLOAD_CLUSTER"] = "true"
            ci_jobs[job]["variables"]["UPDATE_WORKLOAD_CLUSTER"] = "false"
            ci_jobs[job]["variables"]["MGMT_UPDATE_ADDITIONAL_VALUES"] = "${SYLVA_CI_VALUES_FOLDER}/dummy-rolling-update-trigger.yml"

        if "wkld-rolling-update" in job:
            ci_jobs[job].setdefault("variables", {})
            ci_jobs[job]["variables"]["UPDATE_MGMT_CLUSTER"] = "false"
            ci_jobs[job]["variables"]["DEPLOY_WORKLOAD_CLUSTER"] = "true"
            ci_jobs[job]["variables"]["UPDATE_WORKLOAD_CLUSTER"] = "true"
            ci_jobs[job]["variables"]["WC_UPDATE_ADDITIONAL_VALUES"] = "${SYLVA_CI_VALUES_FOLDER}/dummy-rolling-update-trigger.yml"

        if "k8s-upgrade" in job:
            ci_jobs[job].setdefault("variables", {})
            ci_jobs[job]["variables"]["UPDATE_MGMT_CLUSTER"] = "false"
            ci_jobs[job]["variables"]["DEPLOY_WORKLOAD_CLUSTER"] = "true"
            ci_jobs[job]["variables"]["UPDATE_WORKLOAD_CLUSTER"] = "true"
            ci_jobs[job]["variables"]["MGMT_WATCH_TIMEOUT_MIN"] = "15"
            ci_jobs[job]["variables"]["APPLY_WC_WATCH_TIMEOUT_MIN"] = "80"
            ci_jobs[job]["variables"]["MGMT_INITIAL_ADDITIONAL_VALUES"] = "${SYLVA_CI_VALUES_FOLDER}/serve-k8s-1.27-image.yml"
            ci_jobs[job]["variables"]["WC_INITIAL_ADDITIONAL_VALUES"] = "${SYLVA_CI_VALUES_FOLDER}/k8s-1.27.yml"
            ci_jobs[job]["variables"]["WC_UPDATE_ADDITIONAL_VALUES"] = "${SYLVA_CI_VALUES_FOLDER}/k8s-1.28.yml"

        if "migration" in job:
            ci_jobs[job].setdefault("variables", {})
            ci_jobs[job]["variables"]["UPDATE_MGMT_CLUSTER"] = "true"
            ci_jobs[job]["variables"]["DEPLOY_WORKLOAD_CLUSTER"] = "true"
            ci_jobs[job]["variables"]["UPDATE_WORKLOAD_CLUSTER"] = "true"
            ci_jobs[job]["variables"]["UPDATE_WORKLOAD_CLUSTER"] = "true"
            ci_jobs[job]["variables"]["MGMT_INITIAL_CI_VALUES_REVISION"] = "stable/1.1.1"
            ci_jobs[job]["variables"]["MGMT_INITIAL_REVISION"] = "1.1.1"
            ci_jobs[job]["variables"]["MGMT_UPDATE_CI_VALUES_REVISION"] = "main"
            ci_jobs[job]["variables"]["MGMT_UPDATE_REVISION"] = "main"
            ci_jobs[job]["variables"]["WC_INITIAL_CI_VALUES_REVISION"] = "stable/1.1.1"
            ci_jobs[job]["variables"]["WC_INITIAL_REVISION"] = "1.1.1"
            ci_jobs[job]["variables"]["WC_UPDATE_CI_VALUES_REVISION"] = "main"
            ci_jobs[job]["variables"]["WC_UPDATE_REVISION"] = "main"

        if "capm3-virt" in job and "single-node" not in job:
            ci_jobs[job].setdefault("variables", {})
            ci_jobs[job]["variables"]["RUNNER_PLAN"] = "m3.large.x86"

    return ci_jobs


def output_yaml_file_from_template(ci_jobs):
    with open(TEMPLATE_FILE) as f:
        output = yaml.load(f, Loader=yaml.loader.SafeLoader)

    output.update(ci_jobs)
    yaml.dump(output, sys.stdout, indent=2)


if __name__ == "__main__":
    selected_deployments = parse_mr_description()
    # print(selected_deployments, file=sys.stderr)

    # Limit number of generated child pipelines
    if len(selected_deployments) > CHILD_PIPELINE_COUNT_LIMIT:
        print(f"[ERROR] Too many deployments combinations (count={len(selected_deployments)})", file=sys.stderr)
        print(f"[ERROR] Deployment list: {selected_deployments}", file=sys.stderr)
        sys.exit(1)

    ci_jobs = generate_ci_job_struct(selected_deployments)
    # yaml.dump(ci_jobs, sys.stderr, indent=2)
    output_yaml_file_from_template(ci_jobs)
