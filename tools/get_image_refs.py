import argparse
import base64
import json
import logging
import os
from typing import Optional
import yaml
import paramiko
from docker_image import reference
from kubernetes.config.config_exception import ConfigException
from kubernetes.client.rest import ApiException
from kubernetes import client, config
from pydantic import BaseModel
from merge_image_refs import update_images_ref

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class OwnerReference(BaseModel):
    """Kubernetes owner reference."""
    apiVersion: str
    kind: str
    name: str


class Metadata(BaseModel):
    """Kubernetes resource metadata."""
    name: str
    namespace: Optional[str] = None
    labels: Optional[dict] = None
    ownerReferences: Optional[list[OwnerReference]] = None


class Resource(BaseModel):
    """Kubernetes resource."""
    kind: str
    apiVersion: str
    metadata: Metadata


class K8sParser(object):
    """
    Parses Kubernetes cluster information and retrieves various resource details.

    This class initializes Kubernetes clients for management and workload clusters, checks cluster reachability,
    and traces dependencies of Kubernetes resources.
    We need to pass a kubeconfig and optionally a workload cluster name.

    :param kubeconfig: Optional. Path to the management cluster kubeconfig file. If not provided, the default system kubeconfig will be used.
    :param workload_kubeconfig: Optional. Path to the workload cluster kubeconfig file.
    :param workload_name: Optional. Workload cluster name.
    """

    def __init__(self, kubeconfig=None, workload_kubeconfig=None, workload_name=None):

        if not kubeconfig:
            kubeconfig = os.environ['KUBECONFIG']

        try:
            # Initialize Kubernetes clients
            config_mgmt = config.new_client_from_config(kubeconfig)
            self.api_core_mgmt = client.CoreV1Api(config_mgmt)
            self.api_mgmt = client.CustomObjectsApi(config_mgmt)
            apis_mgmt = client.ApisApi(config_mgmt)

            api_mgmt_versions = apis_mgmt.get_api_versions()

            for group in api_mgmt_versions.groups:
                if group.name == "helm.toolkit.fluxcd.io":
                    self.helmrelease_api_version = group.preferred_version.version
                if group.name == "cluster.x-k8s.io":
                    self.cluster_api_version = group.preferred_version.version

            # Fetch workload cluster kubeconfig if provided
            config_wkl = None
            if workload_name:
                workload_namespace = self.get_workload_cluster_namespace(workload_name)
                wkl_kubeconfig_dict = self.get_kubeconfig_from_secret(f"{workload_name}-kubeconfig", workload_namespace)
                config_wkl = config.new_client_from_config_dict(wkl_kubeconfig_dict)
            elif workload_kubeconfig:
                config_wkl = config.new_client_from_config(workload_kubeconfig)
            if config_wkl:
                self.api_core = client.CoreV1Api(config_wkl)
                self.api = client.CustomObjectsApi(config_wkl)
            else:
                self.api_core = self.api_core_mgmt
                self.api = self.api_mgmt

            self.nodes = self.api_core.list_node()

        except ConfigException as e:
            raise RuntimeError("Failed to load kubeconfig. Ensure file is present and correctly configured.") from e
        except Exception as e:
            raise Exception(f"Error: {e}")

    def is_cluster_reachable(self):
        """
        Checks if the Kubernetes cluster is reachable by listing namespaces.

        :return: A boolean indicating if the connection was successful or not.
        :rtype: bool
        """
        try:
            self.api_core.list_namespace(_request_timeout=5)
            return True
        except Exception:
            return False

    def get_workload_cluster_namespace(self, workload_cluster_name):
        try:
            # List all cluster.cluster objects across all namespaces
            clusters = self.api_mgmt.list_cluster_custom_object(
                group="cluster.x-k8s.io",
                version=self.cluster_api_version,
                plural="clusters"
            )

            # Find the namespace for the given workload cluster name
            for cluster in clusters['items']:
                if cluster['metadata']['name'] == workload_cluster_name:
                    return cluster['metadata']['namespace']
            raise RuntimeError(f"Workload cluster {workload_cluster_name} not found.")
        except ApiException as e:
            raise RuntimeError(f"Failed to get workload cluster namespace: {e}")

    def get_kubeconfig_from_secret(self, secret_name, namespace='default'):
        """
        Retrieves the kubeconfig from a Kubernetes secret.

        :param secret_name: The name of the secret containing the kubeconfig.
        :param namespace: The namespace where the secret is located.
        :return: The kubeconfig as a string.
        :rtype: dict
        """
        try:
            secret = self.api_core_mgmt.read_namespaced_secret(secret_name, namespace)
            kubeconfig_str = base64.b64decode(secret.data['value']).decode('utf-8')
            kubeconfig_dict = yaml.safe_load(kubeconfig_str)
            return kubeconfig_dict
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve kubeconfig from secret {secret_name} in namespace {namespace}: {e}")

    def type_of_resource(self, group, version, kind):
        """
        Determines the type of Kubernetes resource based on the provided group, version, and kind.

        :param group: The API group of the resource.
        :type group: str
        :param version: The API version of the resource.
        :type version: str
        :param kind: The kind of the resource.
        :type kind: str
        :return: A tuple containing the plural name of the resource and a boolean indicating whether the resource is namespaced.
        :rtype: tuple
        :raises Exception: If the resource kind is not found in the specified group and version.
        """
        if group == '':
            resources = self.api_core.get_api_resources()
        else:
            resources = self.api.get_api_resources(group, version)
        for res in resources.resources:
            if res.kind == kind and '/' not in res.name:
                return res.name, res.namespaced
        raise Exception(f"Resource kind {kind} not found in {group}/{version}")

    def get_nodes_ips(self):
        """
        Inefficiant way to retrieves IP addresses of the nodes in the Kubernetes cluster.

        This function is more like a placeholder for further improvements.

        :return: A list of IP addresses of the nodes.
        :rtype: list
        """
        return [node.status.addresses[0].address for node in self.nodes.items]

    def get_nodes_images(self):
        """
        Returns a list of images in nodes.

        :return: A list of dictionaries containing repoDigest and aliases of images in nodes.
        :rtype: list
        """
        node_images = []
        logger.info(" >>> Discover nodes images")
        for node in self.nodes.items:
            for img in node.status.images:
                repoDigest = None
                aliases = []
                for _str in img.names:
                    if 'sha256' in _str:
                        repoDigest = _str
                    else:
                        aliases.append(_str)
                if repoDigest:
                    existing_img = [_img for _img in node_images if _img['repoDigest'] == repoDigest]
                    if existing_img:
                        # update reference
                        for alias in aliases:
                            if alias not in existing_img[0]['aliases']:
                                existing_img[0]['aliases'].append(alias)
                                logger.info(f" - {alias}")
                            else:
                                logger.info(f" - {alias} exists already in reference")
                    else:
                        node_images.append(dict(repoDigest=repoDigest, aliases=aliases))

        logger.info(" >>> Discover nodes images: done")
        return node_images

    def look_for_unit(self, obj):
        """
        Recursively looks for the unit (ancestor) of a given Kubernetes object.

        :param obj: A Kubernetes object with metadata attributes such as kind, name, namespace, labels, and ownerReferences.
        :type obj: Resource
        :return: A list of dictionaries, each representing a Kubernetes object in the ancestry chain, from the current object to its ancestors.
        :rtype: list
        """
        current_object = {'kind': obj.kind, 'name': obj.metadata.name, 'namespace': obj.metadata.namespace}
        print(current_object)
        if obj.metadata.labels and obj.metadata.labels.get('kustomize.toolkit.fluxcd.io/name'):

            return [
                current_object,
                {
                    'kind': 'Kustomization',
                    'name': obj.metadata.labels['kustomize.toolkit.fluxcd.io/name'],
                    'namespace': obj.metadata.labels['kustomize.toolkit.fluxcd.io/namespace']
                }
            ]
        if obj.metadata.labels and obj.metadata.labels.get('helm.toolkit.fluxcd.io/name'):
            ancestor = self.api_mgmt.get_namespaced_custom_object(
                group='helm.toolkit.fluxcd.io',
                version=self.helmrelease_api_version,
                namespace=obj.metadata.labels['helm.toolkit.fluxcd.io/namespace'],
                plural='helmreleases',
                name=obj.metadata.labels['helm.toolkit.fluxcd.io/name'],
                _preload_content=False)
            res = Resource.model_validate(json.loads(ancestor.read()))
            dependencies = self.look_for_unit(res)
            return [current_object] + dependencies
        if obj.metadata.ownerReferences:
            owner_reference = obj.metadata.ownerReferences[0]
            kind = owner_reference.kind

            if '/' in owner_reference.apiVersion:
                group = owner_reference.apiVersion.split('/')[0]
                version = owner_reference.apiVersion.split('/')[1]
            else:
                group = ''
                version = owner_reference.apiVersion

            plural, namespaced = self.type_of_resource(group, version, kind)

            if group != '' and namespaced:
                ancestor = self.api.get_namespaced_custom_object(
                    group=group,
                    version=version,
                    namespace=obj.metadata.namespace,
                    plural=plural,
                    name=owner_reference.name,
                    _preload_content=False)
            if group != '' and not namespaced:
                ancestor = self.api.get_cluster_custom_object(
                    group=group,
                    version=version,
                    plural=plural,
                    name=owner_reference.name,
                    _preload_content=False)
            if group == '' and kind == 'Node':
                ancestor = self.api_core.read_node(name=owner_reference.name, _preload_content=False)
            res = Resource.model_validate(json.loads(ancestor.read()))
            dependencies = self.look_for_unit(res)
            return [current_object] + dependencies
        else:
            return [current_object]

    def get_pods_images_dependencies(self):
        """
        Retrieves the dependencies of Kubernetes resources in the cluster.

        This function lists all pods in all namespaces and inspects their metadata to determine their dependencies.
        It identifies the images used by each pod and traces their ancestry to determine the unit (ancestor) they belong to.
        The function returns a dictionary where keys are image names and values are nested dictionaries representing the dependency tree.

        :return: A dictionary containing the dependencies of Kubernetes resources, structured as image_dependencies.
        :rtype: dict
        """
        image_dependencies = {}

        pods = self.api_core.list_pod_for_all_namespaces(watch=False)

        for i in pods.items:
            ret = self.api_core.read_namespaced_pod(i.metadata.name, i.metadata.namespace, _preload_content=False)
            res = Resource.model_validate(json.loads(ret.read()))

            containers = i.spec.containers or []
            containers += i.spec.init_containers or []
            containers += i.spec.ephemeral_containers or []

            for container in containers:
                img = container.image
                normalized_img = reference.Reference.parse_normalized_named(img).string()
                if normalized_img not in image_dependencies:
                    image_dependencies[normalized_img] = {}

                dependencies = self.look_for_unit(res)
                current_level = image_dependencies[normalized_img]
                for dep in reversed(dependencies):
                    kind_name = f"{dep['kind']}/{dep['namespace']}/{dep['name']}"
                    if kind_name not in current_level:
                        current_level[kind_name] = {}
                    current_level = current_level[kind_name]

                # Add container name to the final level as a list
                if 'containers' not in current_level:
                    current_level['containers'] = []
                current_level['containers'].append(container.name)
        return image_dependencies

    def get_images_per_unit(self, image_dependencies: dict):
        """
        Creates a dictionary of images per unit based on the dependencies of Kubernetes resources.

        :param: image_dependencies: A dictionary containing the dependencies of Kubernetes resources, structured as image_dependencies.
        :return: A dictionary containing images per unit.
        :rtype: dict
        """
        images_per_unit = {}
        for img, dependencies in image_dependencies.items():
            def traverse_dependencies(deps):
                for key, value in deps.items():
                    if key.startswith('Kustomization/'):
                        unit_name = key.split('/')[-1]
                        if unit_name in images_per_unit:
                            images_per_unit[unit_name].add(img)
                        else:
                            images_per_unit[unit_name] = {img}
                    if isinstance(value, dict):
                        traverse_dependencies(value)

            traverse_dependencies(dependencies)

        # Convert sets to lists
        images_per_unit = {k: list(v) for k, v in images_per_unit.items()}
        return images_per_unit

    def get_images_without_unit(self, image_dependencies: dict):
        """
        Creates a dictionary of images without a unit based on the dependencies of Kubernetes resources.

        :param: image_dependencies: A dictionary containing the dependencies of Kubernetes resources, structured as image_dependencies.
        :return: A dictionary containing dependencies of images without a unit.
        :rtype: dict
        """
        image_without_unit_dependencies = {}
        for img, dependencies in image_dependencies.items():
            for dependency in dependencies:
                if 'Kustomization' not in dependency:
                    if img in image_without_unit_dependencies:
                        image_without_unit_dependencies[img].append(dependency)
                    else:
                        image_without_unit_dependencies[img] = [dependency]
        return image_without_unit_dependencies

    def get_units_per_image(self, images_per_unit: dict):
        """
        Creates a dictionary of units per image based on the images per unit.
        Basically, it reverses the images_per_unit dictionary.

        :param: A dictionary containing images per unit.
        :return: A dictionary containing units per image.
        :rtype: dict
        """
        # Create unit_of_image dictionary
        units_per_image = {}
        for unit, images in images_per_unit.items():
            for image in images:
                if image not in units_per_image:
                    units_per_image[image] = set()  # Use a set to avoid duplicates
                units_per_image[image].add(unit)

        # Convert sets back to lists
        for unit in units_per_image:
            units_per_image[unit] = list(units_per_image[unit])

        return units_per_image


