import os
import subprocess
import tempfile
import shutil
import re
import logging
from pathlib import Path

OCI_REGISTRY = os.getenv("OCI_REGISTRY", "oci://registry.gitlab.com/sylva-projects/sylva-core")
REGISTRY_URI = OCI_REGISTRY.replace("oci://", "")
CI_REGISTRY = os.getenv('CI_REGISTRY')
ARTIFACT_DIGEST = None

# Create a temporary directory for the artifacts
LOG_ERROR_FILE = tempfile.mktemp()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_ERROR_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ArtifactPaths:
    def __init__(self):
        self.artifact_dir = Path(tempfile.mkdtemp(prefix='sylva-artifact-'))
        self.pulled_artifact_dir = Path(tempfile.mkdtemp(prefix='sylva-pulled-'))
        self.tgz_artifact_dir = Path(tempfile.mkdtemp(prefix='tgz-'))
        logger.info(f"(working with artifact_dir: {self.artifact_dir})")
        logger.info(f"(working with pulled_artifact_dir: {self.pulled_artifact_dir})")
        logger.info(f"(working with tgz_artifact_dir: {self.tgz_artifact_dir})")


def run_command(command, hide_command=False, **kwargs):
    if not isinstance(command, list):
        kwargs['shell'] = True
        log_command = command
    else:
        log_command = " ".join([str(arg) for arg in command])

    kwargs['capture_output'] = True
    kwargs['text'] = True

    # remember 'check' parameter
    check = kwargs.get('check', True)
    # .. then unset it
    kwargs['check'] = False

    if not hide_command:
        logger.info(f"  running: {log_command}")

    process = subprocess.run(command, **kwargs)
    for line in process.stdout.splitlines():
        logger.info(f"    stdout: {line}")
    for line in process.stderr.splitlines():
        logger.warning(f"    !stderr: {line}")
    if check:
        process.check_returncode()
    return process


def chart_version_from_repo(repo):
    """Produces a string which will be used as Helm chart version
    from a source_templates.xxx repo

    Args:
        repo (dict): dict holding the repo definition (content of source_templates.xxx)
    """
    repo_ref = repo["spec"]["ref"]

    if "tag" in repo_ref:
        # remove any "xxxxx/" prefix
        return re.sub("^.*/", "", repo_ref["tag"])

    # if the source_templates repo entry points to a branch
    # we'll generate an OCI artifact with a version containing the branch name and the CI pipeline id
    # adding the pipeline id allows to have an up-to-date OCI artifact each time a new pipeline is created
    # (without the pipeline id, a new pipeline after a change of the branch, would result in a different content
    # and a failure to re-push the OCI artifact because of the checks done elsewhere in these tools to avoid
    # overwriting an existing artifact with different content)
    if "branch" in repo_ref:
        sanitized_branch_name = re.sub(r"[^a-zA-Z0-9-]", "-", repo_ref["branch"])
        pipeline_id = os.getenv("CI_PIPELINE_IID")
        if not pipeline_id:
            raise Exception(f"no CI_PIPELINE_IID, can't generate version for Helm artifact for source_template repo ({repo})")
        return f"0.0.0-{sanitized_branch_name}-{pipeline_id}"

    if "commit" in repo_ref:
        raise Exception("using commit in source_templates.x.spec.ref isn't compatible with the production of OCI artifacts")


def diff(artifact_name, source_dir, dest_dir):
    logger.info("---------- make a diff --------------")
    result = run_command(
        [
            "diff",
            "-wur",
            "--exclude",
            "Chart.lock",
            "--exclude",
            ".git",
            f"{source_dir}/",
            f"{dest_dir}/"
        ],
        check=False)

    if result.returncode != 0:
        raise ValueError(f"[ERROR] {artifact_name} content differs from the content of "
                         f"the already existing OCI artifact")

    logger.info("Integrity check: ok")


def fail_if_existing_artifact_differs(artifact_name, artifact_version, artifact_url, paths, tgz_file=None):
    logger.info(
        f"Checking the integrity of the existing artifact {artifact_name}:{artifact_version} :: "
        f"{artifact_url}")
    if tgz_file and Path(tgz_file).is_file():
        run_command(["tar", "-xzf", tgz_file, "-C", paths.tgz_artifact_dir])
        run_command(["tar", "-xzf", f"{paths.pulled_artifact_dir}/{artifact_name}-{artifact_version}.tgz", "-C",
                     paths.pulled_artifact_dir])
        os.remove(f"{paths.pulled_artifact_dir}/{artifact_name}-{artifact_version}.tgz")
        diff(artifact_name, paths.tgz_artifact_dir, paths.pulled_artifact_dir)
    else:
        # artifacts are not packaged in an archive
        diff(artifact_name, paths.artifact_dir, paths.pulled_artifact_dir)


def signature_is_valid(artifact_name):
    result = run_command(
        f"cosign verify --insecure-ignore-tlog=true --insecure-ignore-sct=true "
        f"--key env://COSIGN_PUBLIC_KEY {REGISTRY_URI}/{artifact_name}@{ARTIFACT_DIGEST}",
        check=False
    )

    if result.returncode != 0:
        raise ValueError(f"[ERROR] Signature for {artifact_name} is invalid.")

    logger.info(f"Signature for {artifact_name} is valid.")


