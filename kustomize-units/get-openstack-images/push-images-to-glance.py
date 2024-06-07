#!/usr/bin/env python
#
# This script can be tested with:
#
#   OS_IMAGES_INFO_PATH=my-os-images.info.yaml TARGET_NAMESPACE=sylva-system OS_CLIENT_CONFIG_FILE=./cloud.yaml OS_CLOUD=capo_cloud kustomize-units/get-openstack-images/push-images-to-glance.py
#
# With my-os-images.info.yaml having content similar as the one produced by the os-images-info unit:
#
#   kubectl get configmap os-images-info -o yaml | yq '.data."values.yaml"' > my-os-images.info.yaml
#
# And cloud.yaml with the content similar to:
#
#   kubectl get secrets cluster-cloud-config -n sylva-system -o yaml | yq '.data."clouds.yaml"' | base64 -d > clouds.yaml

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
import sys
import yaml

from distutils.util import strtobool

class MyProvider(oras.provider.Registry):
    def get_oci_manifest(self, artifact_url):
        try:
            container = self.get_container(artifact_url)
            manifest = self.get_manifest(container)
            return manifest
        except Exception:
            logger.exception("Failed to get OCI manifest.")
            raise

    def pull_image(self, artifact_uri):
        try:
            res = self.pull(target=artifact_uri)
            if len(res) > 1:
                raise ValueError("Expected only one file, but multiple files were found.")
            return res[0]
        except Exception:
            logger.exception("Failed to pull image.")
            raise

def download_file(url, verify_ssl):
    temp_dir = tempfile.mkdtemp()
    filename = url.split('/')[-1]
    file_path = os.path.join(temp_dir, filename)
    # Use the verify_ssl parameter for the verify argument in requests.get
    with requests.get(url, stream=True, verify=verify_ssl) as r:
        r.raise_for_status()
        with open(file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return file_path

def cleanup_image(file_path):
    parent_dir = os.path.dirname(file_path)
    # Check if the file path exists and is a directory
    if os.path.exists(parent_dir) and os.path.isdir(parent_dir):
        shutil.rmtree(parent_dir)
        return f"Directory '{parent_dir}' has been removed."
    else:
        return f"The path '{file_path}' does not exist or is not a directory."

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

    # Initialize a variable to hold the path of a non-gzipped file, if found
    non_gz_file_path = None

    # Find and gunzip the .gz file or identify .raw/.qcow file
    for root, dirs, files in os.walk(extraction_path):
        for file in files:
            if file.endswith(".gz"):
                gz_file = os.path.join(root, file)
                extracted_file_path = gz_file[:-3]  # Removes the .gz extension
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


def image_exists_in_glance(checksum, _image_name):
    try:
        matching_images = [
            {
                'id': image.id,
                'name': image.name,
                'checksum': image.get('checksum'),
                'tags': image.tags
            } 
            for image in conn.image.images(tags=[f"sylva-md5-{checksum}"], visibility="community")
            if image.properties is not None and image.get('checksum') == checksum
        ]
        if _image_name in [i['name'] for i in matching_images]:
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


def push_image_to_glance(file, manifest, image_name, image_format, update_only=False, existing_image=None):
    _checksum = manifest['md5']
    tag = f"sylva-md5-{_checksum}"

    if update_only:
        if not existing_image or 'id' not in existing_image:
            logger.error("Existing image details are required for updating.")
            raise Exception("Existing image details are required for updating image information.")
        image_id = existing_image['id']
        logger.info(f"Updating image properties for image ID {image_id} with tag {tag}...")
    else:
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
                    visibility="community",
                )
                logger.info(f"Image UUID: {image.id}")
                image_id = image.id
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
        _image_data = conn.image.find_image(image_id)
        if openstack_user_project_id == _image_data.owner:
            logger.info("Updating image properties...")
            image_properties = {f"sylva/{k}": v for k, v in manifest.items()}
            logger.info(f"Image properties to update: {image_properties}")
            updated_image = conn.image.update_image(image_id, properties=image_properties)
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


# Set namspace var
NAMESPACE = os.environ.get('TARGET_NAMESPACE')
# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(name)s %(funcName)s: %(message)s')
logger = logging.getLogger(__name__)

# Create empty configmap
configmap = {}

##############################
# Parse the YAML string resulted from loading the contents of the ConfigMap/os-images-info-xxxx  (produced by the os-images-info unit)
os_images_info_path = os.environ.get("OS_IMAGES_INFO_PATH", '/opt/config/os-images-info.yaml')
with open(os_images_info_path, 'r') as file:
    os_images = yaml.safe_load(file.read())
