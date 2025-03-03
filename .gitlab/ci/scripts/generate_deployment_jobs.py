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

ALLOWED_INFRA = os.getenv("ALLOWED_DEPLOYMENT_INFRA", "capd,capo,capm3").split(",")
ALLOWED_BOOTSTRAP = os.getenv("ALLOWED_DEPLOYMENT_BOOTSTRAP", "kadm,rke2").split(",")
ALLOWED_OS = os.getenv("ALLOWED_DEPLOYMENT_NODE_OS", "ubuntu,suse").split(",")
ALLOWED_SCENARIOS = os.getenv(
    "ALLOWED_DEPLOYMENT_SCENARIO",
    ",".join([
        "no-wkld",
        "simple-update",
        "simple-update-no-wkld",
        "rolling-update",
        "rolling-update-no-wkld",
        "preview",
        "nightly",
        "wkld-k8s-upgrade",
        "sylva-upgrade",
        "sylva-upgrade-no-wkld",
        "sylva-upgrade-from-1.1.1",
        "sylva-upgrade-from-1.2.1",
        "sylva-upgrade-from-1.3.x",
    ])
).split(",")

# Max number of pipelines to be allowed for a MR
DEPLOY_CHILD_PIPELINE_COUNT_LIMIT = int(os.getenv("DEPLOY_CHILD_PIPELINE_COUNT_LIMIT", "9"))

# Make randomization stable for a single MR
random.seed(os.getenv("CI_MERGE_REQUEST"))


def get_ci_configuration_from_context():

    global_options = {
        "autorun": True,
        "allow-failure": False,
        "record-sylvactl-events": False,
    }

    # CI variable DEPLOYMENT_DESCRIPTION_OVERRIDE can be used to override CI config in any case
    DEPLOYMENT_DESCRIPTION_OVERRIDE = os.getenv("DEPLOYMENT_DESCRIPTION_OVERRIDE")
    if DEPLOYMENT_DESCRIPTION_OVERRIDE:
        requested_deployments = DEPLOYMENT_DESCRIPTION_OVERRIDE.split("|")
        logging.info("Requested deployment flavors found from DEPLOYMENT_DESCRIPTION_OVERRIDE variable")
        logging.info(f"{requested_deployments}")
        return requested_deployments, global_options

    # if CI variable DEPLOYMENT_DESCRIPTION is set, refer to config in predefined-pipelines-config.yaml
    if os.getenv("DEPLOYMENT_DESCRIPTION"):
        requested_deployment_config = os.getenv("DEPLOYMENT_DESCRIPTION")
        retrieved_config = get_predefined_ci_config(requested_deployment_config)
        if not retrieved_config:
            logging.error(f"Unable to find deployment flavors for {requested_deployment_config}")
            sys.exit(1)
        logging.info(f"Requested deployment flavors found for {requested_deployment_config} pipeline")
        logging.info(f"{retrieved_config}")
        return retrieved_config, global_options

    # attempt to use CI config from MR description
    if os.getenv("CI_MERGE_REQUEST_DESCRIPTION"):
        ci_config, mr_options = get_ci_config_from_mr_description()
        if ci_config:
            return ci_config, mr_options
        else:
            logging.info("Unable to find any deployment flavor request in MR description.")

    # otherwise, if renovate label is set use predefined config
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
        return retrieved_config, global_options

    # as fallback, get default config
    logging.info("Applying defaut deployment pipeline config")
    return get_default_ci_config()


def get_ci_config_from_mr_description(description=""):

    global_options = {
        "autorun": False,
        "allow-failure": True,
        "record-sylvactl-events": False,
    }

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

    # Global options parsing
    autorun_option_pattern = re.compile(r"\* \[(.)\] .*-- AUTORUN  OPTION --")
    autorun_option = autorun_option_pattern.findall(MR_DESCRIPTION)
    if autorun_option:
        global_options["autorun"] = autorun_option[0] == "x"
    allowfailure_option_pattern = re.compile(r"\* \[(.)\] .*-- ALLOW FAILURE OPTION --")
    allowfailure_option = allowfailure_option_pattern.findall(MR_DESCRIPTION)
    if allowfailure_option:
        global_options["allow-failure"] = allowfailure_option[0] == "x"
    sylvactl_record_option_pattern = re.compile(r"\* \[(.)\] .*-- SYLVACTL RECORD OPTION --")
    sylvactl_record_option = sylvactl_record_option_pattern.findall(MR_DESCRIPTION)
    if sylvactl_record_option:
        global_options["record-sylvactl-events"] = sylvactl_record_option[0] == "x"

    if config:
        selected_deployments = re.compile(r"\n\* \[x\] (.*)").findall(config[0])
        if selected_deployments:
            logging.info("Requested deployments flavors found:")
            [logging.info(f"* {d}") for d in selected_deployments]
            logging.info(f"Global pipeline options: {global_options}")
            return [s.strip() for s in selected_deployments], global_options

    return [], global_options


def get_predefined_ci_config(config_name):
    with open(PREDEFINED_PIPELINES_CONFIG_FILE, "r") as f:
        config = yaml.load(f, Loader=yaml.loader.SafeLoader)
    if config_name in config:
        configured_deployments = config[config_name]
        return configured_deployments


def get_default_ci_config():
    logging.info(f"Getting CI config from default ({DEFAULT_MR_DESCRIPTION})")
    with open(DEFAULT_MR_DESCRIPTION, "r") as f:
        default_mr_description = f.read()
    return get_ci_config_from_mr_description(
        description=default_mr_description
    )