def get_crictl_images(hostnames=None, ssh_key_path=None, user=None, runtime_endpoint=None, crictl_path=None, sudo=False):
    """
    Retrieve images from nodes using crictl via SSH.
    Assuming the same user, ssh key are used for all nodes.

    :param hostnames: List of node hostnames.
    :param ssh_key_path: Path to the SSH key for authentication.
    :param user: SSH user.
    :param runtime_endpoint: Runtime endpoint for crictl.
    :param crictl_path: Path to the crictl binary.
    :param sudo: Whether to use sudo for the command.
    :return: Tuple containing crictl outputs and a set of images.
    :rtype: tuple
    """
    crictl_outputs = {}
    crictl_images_set = set()

    command = f"{'sudo ' if sudo else ''} {crictl_path} {'--runtime-endpoint ' + runtime_endpoint if runtime_endpoint else ''} images -o json"

    for hostname in hostnames:
        output, error = run_command_via_ssh(hostname,
                                            user,
                                            ssh_key_path,
                                            command=command)
        if output:
            hostname_crictl_images = json.loads(output)
            crictl_outputs[hostname] = hostname_crictl_images

            images = hostname_crictl_images.get("images", [])
            for image in images:
                repo_tags = image.get("repoTags", [])
                crictl_images_set.update(repo_tags)

    return crictl_outputs, crictl_images_set


