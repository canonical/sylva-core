#!/usr/bin/env python

import json
import logging
import os
import random
import re
import sys
import urllib.request
import yaml

"""
This script is used in CI for generating list of deployment jobs
"""

logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.INFO)

SCRIPT_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
BASE_DIR = os.path.abspath(f"{SCRIPT_DIR}/../../..")
TEMPLATE_FILE = os.path.abspath(f"{BASE_DIR}/.gitlab/ci/deployments-base.yml")

PREDEFINED_PIPELINES_CONFIG_FILE = f"{BASE_DIR}/.gitlab/ci/configuration/predefined-pipelines-config.yaml"
DEFAULT_MR_DESCRIPTION = f"{BASE_DIR}/.gitlab/merge_request_templates/Default.md"

ALLOWED_INFRA = os.getenv("ALLOWED_DEPLOYMENT_INFRA", "capd,capo,capm3")
ALLOWED_SCENARIOS = os.getenv(
    "ALLOWED_DEPLOYMENT_SCENARIO",
    "simple-update,rolling-update,mgmt-rolling-update,k8s-upgrade,sylva-upgrade,sylva-upgrade-from-1.1.1,nightly,preview"
)

# Max number of pipelines to be allowed for a MR
DEPLOY_CHILD_PIPELINE_COUNT_LIMIT = int(os.getenv("DEPLOY_CHILD_PIPELINE_COUNT_LIMIT", "9"))

# Make randomization stable for a single MR
random.seed(os.getenv("CI_MERGE_REQUEST"))


def get_ci_configuration_from_context():

    # CI variable DEPLOYMENT_DESCRIPTION_OVERRIDE can be used to override CI config in any case
    DEPLOYMENT_DESCRIPTION_OVERRIDE = os.getenv("DEPLOYMENT_DESCRIPTION_OVERRIDE")
    if DEPLOYMENT_DESCRIPTION_OVERRIDE:
        requested_deployments = DEPLOYMENT_DESCRIPTION_OVERRIDE.split("|")
        logging.info("Requested deployment flavors found from DEPLOYMENT_DESCRIPTION_OVERRIDE variable")
        logging.info(f"{requested_deployments}")
        return requested_deployments

    # if CI variable DEPLOYMENT_DESCRIPTION is set, refer to config in predefined-pipelines-config.yaml
    if os.getenv("DEPLOYMENT_DESCRIPTION"):
        requested_deployment_config = os.getenv("DEPLOYMENT_DESCRIPTION")
        retrieved_config = get_predefined_ci_config(requested_deployment_config)
        if not retrieved_config:
            logging.error(f"Unable to find deployment flavors for {requested_deployment_config}")
            sys.exit(1)
        logging.info(f"Requested deployment flavors found for {requested_deployment_config} pipeline")
        logging.info(f"{retrieved_config}")
        return retrieved_config

    # if renovate label is set use predefined config
    if "renovate" in os.getenv("CI_MERGE_REQUEST_LABELS", "").split(","):
        if "capo" in os.getenv("CI_MERGE_REQUEST_LABELS", "").split(","):
            retrieved_config = get_predefined_ci_config("Renovate Capo")
        else:
            retrieved_config = get_predefined_ci_config("Renovate")
        if not retrieved_config:
            logging.error("Unable to find deployment flavors for renovate")
            sys.exit(1)
        logging.info("Requested deployment flavors found for renovate pipeline")
        logging.info(f"{retrieved_config}")
        return retrieved_config

    # otherwise check MR description
    if os.getenv("CI_MERGE_REQUEST_DESCRIPTION"):
        return get_ci_config_from_mr_description()

    # anyway get default config
    return get_default_ci_config()


def get_ci_config_from_mr_description(description="", fallback=True):

    MR_DESCRIPTION = description
    if not MR_DESCRIPTION and os.getenv("CI_MERGE_REQUEST_DESCRIPTION"):
        MR_DESCRIPTION = os.getenv("CI_MERGE_REQUEST_DESCRIPTION")
        if os.getenv("CI_MERGE_REQUEST_DESCRIPTION_IS_TRUNCATED") == "true":
            logging.info("MR description is longer than 2700 characters and truncated in CI variable")
            logging.info("Retrieving MR description from API")
            url = f"{os.getenv('CI_API_V4_URL')}/projects/{os.getenv('CI_PROJECT_ID')}/merge_requests/{os.getenv('CI_MERGE_REQUEST_IID')}"
            mr = json.loads(urllib.request.urlopen(url).read())
            MR_DESCRIPTION = mr["description"]

    config_pattern = re.compile(
        r"-- DEPLOYMENT FLAVOR DEFINITION START --((?:.|\n|\r\n)*)-- DEPLOYMENT FLAVOR DEFINITION END --",
        re.MULTILINE,
    )
    config = config_pattern.findall(MR_DESCRIPTION)

    if config:
        selected_deployments = re.compile(r"\n\* \[x\] (.*)").findall(config[0])
        if selected_deployments:
            logging.info("Requested deployments flavors found:")
            [logging.info(f"* {d}") for d in selected_deployments]
            return [s.strip() for s in selected_deployments]

    if fallback:
        logging.info("Unable to find any deployment flavor request in MR description. Applying defaut config")
        return get_default_ci_config()

    return []