def push_and_sign_with_helm(tgz_file, artifact_name):
    logger.info(f"Pushing {artifact_name} artifact to OCI registry using Helm tool...")
    # if we run in a gitlab CI job, then we use the credentials provided by gitlab job environment
    if CI_REGISTRY:
        registry_login()

    result = run_command(["helm", "push", tgz_file, OCI_REGISTRY])
    digest = re.search(r'.*Digest:\s+(.*)', result.stderr, flags=re.M).group(1)
    sign(artifact_name, digest)


def push_and_sign_with_flux(artifact_name, artifact_version, artifact_source, artifact_revision):
    logger.info(f"Pushing {artifact_name}:{artifact_version} artifact to OCI registry using Flux tool...")

    cmd = [
        "flux", "push", "artifact", f"{OCI_REGISTRY}/{artifact_name}:{artifact_version}",
        "--path", ".", "--source", artifact_source, "--revision", artifact_revision
    ]
    # if we run in a gitlab CI job, then we use the credentials provided by gitlab job environment
    commands = " ".join(cmd)
    logger.info(f"command: {commands}")
    if CI_REGISTRY:
        ci_registry_user = os.getenv('CI_REGISTRY_USER')
        ci_registry_password = os.getenv('CI_REGISTRY_PASSWORD')
        cmd.append("--creds")
        creds = f"{ci_registry_user}:{ci_registry_password}"
        cmd.append(creds)
    result = run_command(cmd, hide_command=True)
    digest = re.search('.*@+(.*)', result.stderr, flags=re.M).group(1)

    sign(artifact_name, digest)


def sign(artifact_name, digest):
    # sign the artifact to registry
    cosign_priv_key = os.getenv('COSIGN_PRIVATE_KEY')
    cosign_password = os.getenv('COSIGN_PASSWORD')
    if cosign_priv_key:
        if cosign_password:
            logger.info(f"Signing {artifact_name} artifact to OCI registry...")
            run_command(
                f"cosign login {CI_REGISTRY} -u {os.getenv('CI_REGISTRY_USER')} -p {os.getenv('CI_REGISTRY_PASSWORD')}"
            )
            try:
                run_command(
                    f"cosign sign -y --tlog-upload=false --key  env://COSIGN_PRIVATE_KEY "
                    f"{REGISTRY_URI}/{artifact_name}@{digest}"
                )
            except subprocess.CalledProcessError:
                logger.error(f"!! Unable to sign the {artifact_name} !!")
        else:
            logger.warning(f"Unable to sign the {artifact_name}, the private key password is not available")
    else:
        logger.warning(f"Unable to sign the {artifact_name}, the private key is not set")


def registry_login():
    ci_registry_user = os.getenv('CI_REGISTRY_USER')
    ci_registry_password = os.getenv('CI_REGISTRY_PASSWORD')
    run_command(
        f"echo '{ci_registry_password}' | helm registry login -u '{ci_registry_user}' '{CI_REGISTRY}' "
        f"--password-stdin"
    )


def artifact_exists_with_flux(artifact_name, artifact_version, artifact_url, paths):
    logger.info(f"Checking if OCI artifact exists: {artifact_name}:{artifact_version} :: {artifact_url}")
    result = run_command(["flux", "pull", "artifact", artifact_url, "-o", paths.pulled_artifact_dir],
                         check=False)
    if result.returncode == 0:
        global ARTIFACT_DIGEST
        ARTIFACT_DIGEST = re.search('.*@+(.*)', result.stderr, flags=re.M).group(1)
        return True
    return False


def artifact_exists_with_helm(artifact_name, artifact_version, artifact_url, paths):
    logger.info(f"Checking if OCI artifact exists: {artifact_name}:{artifact_version} :: {artifact_url}")
    result = run_command(["helm", "pull", artifact_url, "--version", artifact_version, "-d", paths.pulled_artifact_dir],
                         check=False)
    if result.returncode == 0:
        global ARTIFACT_DIGEST
        ARTIFACT_DIGEST = re.search(r'.*Digest:\s+(.*)', result.stderr, flags=re.M).group(1)
        return True
    return False


def process_artifact_helm(artifact_name, artifact_version, tgz_file, paths):
    artifact_url = f"{OCI_REGISTRY}/{artifact_name}"

    artifact_version = artifact_version.replace("_", "+")
    if artifact_exists_with_helm(artifact_name, artifact_version, artifact_url, paths):
        fail_if_existing_artifact_differs(artifact_name, artifact_version, artifact_url, paths, tgz_file)

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
            logger.warning(f"Unable to sign the {artifact_name}, signing material is not set")
    else:
        push_and_sign_with_helm(tgz_file, artifact_name)


def clean_directory_and_files(directory):
    for root, dirs, files in os.walk(directory):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))


# Ensure the temporary files and directories are cleaned up before next artifact treatment
def delete_temp_files(paths):
    for directory in [paths.artifact_dir, paths.pulled_artifact_dir, paths.tgz_artifact_dir]:
        clean_directory_and_files(directory)


# Ensure the temporary directory is cleaned up
def cleanup(paths):
    shutil.rmtree(paths.artifact_dir)
    shutil.rmtree(paths.pulled_artifact_dir)
    shutil.rmtree(paths.tgz_artifact_dir)