def run_command_via_ssh(hostname, username, key_file, command):
    """
    Executes a command on a remote server via SSH.

    example: run_command_via_ssh(hostname, username, key_file, command)

    :param hostname: The hostname or IP address of the remote server.
    :param username: The username for SSH authentication.
    :param key_file: Path to the private key file for authentication.
    :param command: The command to be executed on the remote server.
    :return: A tuple containing:
        - Standard output from the command execution.
        - Standard error output from the command execution.
    :rtype: tuple
    :raises SSHException: If there is an issue with the SSH connection or command execution.
    :raises FileNotFoundError: If the specified key file cannot be found.
    :raises Exception: For any other exceptions that may occur during execution.
    """
    # Create an SSH client
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # We could use subprocess in this function, but I wanted to try establishing ssh connection with Python (no real reason to that)
        # ssh_command = [
        #     'ssh',
        #     '-i', key_file,
        #     f'{username}@{hostname}',
        #     command
        #     ]
        # try:
        #    except subprocess.CalledProcessError as e:
        #    print(f"Command execution failed: {e}")
        #    raise

        #    result = subprocess.run(ssh_command, capture_output=True, text=True, check=True)
        #    output = result.stdout
        #    error = result.stderr
        # except subprocess.CalledProcessError as e:
        #    print(f"Command execution failed: {e}")
        #    raise

        # Load the private key
        private_key = paramiko.RSAKey.from_private_key_file(key_file)

        # Connect to the remote machine using the private key
        print(f"Connecting to {hostname}...")
        client.connect(hostname, username=username, pkey=private_key)
        print(f"Connected to {hostname}.")

        # Execute the command
        stdin, stdout, stderr = client.exec_command(command)

        # Read output and error streams
        output = stdout.read().decode()
        error = stderr.read().decode()

        # Print the output
        # if output:
        #     print("Output:\n", output)
        # if error:
        #     print("Error:\n", error)

    except paramiko.SSHException as ssh_exception:
        print(f"SSH error: {ssh_exception}")
        raise
    except FileNotFoundError:
        print("Key file not found.")
        raise
    except Exception as e:
        print(f"An error occurred: {e}")
        raise
    finally:
        # Close the client and file objects
        if stdin:
            stdin.close()
        if stdout:
            stdout.close()
        if stderr:
            stderr.close()
        client.close()
        print(f"Connection to {hostname} closed.")
    return output, error


