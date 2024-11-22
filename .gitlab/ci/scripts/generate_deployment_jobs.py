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

PREDEFINED_PIPELINES_CONFIG_FILE = f"{BASE_DIR}/.gitlab/ci/configuration/predifined-pipelines-config.yaml"
DEFAULT_MR_DESCRIPTION = f"{BASE_DIR}/.gitlab/merge_request_templates/Default.md"

ALLOWED_INFRA = os.getenv("ALLOWED_DEPLOYMENT_INFRA", "capd,capo,capm3").split(",")
ALLOWED_BOOTSTRAP = os.getenv("ALLOWED_DEPLOYMENT_BOOTSTRAP", "kadm,rke2").split(",")
ALLOWED_OS = os.getenv("ALLOWED_DEPLOYMENT_NODE_OS", "ubuntu,suse").split(",")
ALLOWED_SCENARIOS = os.getenv(
    "ALLOWED_DEPLOYMENT_SCENARIO",
    "simple-update,rolling-update,mgmt-rolling-update,rolling-update,k8s-upgrade,sylva-upgrade,nightly,preview"
).split(",")

# Max number of pipelines to be allowed for a MR
DEPLOY_CHILD_PIPELINE_COUNT_LIMIT = int(os.getenv("DEPLOY_CHILD_PIPELINE_COUNT_LIMIT", "8"))

# Make randomization stable for a single MR
random.seed(os.getenv("CI_MERGE_REQUEST_ID"))


def get_ci_configuration_from_context():

    # CI variable DEPLOYMENT_DESCRIPTION_OVERRIDE can be used to override CI config in any case
    DEPLOYMENT_DESCRIPTION_OVERRIDE = os.getenv("DEPLOYMENT_DESCRIPTION_OVERRIDE")
    if DEPLOYMENT_DESCRIPTION_OVERRIDE:
        requested_deployments = DEPLOYMENT_DESCRIPTION_OVERRIDE.split("|")
        logging.info("Requested deployments flavors found from DEPLOYMENT_DESCRIPTION_OVERRIDE variable")
        logging.info(f"{requested_deployments}")
        return requested_deployments

    # if CI variable DEPLOYMENT_DESCRIPTION is set, refer to config in predefined-pipelines-config.yaml
    if os.getenv("DEPLOYMENT_DESCRIPTION"):
        with open(PREDEFINED_PIPELINES_CONFIG_FILE, "r") as f:
            config = yaml.load(f, Loader=yaml.loader.SafeLoader)
        deployment = os.getenv("DEPLOYMENT_DESCRIPTION")
        if deployment in config:
            configured_deployments = config[deployment]
            logging.info(f"Requested deployments flavors found for {deployment} pipeline")
            logging.info(f"{configured_deployments}")
            return configured_deployments

    # otherwise check MR description
    if os.getenv("CI_MERGE_REQUEST_DESCRIPTION"):
        return get_ci_config_from_mr_desription()

    # anyway get default config
    return get_default_ci_config()


def get_ci_config_from_mr_desription(description="", fallback=True):

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
        logging.info("Unable to find any deployments flavor request in MR description. Applying defaut config")
        return get_default_ci_config()

    logging.error("Unable to find any deployments flavor request")
    sys.exit(1)


def get_default_ci_config():
    with open(DEFAULT_MR_DESCRIPTION, "r") as f:
        default_mr_description = f.read()
    return get_ci_config_from_mr_desription(
        description=default_mr_description, fallback=False
    )


def get_deploy_parameter(deploy_name, emoji_key, as_list=False, can_be_empty=False):
    match = re.compile(emoji_key + r"([\w\d,\.-]+)").findall(deploy_name)
    if len(match) != 1:
        if len(match) == 0 and can_be_empty is False:
            logging.error(f"unable to get {emoji_key} value from {deploy_name}")
            sys.exit(1)
        if len(match) > 1:
            logging.error(f"multiple {emoji_key} values from {deploy_name}")
            sys.exit(1)
    if match:
        if as_list is False:
            return match[0]
        else:
            return match[0].split(",")
    if as_list is True:
        return []


