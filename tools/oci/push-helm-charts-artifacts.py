#!/usr/bin/env python3
#
# This script will push helm charts used in sylva to registry.gitlab.com
# as OCI registry artifacts.
#
#
# If run manually, the tool can be used after having preliminarily done
# a 'docker login registry.gitlab.com' with suitable credentials.
#
# To enable signing when running manually, export the environment variables:
# - COSIGN_PASSWORD
# - COSIGN_PRIVATE_KEY (in PEM format)
#
# Cosign default signing material is available on sylva project gitlab://43786055
#
# Requirements:
# - helm
# - git
# - cosign
import atexit
import os
import re
import subprocess
import shutil
import yaml
import logging
import sys
import time

# pylama:ignore=W0401
from artifact_utils import *


class ExitHandler(logging.StreamHandler):
    def emit(self, record):
        if record.levelno in (logging.ERROR, logging.CRITICAL):
            sys.exit(1)


logger = logging.getLogger()
eh = ExitHandler()
logger.addHandler(eh)
section_logger = logging.getLogger('section_logger')
section_handler = logging.StreamHandler()
section_handler.setFormatter(logging.Formatter('%(message)s'))
section_logger.addHandler(section_handler)
section_logger.setLevel(logging.INFO)
section_logger.propagate = False

start = time.time()

BASE_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), '../..'))
VALUES_FILE = os.path.join(BASE_DIR, 'charts/sylva-units/values.yaml')


def start_section(unit_name):
    timestamp = int(time.time())
    section_logger.info(f"\033[1m\033[0Ksection_start:{timestamp}:section_{unit_name}[collapsed=true]\r\033[0K--- processing unit {unit_name}\033[0m")


def end_section(unit_name):
    timestamp = int(time.time())
    section_logger.info(f"\033[0Ksection_end:{timestamp}:section_{unit_name}\r\033[0K")


def check_invalid_semver_tag(chart_name, version, rewrite_chart=False):
    if re.search(r"\.0[0-9]", version):
        # Implement a workaround for issue: https://gitlab.com/sylva-projects/sylva-core/-/issues/253
        # If we find a version with a 0 prefix
        # rewrite the version by (a) prepeding a number before the z in x.y.z (for instance 9)
        # and (b) keeping the original version in the free-form + field
        # 3.25.001 would become 3.25.9001+v3.25.001
        if re.search(r"(.?[0-9]+)\.([0-9]+)\.([0-9]+)([\+\-].*)?", version):
            parts = version.split(".")
            parts[2] = '9' + parts[2]
            new_version = ".".join(parts) + '+' + version
            if rewrite_chart:
                logger.info("rewriting version in Chart.yaml")
                tgz_file = f"{chart_name}-{version}.tgz"
                run_command(f"tar -xzf {tgz_file}", cwd=ARTIFACT_DIR)
                with open(f"{ARTIFACT_DIR}/{chart_name}/Chart.yaml", 'r+') as f:
                    chart = yaml.safe_load(f)
                    chart['version'] = new_version
                    f.seek(0)
                    yaml.safe_dump(chart, f)
                    f.truncate()
                run_command(f"tar -czf {chart_name}-{new_version}.tgz {chart_name}/",
                            cwd=ARTIFACT_DIR)
                shutil.rmtree(f"{ARTIFACT_DIR}/{chart_name}")
                os.remove(f"{ARTIFACT_DIR}/{tgz_file}")
            return new_version
    return version


def process_chart_in_helm_repo(helm_repo, chart_name, chart_version, artifact_name, version_to_check):
    try:
        is_oci = helm_repo.startswith('oci://')
        # Build pull command based on repo type
        if is_oci:
            pull_cmd = f"helm pull {helm_repo}/{chart_name} --version {chart_version}"
        else:
            pull_cmd = f"helm pull --repo {helm_repo} --version {chart_version} {chart_name}"
        run_command(f"{pull_cmd} -d {ARTIFACT_DIR}", cwd=ARTIFACT_DIR)
    except subprocess.CalledProcessError:
        logging.error(f"The chart {chart_name}:{chart_version} from {helm_repo} can't be pulled locally.")

    tgz_file = f"{ARTIFACT_DIR}/{chart_name}-{chart_version}.tgz"
    if os.path.exists(tgz_file):
        chart_version = check_invalid_semver_tag(artifact_name, chart_version, rewrite_chart=True)
        tgz_file = f"{ARTIFACT_DIR}/{chart_name}-{chart_version}.tgz"
        if artifact_name != chart_name:
            new_tgz_file = f"{ARTIFACT_DIR}/{artifact_name}-{chart_version}.tgz"
            run_command(f"tar -xzvf {tgz_file}", cwd=ARTIFACT_DIR)
            with open(f"{ARTIFACT_DIR}/{chart_name}/Chart.yaml", 'r+') as f:
                chart = yaml.safe_load(f)
                chart['name'] = artifact_name
                f.seek(0)
                yaml.safe_dump(chart, f)
                f.truncate()
            run_command(f"tar -czvf {new_tgz_file} {chart_name}/",
                        cwd=ARTIFACT_DIR)
            shutil.rmtree(f"{ARTIFACT_DIR}/{chart_name}")
            os.remove(tgz_file)
            tgz_file = new_tgz_file

        process_artifact_helm(artifact_name, version_to_check, tgz_file)

    else:
        logging.error(f"The {tgz_file} file was expected but wasn't found")
        run_command(f"ls -l {ARTIFACT_DIR}")