def get_deploy_parameter(deploy_name, emoji_key, as_list=False, can_be_empty=False):
    """
    Extract value for a key (emoji) for a deployment variant
    """
    match = re.compile(emoji_key + r"\s?([\w\d,\.-]+)").findall(deploy_name)
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
    return ""


def check_deployments(deployments):
    """
    Enforce various rules on selected deployment in order to limit uncompatibilities
    """
    # Limit number of generated child pipelines
    if len(deployments) > DEPLOY_CHILD_PIPELINE_COUNT_LIMIT:
        logging.error(f"Too many deployments combinations ({len(deployments)} > {DEPLOY_CHILD_PIPELINE_COUNT_LIMIT})")
        logging.error(f"Deployment list: {deployments}")
        sys.exit(1)

    generated_deployments = []

    for index, deploy_name in enumerate(deployments):

        infra = get_deploy_parameter(deploy_name, "☁")
        bootstrap = get_deploy_parameter(deploy_name, "🚀")
        node_os = get_deploy_parameter(deploy_name, "🐧")
        scenario = get_deploy_parameter(deploy_name, "🎬", can_be_empty=True)
        options = get_deploy_parameter(deploy_name, "🛠", as_list=True, can_be_empty=True)

        if infra not in ALLOWED_INFRA:
            logging.error(f"deployment {deploy_name}: infra not allowed")
            sys.exit(1)

        if bootstrap not in ALLOWED_BOOTSTRAP:
            logging.error(f"deployment {deploy_name}: bootstrap provider not allowed")
            sys.exit(1)

        if node_os not in ALLOWED_OS:
            logging.error(f"deployment {deploy_name}: node OS not allowed")
            sys.exit(1)

        if scenario and scenario not in ALLOWED_SCENARIOS:
            logging.error(f"deployment {deploy_name}: scenario not allowed")
            sys.exit(1)

        if scenario and scenario not in ["simple-update", "preview"] and "ha" not in options:
            options.append("ha")

        generated_deploy_name = f"☁{infra} 🚀{bootstrap}"
        if scenario:
            if scenario == "preview":
                generated_deploy_name = f"🎬preview {generated_deploy_name}"
            else:
                generated_deploy_name = f"{generated_deploy_name} 🎬{scenario}"
        if options:
            generated_deploy_name = f"{generated_deploy_name} 🛠{','.join(sorted(options))}"
        generated_deploy_name = f"{generated_deploy_name} 🐧{node_os}"

        generated_deployments.append(generated_deploy_name)

    logging.info("")
    logging.info("Deployments flavors generated:")
    [logging.info(f"* {d}") for d in generated_deployments]

    return generated_deployments


def generate_ci_job_struct(job_names, global_options):
    ci_jobs = {}

    for job in job_names:
        ci_jobs[job] = {}
        infra = get_deploy_parameter(job, "☁")
        bootstrap = get_deploy_parameter(job, "🚀")
        node_os = get_deploy_parameter(job, "🐧")
        scenario = get_deploy_parameter(job, "🎬", can_be_empty=True)
        options = get_deploy_parameter(job, "🛠", as_list=True, can_be_empty=True)

        # inject deployment parameters as pipeline variables
        ci_jobs[job]["variables"] = {
            "DEPLOYMENT_INFRA_PROV": infra,
            "DEPLOYMENT_BOOTSTRAP_PROV": bootstrap,
            "DEPLOYMENT_OS": node_os,
            "DEPLOYMENT_SCENARIO": scenario,
            "DEPLOYMENT_OPTIONS": ",".join(options),
        }

        ci_jobs[job]["extends"] = [f".{infra}"]

        if scenario:
            ci_jobs[job]["extends"].append(f".scenario_{scenario}")

            # Special temporary exception for capm3 sylva-upgrade
            if scenario == "sylva-upgrade-from-1.1.1" and infra in ["capm3", "capm3-virt"]:
                ci_jobs[job]["extends"].append(".scenario_sylva-upgrade-capm3-from-1.1.1")

        if "dev-sources" not in options:
            ci_jobs[job]["extends"].append(".wait-publish-jobs")

        if infra in ["capm3", "capm3-virt"] and "ha" in options:
            ci_jobs[job]["variables"]["EQUINIX_RUNNER_PLAN"] = "m3.large.x86"

        if "skip-tests" in options:
            ci_jobs[job]["variables"]["SKIP_TESTS"] = "true"

        # Handle global options
        ci_jobs[job]["allow_failure"] = global_options["allow-failure"]
        if (not scenario or scenario != "preview") and global_options["autorun"] is False:
            ci_jobs[job]["when"] = "manual"
        if global_options["record-sylvactl-events"]:
            ci_jobs[job]["variables"]["SYLVACTL_RECORD"] = "true"

    return ci_jobs


def output_yaml_file_from_template(ci_jobs):
    with open(TEMPLATE_FILE, "r") as f:
        output = yaml.load(f, Loader=yaml.loader.SafeLoader)

    output.update(ci_jobs)
    yaml.dump(output, sys.stdout, indent=2, allow_unicode=True)


if __name__ == "__main__":
    requested_deployments, global_options = get_ci_configuration_from_context()
    selected_deployments = check_deployments(requested_deployments)
    ci_jobs = generate_ci_job_struct(selected_deployments, global_options)
    output_yaml_file_from_template(ci_jobs)
