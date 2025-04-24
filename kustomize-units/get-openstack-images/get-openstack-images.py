#!/usr/bin/env python
#
# This script can be tested with:
#
#   OS_IMAGES_INFO_PATH=my-os-images.info.yaml TARGET_NAMESPACE=sylva-system OS_CLIENT_CONFIG_FILE=./cloud.yaml \
#       OS_CLOUD=capo_cloud kustomize-units/get-openstack-images/get-openstack-images.py
#
# With my-os-images.info.yaml having content similar as the one produced by the os-images-info unit:
#
#   kubectl get configmap os-images-info -o yaml | yq '.data."values.yaml"' > my-os-images.info.yaml
#
# And cloud.yaml with the content similar to:
#
#   kubectl get secrets cluster-cloud-config -n sylva-system -o yaml | yq '.data."clouds.yaml"' | \
#       base64 -d > clouds.yaml

from kubernetes import client, config
from kubernetes.client.rest import ApiException
import openstack
import oras.client
import oras.provider
import requests
import tempfile
from urllib.parse import urlparse
import logging
import os
import shutil
import tarfile
import gzip
import yaml
import sys
import time
from datetime import datetime
from datetime import timezone
from datetime import timedelta


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(name)s %(funcName)s: %(message)s')
logger = logging.getLogger(__name__)
sys.tracebacklimit = 0
NAMESPACE = os.environ.get('NAMESPACE')
if not NAMESPACE:
    logger.exception("NAMESPACE not set")
    sys.exit(22)
os_images_info_path = os.environ.get("OS_IMAGES_INFO_PATH", '/opt/config/os-images-info.yaml')
if not os.path.exists(os_images_info_path) or not os.path.isfile(os_images_info_path):
    logger.exception(f"{os_images_info_path} not found")
    sys.exit(2)
# 'capo_cloud' is the cloud name we hardcode for CAPO in Sylva
cloud_name = os.environ.get("OS_CLOUD", "capo_cloud")
# Insecure TLS flag
tls_verify = False if os.environ.get(
    'INSECURE_CLIENT', 'false').lower() in ['true', 't'] else True
if not tls_verify:
    logger.warning("TLS Verify is disabled")
else:
    logger.info("TLS Verify is enabled")


class TokenAuth(oras.auth.TokenAuth):
    def get_auth_header(self):
        if self.token:
            return super().get_auth_header()
        return {}


oras.auth.auth_backends["token"] = TokenAuth


class MyProvider(oras.provider.Registry):
    def get_oci_manifest(self, artifact_url):
        try:
            container = self.get_container(artifact_url)
            manifest = self.get_manifest(container)
            return manifest
        except Exception:
            logger.exception("Failed to get OCI manifest.")
            raise

    def pull_image(self, artifact_uri, directory):
        try:
            res = self.pull(target=artifact_uri, outdir=directory)
            if len(res) > 1:
                raise ValueError("Expected only one file, but multiple files were found.")
            return res[0]
        except Exception:
            logger.exception("Failed to pull image.")
            raise