def check_deployments(deployments):
    """
    Draw random variant properties (stable on a MR) and
    enforce various rules on selected deployment in order to limit uncompatibilities
    """
    # Limit number of generated child pipelines
    if len(deployments) > DEPLOY_CHILD_PIPELINE_COUNT_LIMIT:
        logging.error(f"Too many deployments combinations (count={len(deployments)})")
        logging.error(f"Deployment list: {deployments}")
        sys.exit(1)

    for index, deploy_name in enumerate(deployments):

        infra = get_deploy_parameter(deploy_name, "☁")
        bootstrap = get_deploy_parameter(deploy_name, "🚀")
        node_os = get_deploy_parameter(deploy_name, "🐧")
        scenario = get_deploy_parameter(deploy_name, "🎬", can_be_empty=True)
        options = get_deploy_parameter(deploy_name, "🛠", as_list=True, can_be_empty=True)
        initial_options = get_deploy_parameter(deploy_name, "🛠", as_list=False, can_be_empty=True)

        if infra == "random":
            if scenario and scenario not in ["simple-update", "preview"]:
                # capd cannot be chosen for HA required senarios
                infra = random.choice([i for i in ALLOWED_INFRA if i != "capd"])
            else:
                infra = random.choice(ALLOWED_INFRA)
        if infra not in ALLOWED_INFRA:
            logging.error(f"deployment {deploy_name}: infra not allowed")
            sys.exit(1)

        if bootstrap == "random":
            bootstrap = random.choice(ALLOWED_BOOTSTRAP)
        if bootstrap not in ALLOWED_BOOTSTRAP:
            logging.error(f"deployment {deploy_name}: bootstrap provider not allowed")
            sys.exit(1)

        if node_os == "random":
            node_os = random.choice(ALLOWED_OS)
        if node_os not in ALLOWED_OS:
            logging.error(f"deployment {deploy_name}: bootstrap provider not allowed")
            sys.exit(1)

        if scenario:
            if scenario not in ALLOWED_SCENARIOS:
                logging.error(f"deployment {deploy_name}: scenario not allowed")
                sys.exit(1)
            if scenario not in ["simple-update", "preview"]:
                options.append("ha")

        if "oci" in options and "git" in options:
            logging.error(f"deployment {deploy_name}: git and oci options are exclusive")
            sys.exit(1)
        if "oci" not in options and "git" not in options:
            options.append(random.choice(["oci", "git"]))

        deploy_name = deploy_name.replace("☁random", f"☁{infra}")
        deploy_name = deploy_name.replace("🚀random", f"🚀{bootstrap}")
        deploy_name = deploy_name.replace("🐧random", f"🐧{node_os}")
        if "🛠" in deploy_name:
            deploy_name = deploy_name.replace(f"🛠{initial_options}", f"🛠{",".join(options)}")
        else:
            deploy_name = f"{deploy_name} 🛠{",".join(options)}"
        deployments[index] = deploy_name

    logging.info("")
    logging.info("Deployments flavors generated:")
    [logging.info(f"* {d}") for d in deployments]

    return deployments


def generate_ci_job_struct(job_names):
    ci_jobs = {}

    for job in job_names:
        infra = get_deploy_parameter(job, "☁")

        ci_jobs[job] = {"extends": [f".{infra}"]}

        if "skip-tests" in job:
            ci_jobs[job].setdefault("variables", {})
            ci_jobs[job]["variables"]["SKIP_TESTS"] = "true"

        scenario = get_deploy_parameter(job, "🎬", can_be_empty=True)
        if scenario:
            ci_jobs[job]["extends"].append(f".scenario_{scenario}")

            # Special temporary exception for capm3 sylva-upgrade
            if scenario == "sylva-upgrade" and infra in ["capm3", "capm3-virt"]:
                ci_jobs[job]["extends"].append(".scenario_sylva-upgrade-capm3")

        options = get_deploy_parameter(job, "🛠", as_list=True, can_be_empty=True)
        if "oci" in options:
            ci_jobs[job]["extends"].append(".wait-publish-jobs")

        if infra == "capm3" and "single-node" not in options:
            ci_jobs[job].setdefault("variables", {})
            ci_jobs[job]["variables"]["EQUINIX_RUNNER_PLAN"] = "m3.large.x86"

        # For human triggered pipelines, make deployment jobs triggerable individually
        if os.getenv("CI_PIPELINE_SOURCE") in ["pipeline", "web", "merge_request_event", "push"] \
            and "renovate" not in os.getenv("CI_MERGE_REQUEST_LABELS", "") \
                and scenario != "preview":
            ci_jobs[job]["when"] = "manual"

        if ("allow-failure" in job
           or "ci-allow-failure" in os.getenv("CI_MERGE_REQUEST_LABELS", "")):
            ci_jobs[job]["allow_failure"] = True
        else:
            ci_jobs[job]["allow_failure"] = False

    return ci_jobs


def output_yaml_file_from_template(ci_jobs):
    with open(TEMPLATE_FILE, "r") as f:
        output = yaml.load(f, Loader=yaml.loader.SafeLoader)
    output.update(ci_jobs)
    yaml.dump(output, sys.stdout, indent=2, allow_unicode=True)


if __name__ == "__main__":
    selected_deployments = check_deployments(get_ci_configuration_from_context())
    ci_jobs = generate_ci_job_struct(selected_deployments)
    output_yaml_file_from_template(ci_jobs)