def main():
    """
    Lists images in a Kubernetes cluster and generates a JSON report.

    Example usage:
    Generates a JSON report for management clusters:
    python get_image_refs.py --output image_refs.json --kubeconfig /path/to/kubeconfig
    Generates a JSON report for workload clusters:
    python get_image_refs.py --output image_refs.json --kubeconfig /path/to/kubeconfig --workload-kubeconfig /path/to/workload-kubeconfig

    :param --kubeconfig: Optional. The path to the management cluster kubeconfig file.
    If not provided, the default system kubeconfig will be used.
    :param --workload-kubeconfig: Optional. The path to the workload cluster kubeconfig file
    If not provided, the default system kubeconfig will be used.
    :param --workload-name: Optional. The name of the workload cluster.
    :param --output: Optional. The file path to save the result as JSON.
    If not provided, the result will be printed to the console.
    :param --ssh-key: Optional. Path to SSH key for node authentication.
    If provided, connects to nodes and uses crictl to list containerd images.
    :param --input: Optional. Paths to previous lists to merge with the new output.
    :return: None
    :raises Exception: For any exceptions that may occur during execution.
    """

    print("Started...")

    # Args parsing
    parser = argparse.ArgumentParser(description='Kubernetes cluster images parser')
    parser.add_argument('-k', '--kubeconfig',
                        required=False,
                        default=None,
                        help='Path for the management cluster kubeconfig.')
    parser.add_argument('-w', '--workload-kubeconfig',
                        required=False,
                        help='Path for the management cluster kubeconfig.')
    parser.add_argument('--workload-name',
                        required=False,
                        help='Name of the workload cluster (the script will try to get the kubeconfig from the management cluster).')
    parser.add_argument('-o', '--output',
                        required=False,
                        default=None,
                        help='Directory to dump artifact. Created if it doesn\'t exist')
    parser.add_argument('-i', '--input',
                        nargs='+',
                        required=False,
                        default=None,
                        help='Path to a previous list to merge with the new output.')
    # Crictl related args
    parser.add_argument('-s', '--ssh-key',
                        required=False,
                        default=None,
                        help='Required by crictl - Path to the SSH key for authentication to the nodes.')
    args = parser.parse_args()

    # Validation logic
    if args.workload_name and args.workload_kubeconfig:
        parser.error("You cannot provide both --workload-name and --workload-kubeconfig at the same time.")

    images_set = set()

    # Initialize K8sParser
    k8s_parser = K8sParser(kubeconfig=args.kubeconfig, workload_kubeconfig=args.workload_kubeconfig, workload_name=args.workload_name)

    # Images from pods
    pod_images_dependencies = k8s_parser.get_pods_images_dependencies()
    images_per_unit = k8s_parser.get_images_per_unit(pod_images_dependencies)
    units_per_image = k8s_parser.get_units_per_image(images_per_unit)

    pod_images = pod_images_dependencies.keys()
    images_set.update(pod_images)

    # Images from crictl
    if args.ssh_key:
        hostnames = k8s_parser.get_nodes_ips()
        crictl_images_set = set()
        crictl_outputs, crictl_images_set = get_crictl_images(hostnames,
                                                              args.ssh_key,
                                                              user="node-admin",
                                                              runtime_endpoint="/run/k3s/containerd/containerd.sock",
                                                              crictl_path="/var/lib/rancher/rke2/bin/crictl",
                                                              sudo=True)
        images_set = images_set | crictl_images_set
        print(f"Total images: {len(images_set)}")
        print(f"Images from crictl: {len(crictl_images_set)}")

    # Print number number of images
    print(f"Images from pods: {len(images_set)}")

    # Generate images_ref dictionary
    images_ref = {}
    images_ref['images'] = list(images_set)
    images_ref['units_per_image'] = units_per_image
    images_ref['images_per_unit'] = images_per_unit
    images_ref['images_with_unknown_unit'] = list(images_set - set(images_ref["units_per_image"].keys()))
    images_ref['pod_images_dependencies'] = pod_images_dependencies
    if args.ssh_key:
        images_ref['crictl_images'] = list(crictl_images_set)
        images_ref['images_in_crictl_not_in_pods'] = list(crictl_images_set - images_set)
        images_ref['images_in_pods_not_in_crictl'] = list(images_set - crictl_images_set)

    # Merge with previous list if provided
    if args.input:
        for input_file in args.input:
            try:
                with open(input_file, "r", encoding="utf-8") as in_file:
                    previous_data = json.load(in_file)
                    images_ref = update_images_ref(previous_data, images_ref)
            except Exception as e:
                print(f"Error reading input file {args.input}: {e}")

    # Output to file or stdout
    if args.output:
        with open(args.output, "w", encoding="utf-8") as out_file:
            json.dump(images_ref, out_file, indent=4)
            print(f"Output result to {args.output}")
    else:
        print(json.dumps(images_ref, indent=4))


if __name__ == "__main__":
    main()