def download_file(url, verify_ssl, directory):
    filename = url.split('/')[-1]
    file_path = os.path.join(directory, filename)
    # Use the verify_ssl parameter for the verify argument in requests.get
    with requests.get(url, stream=True, verify=verify_ssl) as r:
        r.raise_for_status()
        with open(file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return file_path


def cleanup_image(path):
    # Check if the file path exists and is a directory
    if os.path.exists(path) and os.path.isdir(path):
        shutil.rmtree(path)
        return f"Directory '{path}' has been removed."
    else:
        return f"The path '{path}' does not exist or is not a directory."


def unzip_artifact(file_path):
    # Check if the file exists
    if not os.path.exists(file_path):
        logger.warning(f"The file '{file_path}' does not exist.")
        return None
    # Determine the extraction path
    extraction_path = os.path.dirname(file_path)
    # Extract the tar.gz file
    with tarfile.open(file_path, 'r:gz') as tar:
        tar.extractall(path=extraction_path)
        logger.info(f"Extracted '{file_path}' to '{extraction_path}'.")
    # remove raw file to save PV size
    os.remove(file_path)
    # Initialize a variable to hold the path of a non-gzipped file, if found
    non_gz_file_path = None

    # Find and gunzip the .gz file or identify .raw/.qcow file
    for root, _, files in os.walk(extraction_path):
        for file in files:
            if file.endswith(".gz"):
                gz_file = os.path.join(root, file)
                extracted_file_path = gz_file[:-3]  # Removes the .gz extension
                logger.info(f"Gunzipping '{gz_file}' to '{extracted_file_path}'")
                with gzip.open(gz_file, 'rb') as f_in, open(extracted_file_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
                    logger.info(f"Gunzipped '{gz_file}' to '{extracted_file_path}'")
                return extracted_file_path
            elif file.endswith(".raw") or file.endswith(".qcow2"):
                # Store the path but do not return immediately to prioritize .gz extraction
                # If no .gz file found but a .raw or .qcow file was found, return its path
                non_gz_file_path = os.path.join(root, file)
                logger.info(f"Found non-gzipped file '{non_gz_file_path}'.")
                return non_gz_file_path

    # If no .gz, .raw, or .qcow file found, return None
    logger.info(f"no .gz, .raw, or .qcow file found: {', '.join([f[0] for f in os.walk(extraction_path)])}")
    return None


def image_exists_in_glance(checksum, _image_name, status=['active']):
    try:
        matching_images = [
            image
            for image in conn.image.images(tags=[f"sylva-md5-{checksum}"], visibility="community")
            if image.status in status
        ]
        if _image_name in [i.name for i in matching_images]:
            logger.warning(f"Image with name '{_image_name}' already exists.")
        return matching_images
    except openstack.exceptions.HttpException:
        logger.exception("HTTP error occurred while checking images.")
        raise
    except openstack.exceptions.SDKException:
        logger.exception("SDK error occurred while checking images.")
        raise
    except Exception:
        logger.exception("Unexpected error occurred while checking images.")
        raise


def handle_queued_image(image):
    try:
        logger.info(f"Deleting image {image.name}  {image.id}")
        conn.image.delete_image(image.id)
        logger.warning(f"Stalling image {image.name} {image.id} deleted")
    except Exception as E:
        logger.warning(f"Can't delete image {image.name} {image.id} : {str(E)}")


def wait_for_in_progress_image(image_name, checksum):
    """
        if an image is already "saving" wait for it to complete
        if an image is "queued" wait for 10sec and then clean it (stalling image upload)
    """
    TIMEOUT = timedelta(hours=1)
    WAIT_QUEUED_IMAGE = 10
    LOOP_INTERVAL = 10
    t0 = datetime.now(timezone.utc)
    image_active = None
    ignored_queued_images = []
    images = [None]

    # this main loop is meant to wait for images in 'saving' state
    while (datetime.now(timezone.utc) - t0 < TIMEOUT):
        images = image_exists_in_glance(
            _image_name=image_name,
            checksum=checksum,
            status=['active', 'queued', 'importing', 'uploading', 'saving']
        )
        for image in images:
            if image.status == 'active':
                image_active = image
                break
            if image.status == 'queued':
                created_at = datetime.strptime(image.created_at, "%Y-%m-%dT%H:%M:%S%z")
                if created_at > t0 - timedelta(seconds=WAIT_QUEUED_IMAGE):
                    # image create less than WAIT_QUEUED_IMAGE seconds ago
                    logger.warning(
                        f"Stalling image {image.name} {image.id} waiting {WAIT_QUEUED_IMAGE} seconds")
                    time.sleep(WAIT_QUEUED_IMAGE)

                _image = conn.image.get_image(image.id)
                if _image.status == 'queued':
                    if _image.owner == conn.current_project_id:
                        # probably a stalling image, we try to remove it
                        handle_queued_image(image)
                    else:
                        # stalling image but we can't delete it
                        # we can't remediate, manual action needed
                        logger.warning(
                            f"Can't delete image {image.name} {image.id} :"
                            f" {conn.current_project_id} is not the owner")
                        logger.warning(
                            f"Owner of image {image.name} {image.id} is {image.owner}, ignoring it for now"
                        )
                        # this image will not be taken into account for now
                        # (the tenant owning it may or may not continue to work on it, but we don't want to block on it)
                        ignored_queued_images.append(image.id)
            if image.status in ['saving', 'importing', 'uploading']:
                logger.info(f"Waiting for image {image.name} {image.id} to be active")

        # we break out of the loop if:
        # - we have found an active image
        # - or if there is no image to wait for (we ignore the images in 'queued' state that we don't own)
        relevant_images = [i for i in images if i.id not in ignored_queued_images]
        if image_active or not relevant_images:
            break
        time.sleep(LOOP_INTERVAL)
    return image_active


def push_image_to_glance(file, manifest, image_name, image_format, update_only=False, existing_image=None):
    _checksum = manifest['md5']
    tag = f"sylva-md5-{_checksum}"

    if update_only:
        if not existing_image or not hasattr(existing_image, 'id'):
            logger.error("Existing image details are required for updating.")
            raise Exception("Existing image details are required for updating image information.")
        logger.info(f"Updating image properties for image ID {existing_image.id} with tag {tag}...")
        image = existing_image
    else:
        image = wait_for_in_progress_image(image_name=image_name, checksum=_checksum)
        if not image:
            try:
                with open(file, 'rb') as image_data:
                    logger.info(f"{image_name}: creating image with tag {tag}")
                    image = conn.image.create_image(
                        name=image_name,
                        data=image_data,
                        disk_format=image_format,
                        md5=_checksum,
                        tags=[tag],
                        allow_duplicates=True,
                        visibility="community"
                    )
                    logger.info(f"Image UUID: {image.id}")
            except openstack.exceptions.HttpException:
                logger.exception("HTTP error during image creation.")
                raise
            except openstack.exceptions.SDKException:
                logger.exception("OpenStack SDK error during image creation.")
                raise
            except Exception:
                logger.exception("Unexpected error during image creation.")
                raise

    # Common block for updating image properties, applicable in both cases
    try:
        _image_data = conn.image.find_image(image.id)
        if openstack_user_project_id == _image_data.owner:
            logger.info("Updating image properties...")
            image_properties = {f"sylva/{k}": v for k, v in manifest.items()}
            logger.info(f"Image properties to update: {image_properties}")
            updated_image = conn.image.update_image(image.id, properties=image_properties)
            return updated_image
    except openstack.exceptions.ForbiddenException:
        logger.exception("Forbidden error while updating image properties.")
        raise
    except openstack.exceptions.HttpException:
        logger.exception("HTTP error while updating image properties.")
        raise
    except Exception:
        logger.exception("Unexpected error while updating image properties.")
        raise


# Create empty configmap
configmap = {}

##############################
# Parse the YAML string resulted from loading the contents of the ConfigMap/os-images-info-xxxx
#       (produced by the os-images-info unit)
with open(os_images_info_path, 'r') as file:
    os_images = yaml.safe_load(file.read())
os_images = os_images['os_images']
logger.info(f"os_images: {os_images}")

##############################

# Initialize openstack connection
conn = openstack.connect(cloud=cloud_name, verify=False)
openstack_user_project_id = conn.current_project_id

for os_name, os_image_info in os_images.items():
    # Initialize oras class inside the for in order to retrieve a new token
    oras_client = MyProvider(tls_verify=tls_verify)
    artifact = os_image_info["uri"]
    md5_checksum = os_image_info['md5']
    image_format = os_image_info['image-format']
    parsed_url = urlparse(artifact)
    if os_image_info.get("commit-tag"):
        _os_name = f'{os_name}-sylva-diskimage-builder-{os_image_info["commit-tag"]}'
    else:
        _os_name = os_name
    logger.info(f"Working on image: {os_name} with MD5 checksum {md5_checksum}")
    existing_images = image_exists_in_glance(md5_checksum, _os_name)

    if not existing_images:
        temp_dir = tempfile.mkdtemp()
        logger.info(f"image not in Glance: {os_name} / md5 {md5_checksum}")
        logger.info(f"Pulling image: {os_name} from artifact uri: {artifact} to {temp_dir}")
        image_path = ''
        if parsed_url.scheme in ['http', 'https']:
            image_path = download_file(artifact, verify_ssl=tls_verify, dir=temp_dir)
        elif parsed_url.scheme == 'oci':
            oras_pull_path = oras_client.pull_image(artifact, directory=temp_dir)
            logger.info("Unzipping artifact...")
            image_path = unzip_artifact(oras_pull_path)
        try:
            logger.info("Pushing image to Glance...")
            image = push_image_to_glance(image_path, os_image_info, _os_name, image_format)
            logger.info(f"Image pushed to glance with image ID {image['id']}")
        except Exception:
            logger.exception("exception while pushing image to glance")
            raise
        finally:
            logger.info("Cleaning up files")
            cleanup_image(temp_dir)

        if image and 'id' in image:
            logger.info("Updating configmap")
            configmap.update({os_name: {'openstack_glance_uuid': image['id']}})
        else:
            logger.warning(
                "Image push to Glance failed, image ID is unavailable, or image is None; "
                "configmap will not be updated.")
    else:
        # Image already exists in Glance, so we might want to update it
        logger.info(f"Image already in Glance: {os_name} with MD5 checksum {md5_checksum}")
        image_to_update = existing_images[0]  # Assuming we get one image back
        logger.info(f"Existing image details - Name: {image_to_update.name}, UUID: {image_to_update.id}")

        # Optional: Pull manifest to verify/update image properties
        if parsed_url.scheme == 'oci':
            manifest = oras_client.get_oci_manifest(artifact)

        try:
            logger.info("Updating image properties in Glance...")
            updated_image = push_image_to_glance(
                None, os_image_info, _os_name, image_format, update_only=True, existing_image=image_to_update)
            if updated_image and hasattr(updated_image, 'id'):
                logger.info(f"Image properties updated for image ID {updated_image.id}")
            else:
                logger.warning("Image properties could not be updated")
        except Exception:
            logger.exception("Error updating image properties.")
            raise

        # Update configmap with the existing image's UUID
        configmap.update({os_name: {'openstack_glance_uuid': image_to_update.id}})

    logger.info(f"Finished processing image: {os_name}")

logger.info(f"""Images UUID map:
{configmap}""")

logger.info("Pushing ConfigMap to Kubernetes...")

# Initialize Kube config
# Load Kubernetes configuration
try:
    config.load_incluster_config()
except Exception:
    # this is meant to allow testing this script manually out of a pod,
    # assuming that KUBECONFIG points to your kubeconfig
    config.load_kube_config()
api_instance = client.CoreV1Api()

# Define the metadata for the ConfigMap
metadata = client.V1ObjectMeta(
    name="openstack-images-uuids",
    namespace=NAMESPACE
)

# Convert configmap to yaml-formatted string
# os_images is the key expected for sylva-capi-cluster chart values
yaml_string = yaml.dump({'os_images': configmap}, default_flow_style=False)

# Create a ConfigMap object
body = client.V1ConfigMap(
    api_version="v1",
    kind="ConfigMap",
    metadata=metadata,
    data={'values.yaml': yaml_string}
)


def create_or_update_configmap(api_instance, namespace, body):
    try:
        # Check if the ConfigMap exists
        api_instance.read_namespaced_config_map(name=body.metadata.name, namespace=namespace)
        # If exists, update the ConfigMap
        api_response = api_instance.replace_namespaced_config_map(
            name=body.metadata.name, namespace=namespace, body=body)
        logger.info(f"ConfigMap updated. Name: {api_response.metadata.name}")
    except ApiException as e:
        if e.status == 404:
            # If not exists, create the ConfigMap
            try:
                api_response = api_instance.create_namespaced_config_map(namespace=namespace, body=body)
                logger.info(f"ConfigMap created. Name: {api_response.metadata.name}")
            except ApiException:
                logger.exception("Failed to create ConfigMap after not finding an existing one.")
                raise
        else:
            # Handle other exceptions
            logger.exception("Exception occurred while updating or creating ConfigMap.")
            raise


# Create the ConfigMap in the specified namespace
try:
    create_or_update_configmap(api_instance, NAMESPACE, body)
except Exception as e:
    logger.error(f"upsie.. : {e}")
    raise

logger.info("We're done")