os_images = os_images['os_images']
logger.info(f"os_images: {os_images}")

##############################

# Initialize openstack connection
try:
    cloud_name = os.environ.get("OS_CLOUD","capo_cloud")  # 'capo-cloud' is the cloud name we hardcode for CAPO in Sylva
except KeyError:
    raise Exception("no OS_CLOUD environment variable specified")
conn = openstack.connect(cloud=cloud_name, verify=False)
openstack_user_project_id = conn.current_project_id

for os_name, os_image_info in os_images.items():
    artifact = os_image_info["uri"]
    md5_checksum = os_image_info['md5']
    image_format = os_image_info['image-format']
    insecure_tls = os_image_info['insecure']
    os_image_info.pop('insecure', None)
    parsed_url = urlparse(artifact)
    if os_image_info.get("commit-tag"):
        _os_name = f'{os_name}-sylva-diskimage-builder-{os_image_info["commit-tag"]}'
    else:
        _os_name = os_name
    logger.info(f"Working on image: {os_name} with MD5 checksum {md5_checksum}")
    existing_images = image_exists_in_glance(md5_checksum, _os_name)

    if not existing_images:
        logger.info(f"image not in Glance: {os_name} / md5 {md5_checksum}" )
        logger.info(f"Pulling image: {os_name} from artifact uri: {artifact}")
        image_path = ''
        if parsed_url.scheme in ['http', 'https']:
            image_path = download_file(artifact, verify_ssl=not insecure_tls)
        elif parsed_url.scheme == 'oci':
            oras_client = MyProvider(tls_verify=not insecure_tls)
            oras_pull_path = oras_client.pull_image(artifact)
            logger.info(f"Unzipping artifact...")
            image_path = unzip_artifact(oras_pull_path)
        try:
            logger.info("Pushing image to Glance...")
            image = push_image_to_glance(image_path, os_image_info, _os_name, image_format)
            logger.info(f"Image pushed to glance with image ID {image['id']}")
            logger.info(f"Cleaning up files")
            if parsed_url.scheme in ['http', 'https']:
                cleanup_image(image_path)
            else:
                cleanup_image(oras_pull_path)
        except Exception:
            logger.exception("exception while pushing image to glance")
            raise

        if image and 'id' in image:
            logger.info("Updating configmap")
            configmap.update({os_name: {'openstack_glance_uuid': image['id']}})
        else:
            logger.warning("Image push to Glance failed, image ID is unavailable, or image is None; configmap will not be updated.")
    else:
        # Image already exists in Glance, so we might want to update it
        logger.info(f"Image already in Glance: {os_name} with MD5 checksum {md5_checksum}")
        image_to_update = existing_images[0]  # Assuming we get one image back
        logger.info(f"Existing image details - Name: {image_to_update['name']}, UUID: {image_to_update['id']}")

        # Optional: Pull manifest to verify/update image properties
        if parsed_url.scheme == 'oci':
            oras_client = MyProvider(tls_verify=not insecure_tls)
            manifest = oras_client.get_oci_manifest(artifact)

        try:
            logger.info("Updating image properties in Glance...")
            updated_image = push_image_to_glance(None, os_image_info, _os_name, image_format, update_only=True, existing_image=image_to_update)
            if updated_image and 'id' in updated_image:
                logger.info(f"Image properties updated for image ID {updated_image['id']}")
            else:
                logger.warning("Image properties could not be updated")
        except Exception:
            logger.exception(f"Error updating image properties.")
            raise

        # Update configmap with the existing image's UUID
        configmap.update({os_name: {'openstack_glance_uuid': image_to_update['id']}})

    logger.info(f"Finished processing image: {os_name}")

logger.info(f"""Images UUID map:
{configmap}""")

logger.info(f"Pushing ConfigMap to Kubernetes...")

# Initialize Kube config
# Load Kubernetes configuration
try:
    config.load_incluster_config()
except:  # this is meant to allow testing this script manually out of a pod, assuming that KUBECONFIG points to your kubeconfig
    config.load_kube_config()
api_instance = client.CoreV1Api()

# Define the metadata for the ConfigMap
metadata = client.V1ObjectMeta(
    name="openstack-images-uuids",
    namespace=NAMESPACE
)

# Convert configmap to yaml-formatted string
yaml_string = yaml.dump({'os_images': configmap}, default_flow_style=False)  # os_images is the key expected for sylva-capi-cluster chart values

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
        api_response = api_instance.replace_namespaced_config_map(name=body.metadata.name, namespace=namespace, body=body)
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

logger.info(f"We're done")