def process_chart_in_git(repo, chart_path, chart_name):

    chart_version = chart_version_from_repo(repo)

    git_repo_url = repo['spec']['url']

    if 'branch' in repo['spec']['ref']:
        git_revision = repo['spec']['ref']['branch']

    if 'tag' in repo['spec']['ref']:
        git_revision = repo['spec']['ref']['tag']

    if not git_revision:
        raise Exception(f"git revision could not be identified from <repo>.spec.ref ({repo['spec']['ref']})")

    tgz_file = f"{ARTIFACT_DIR}/{chart_name}-{chart_version}.tgz"
    try:
        run_command(f"git clone -c advice.detachedHead=false -q --depth 1 --branch {git_revision} {git_repo_url} {ARTIFACT_DIR}")
    except subprocess.CalledProcessError:
        logger.error(f"The git repository {git_repo_url} revision {git_revision} can't be cloned.")

    do_helm_dep_update = True
    if os.path.exists(f"{ARTIFACT_DIR}/{chart_path}/Chart.lock"):
        logger.info("Chart.lock exists, trying 'helm build dependencies'")
        try:
            run_command(f"helm dep build --skip-refresh {ARTIFACT_DIR}/{chart_path}",
                        cwd=ARTIFACT_DIR)
            do_helm_dep_update = False
        except Exception as e:
            logger.info(f"'helm dep build' failed ({e}), but maybe 'helm dep update' will work")

    if do_helm_dep_update:
        run_command(f"helm dep update {ARTIFACT_DIR}/{chart_path}",
                    cwd=ARTIFACT_DIR)

    with open(f"{ARTIFACT_DIR}/{chart_path}/Chart.yaml", 'r+') as f:
        chart = yaml.safe_load(f)
        chart['name'] = chart_name
        f.seek(0)
        yaml.safe_dump(chart, f)
        f.truncate()
    run_command(f"helm package --version {chart_version} {ARTIFACT_DIR}/{chart_path}"
                f" -d {ARTIFACT_DIR}")
    if os.path.exists(tgz_file):
        process_artifact_helm(chart_name, chart_version, tgz_file)
    else:
        error_message = f"The {tgz_file} is not present after the 'helm package' " \
            f"operation, check that the chart version is correct."
        logging.error(error_message)


atexit.register(cleanup)

with open(VALUES_FILE, 'r') as f:
    values = yaml.safe_load(f)
source_templates = values.get('source_templates', [])
units = values.get('units', {})

for unit_name in sorted(units.keys()):
    unit = units[unit_name]
    helmchart_spec = unit.get('helmrelease_spec', {}).get('chart', {}).get('spec')
    if helmchart_spec:
        start_section(unit_name)
        chart = helmchart_spec.get('chart')
        if "sylva-units" in chart:
            logger.info("skipping sylva-units chart")
            end_section(unit_name)
            continue
        helm_repo_url = unit.get('helm_repo_url')
        if helm_repo_url:
            artifact_name = unit.get('helm_chart_artifact_name', helmchart_spec['chart'])
            versions = unit.get('helm_chart_versions', [])
            if not versions:
                versions.append(helmchart_spec['version'])
            for version in versions:
                logger.info(f"- processing version {version} from sylva-units values")
                version_to_check = check_invalid_semver_tag(artifact_name, version, False)
                process_chart_in_helm_repo(
                    helm_repo_url, chart, version, artifact_name, version_to_check.replace('+', '_')
                )
            end_section(unit_name)
        else:
            chart_name = unit.get('helm_chart_artifact_name', chart.split('/')[-1])
            repo = unit.get('repo')
            process_chart_in_git(source_templates[repo], chart, chart_name)
            end_section(unit_name)
    delete_temp_files()

logger.info(f"All Helm charts have been correctly synchronized to {OCI_REGISTRY}")
end = time.time()
hours, rem = divmod(end - start, 3600)
minutes, seconds = divmod(rem, 60)
logger.info("{:0>2} minutes and {:05.2f} seconds elapsed.".format(int(minutes), seconds))