def get_predefined_ci_config(config_name):
    with open(PREDEFINED_PIPELINES_CONFIG_FILE, "r") as f:
        config = yaml.load(f, Loader=yaml.loader.SafeLoader)
    if config_name in config:
        configured_deployments = config[config_name]
        return configured_deployments


def get_default_ci_config():
    with open(DEFAULT_MR_DESCRIPTION, "r") as f:
        default_mr_description = f.read()
    return get_ci_config_from_mr_description(
        description=default_mr_description, fallback=False
    )


def generate_ci_job_struct(job_names):
    ci_jobs = {}

    for job in job_names:
        infra = re.compile(r"☁([\w\d-]+)").findall(job)
        if len(infra) != 1 or infra[0] not in ALLOWED_INFRA.split(","):
            logging.error(f"deployment {job}: infra not allowed")
            sys.exit(1)
        ci_jobs[job] = {"extends": [f".{infra[0]}"]}

        if "skip-tests" in job:
            ci_jobs[job].setdefault("variables", {})
            ci_jobs[job]["variables"]["SKIP_TESTS"] = "true"

        scenario = re.compile(r"🎬([\w\d\.-]+)").findall(job)
        if scenario:
            if scenario[0] in ALLOWED_SCENARIOS.split(","):
                ci_jobs[job]["extends"].append(f".scenario_{scenario[0]}")

                # Special temporary exception for capm3 sylva-upgrade from 1.1.1
                if scenario[0] == "sylva-upgrade-from-1.1.1" and infra[0] in ["capm3", "capm3-virt"]:
                    ci_jobs[job]["extends"].append(".scenario_sylva-upgrade-capm3-from-1.1.1")

            else:
                logging.error(f"deployment {job}: scenario not allowed")
                sys.exit(1)

        options = []
        option_match = re.compile(r"🛠([\w\d,-]+)").findall(job)
        if option_match:
            options = option_match[0].split(",")

        if "oci" in options:
            ci_jobs[job]["extends"].append(".wait-publish-jobs")

        if infra[0] == "capm3" and "single-node" not in options:
            ci_jobs[job].setdefault("variables", {})
            ci_jobs[job]["variables"]["EQUINIX_RUNNER_PLAN"] = "m3.large.x86"

        # For human triggered pipelines, make deployment jobs triggerable individually
        if os.getenv("CI_PIPELINE_SOURCE") in ["pipeline", "web", "merge_request_event", "push"] \
            and "renovate" not in os.getenv("CI_MERGE_REQUEST_LABELS", "").split(",") \
                and (not scenario or scenario[0] != "preview"):
            ci_jobs[job]["allow_failure"] = True
            ci_jobs[job]["when"] = "manual"

        if ("allow-failure" in job
           or "ci-allow-failure" in os.getenv("CI_MERGE_REQUEST_LABELS", "")):
            ci_jobs[job]["allow_failure"] = True

    return ci_jobs


def output_yaml_file_from_template(ci_jobs):
    with open(TEMPLATE_FILE, "r") as f:
        output = yaml.load(f, Loader=yaml.loader.SafeLoader)

    output.update(ci_jobs)
    yaml.dump(output, sys.stdout, indent=2, allow_unicode=True)


if __name__ == "__main__":
    selected_deployments = get_ci_configuration_from_context()

    # Limit number of generated child pipelines
    if len(selected_deployments) > DEPLOY_CHILD_PIPELINE_COUNT_LIMIT:
        logging.error(f"Too many deployments combinations (count={len(selected_deployments)})")
        logging.error(f"Deployment list: {selected_deployments}")
        sys.exit(1)

    ci_jobs = generate_ci_job_struct(selected_deployments)
    output_yaml_file_from_template(ci_jobs)
