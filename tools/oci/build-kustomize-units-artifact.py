#!/usr/bin/env python3
#
# This script will push to registry.gitlab.com an OCI registry artifact
# containing the 'kustomize-units'.
#
# The artifact is pushed as:
#  oci://registry.gitlab.com/sylva-projects/sylva-core/kustomize-units:<tag>
#
# The pushed artifact will contain a values override file, 'use-oci-registry.values.yaml'
# that can be used to override all external sources definitions (from source_templates and helm_repo_url)
# to make them points to OCI Registry artifacts.
#
#
# ### How to use ###
#
# The script accepts an optional parameter, ARTIFACT_VERSION which will be used as <tag> above if set as env var.
# By default the current commit id will be used as <tag>.
#
# If run manually, the tool can be used after having preliminarily done
# a 'docker login registry.gitlab.com' with suitable credentials.
import os
import re
import subprocess
import shutil
import yaml
import atexit
import logging
import sys
# pylama:ignore=W0401
from artifact_utils import *

BASE_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), '../..'))
logger = logging.getLogger()


def find_kustomization_files(base_dir):
    kustomization_files = []
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if re.match(r'kustomization\.ya?ml$', file):
                kustomization_files.append(os.path.join(root, file))
    return sorted(kustomization_files)


# processes a kustomization.yaml (given as parameter):
# - make a copy of the kustomization, keeping only 'resources'
# - render the kustomization with 'kustomize build'
# - replaces 'resources' in the original kustomization by the
#   result of the rendering
def process_kustomization(kustomization):
    logger.info(f"  process kustomization: {kustomization}...")
    kdir = os.path.dirname(kustomization)
    orig_kustomization = f"{kustomization}.orig"
    shutil.move(kustomization, orig_kustomization)

    with open(orig_kustomization) as orig_file:
        data = yaml.safe_load(orig_file)

    with open(kustomization, 'w') as new_file:
        yaml.dump({
            'apiVersion': data['apiVersion'],
            'kind': data['kind'],
            'resources': data['resources']
        }, new_file)

    logger.info("  locally rendering remote resources...")
    kustomize_result = run_command(["kustomize", "build", kdir,
                                    "-o", f"{kdir}/local-resources.yaml"],
                                   check=False)

    if kustomize_result.returncode != 0:
        logger.error(f"Unable to flatten {kustomization} !")
        sys.exit(1)

    logger.info("  OK")

    shutil.move(orig_kustomization, kustomization)

    with open(kustomization) as file:
        data = yaml.safe_load(file)
    data['resources'] = ["local-resources.yaml"]
    with open(kustomization, 'w') as file:
        yaml.dump(data, file)


paths = ArtifactPaths()
artifact_name = "kustomize-units"

if os.getenv('CI_REPOSITORY_URL'):
    artifact_source = re.sub('gitlab-ci-token.*@', '', os.getenv('CI_REPOSITORY_URL'))
else:
    artifact_source = run_command(["git", "config", "--get", "remote.origin.url"]).stdout

artifact_branch = run_command(['git', 'branch', '--show-current']).stdout

artifact_tag = run_command(['git', 'rev-parse', '--short=8', 'HEAD']).stdout

artifact_revision = artifact_branch + "/" + artifact_tag

artifact_version = os.getenv('ARTIFACT_VERSION', f"0.0.0-git-{artifact_tag}")
logger.info(f'artifact_version: {artifact_version}')


shutil.copytree(os.path.join(BASE_DIR, 'kustomize-units'), os.path.join(paths.artifact_dir, 'kustomize-units'),
                dirs_exist_ok=True)

os.chdir(paths.artifact_dir)

kustomizations = find_kustomization_files(paths.artifact_dir)

for kustomization in kustomizations:
    with open(kustomization) as kustomization_file:
        data = yaml.safe_load(kustomization_file)
    if 'resources' in data.keys()\
            and any('http://' in r or 'https://' in r or 'ssh://' in r for r in data['resources']):
        logger.info(f"* {os.path.dirname(kustomization)}, processing ...")
        process_kustomization(kustomization)
    else:
        logger.info(f"* {os.path.dirname(kustomization)}: no remote resource, skipping")

try:
    run_command(["find", ".", "-type", "f", "-name", "'kustomization.y*ml'", "-exec", "grep",
                 "-nsE", "--", "'- +(https?|ssh)://'", "{}", "+"])
except subprocess.CalledProcessError:
    logger.error("There are remaining remote URLs in some kustomization!")

atexit.register(cleanup, paths)


artifact_url = f"{OCI_REGISTRY}/{artifact_name}:{artifact_version}"
if artifact_exists_with_flux(artifact_name, artifact_version, artifact_url, paths):

    fail_if_existing_artifact_differs(artifact_name, artifact_version, artifact_url, paths)

    # artifact content hasn't changed, but we may want to sign it
    if 'COSIGN_PUBLIC_KEY' in os.environ:
        logger.info(f"Check if artifact {artifact_url} is signed with the correct key")

        try:
            signature_is_valid(artifact_name)
            logger.info(f"Artifact {artifact_url} exists and is already signed with the correct key")
        except ValueError:
            logger.info(f"Artifact {artifact_url} exists and needs to be signed")
            sign(artifact_name, ARTIFACT_DIGEST)
    else:
        logger.warning("Unable to sign the kustomize-units, signing material is not set")
else:
    push_and_sign_with_flux(artifact_name, artifact_version, artifact_source, artifact_revision)
