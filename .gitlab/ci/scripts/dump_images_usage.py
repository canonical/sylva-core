from kubernetes import client, config
from pathlib import Path
import subprocess
import yaml
import logging
import argparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Interesting KIND which uses container images
KIND_WITH_IMAGES_TEMPLATE = ['Deployment', 'Job', 'ReplicaSet', 'StatefulSet']
KIND_WITH_IMAGES_WITHOUT_TEMPLATE = ['Pod']
KIND_WITH_IMAGES = KIND_WITH_IMAGES_TEMPLATE + KIND_WITH_IMAGES_WITHOUT_TEMPLATE

parser = argparse.ArgumentParser(description='Kubernetes cluster images parser')
parser.add_argument('--kubeconfig',
                    dest='kubeconfig',
                    required=True,
                    help='kubeconfig path.')
parser.add_argument('--crictl-images',
                    dest='crictlimages',
                    required=False,
                    help='crictl images file path.')
parser.add_argument('--output-dir',
                    dest='outputdir',
                    required=True,
                    help='Directory to dump artifcat. Created if it doesn\'t exist')

args = parser.parse_args()


class K8sParser(object):
    def __init__(self, kubeconfig, outputdir, crictlimages=None):
        if Path(kubeconfig).exists() and Path(kubeconfig).is_file():
            self.kubeconfig = kubeconfig
            config.load_config(config_file=kubeconfig)
        else:
            raise Exception("Kubeconfig error")
        if crictlimages:
            if Path(crictlimages).exists() and Path(crictlimages).is_file():
                self.crictl_images_ref = crictlimages
            else:
                raise Exception("crictl images file error")
        else:
            self.crictl_images_ref = None
        if Path(outputdir).exists():
            if Path(outputdir).is_dir():
                self.output_dir = outputdir
            else:
                raise Exception(f"--output-dir points to an existing file {outputdir}")
        else:
            Path(outputdir).mkdir()
            self.output_dir = outputdir

        # Get all API preferred versions
        api = client.ApisApi()
        api_versions = api.get_api_versions()
        self.api_versions = {}
        for group in api_versions.groups:
            self.api_versions[group.name] = group.preferred_version.version
        # API CORE : used to list nodes, namespaces
        self.api_core = client.CoreV1Api()
        # API : used to list/get Custom resources
        self.api = client.CustomObjectsApi()
        # images will store informations about images (repoDigest, aliases, kustomizations)
        self.images = []
        # namespaces: list of namespaces
        self.namespaces = [ns.metadata.name for ns in (self.api_core.list_namespace()).items]

    def get_kustomizations(self):
        """
            returns a list of kustomizations for all namespaces
        """
        kustomizations = []
        group = "kustomize.toolkit.fluxcd.io"
        for ns in self.namespaces:
            ks = self.api.list_namespaced_custom_object(
                group=group,
                version=self.api_versions[group],
                namespace=ns,
                plural="kustomizations"
            )
            kustomizations += ks['items']
        return kustomizations

    def pluralize(self, kind):
        """
            return plural of a kind in lowercase
        """
        if kind[-1:] == 's':
            plural = kind + 'es'
        elif kind[-1:] == 'y':
            plural = kind[:-1] + 'ies'
        else:
            plural = kind + 's'
        return plural.lower()

    def get_resource_details(self, group, kind, name, namespace=None):
        """
            return details of a resource either namespaced or not
        """
        resource_details = None
        if group:
            version = self.api_versions[group]
            params = dict(
                    group=group,
                    plural=self.pluralize(kind),
                    version=version,
                    name=name
                )
            if namespace:
                try:
                    resource_details = self.api.get_namespaced_custom_object(
                        namespace=namespace,
                        **params)
                except Exception as E:
                    logger.error(f"{str(E)}")
            else:
                try:
                    resource_details = self.api.get_cluster_custom_object(
                        **params)
                except Exception as E:
                    logger.error(f"{params} {str(E)}")
            return resource_details
        else:
            # there is no generic method to call for Core resource
            if kind == 'Namespace':
                # specific case of namespaces
                method_name = 'read_namespace'
                args = dict(name=namespace)
            else:
                # build the method name dynamically based on kind
                method_name = 'read_namespaced_'
                method_name += ''.join(['_' + c.lower() if c.isupper() else c for c in kind]).lstrip('_')
                args = dict(namespace=namespace, name=name)
            try:
                method = getattr(self.api_core, method_name)
                resource = method(**args)
            except Exception as E:
                logger.error(f"{method_name}({args})   {str(E)}")
                return None
            return dict(
                kind=resource.kind,
                metadata=dict(
                    name=resource.metadata.name,
                    namespace=resource.metadata.namespace,
                    uid=resource.metadata.uid))

    def get_flux_tree_for_kustomization(self, namespace, kustomization):
        """
            return flux tree of a kustomization, with children resources
            format is the following:
            {
                'resource': {
                    'GroupKind': {
                        'Group': 'kustomize.toolkit.fluxcd.io',
                        'Kind': 'Kustomization'
                    },
                    'Name': 'cluster',
                    'Namespace': 'kubeadm-capm3-virt'
                },
                'resources': [
                    {
                        'resource': {
                            'GroupKind': {
                                'Group': '',
                                'Kind': 'Secret'
                            },
                            'Name': 'helm-unit-values-cluster-639a499',
                            'Namespace': 'kubeadm-capm3-virt'
                        }
                    },
                    {
                        'resource': {
                            'GroupKind': {
                                'Group': 'helm.toolkit.fluxcd.io',
                                'Kind': 'HelmRelease'
                            },
                            'Name': 'cluster',
                            'Namespace': 'kubeadm-capm3-virt'
                        },
                        ...
                ]
            }
        """
        flux_cli = ['flux', 'tree', '-n', namespace, 'kustomization', kustomization, '-o', 'yaml']
        if self.kubeconfig:
            flux_cli += ['--kubeconfig', self.kubeconfig]
        result = subprocess.run(
            flux_cli,
            stdout=subprocess.PIPE)
        return yaml.safe_load(result.stdout.decode('utf-8'))

    def discover_child_resource(self, resource):
        """
            return information (name, ns, group, kind, uid) about a resource described
            by resource arg (part of flux tree kustomization) and its children resources if any

            return example (here an HelmRelease with children resources):
            {
                group: helm.toolkit.fluxcd.io
                kind: HelmRelease
                name: vault-config-operator
                namespace: sylva-system
                resources:
                - group: rbac.authorization.k8s.io
                  kind: ClusterRole
                  name: vault-config-operator-manager-role
                  namespace: ''
                  resources: []
                  uid: e66a55de-7ee3-4f93-8339-d7eeabd449f5
                - group: rbac.authorization.k8s.io
                  kind: ClusterRole
                  name: vault-config-operator-metrics-reader
                  namespace: ''
                  resources: []
                  uid: 7be2cea3-1731-4b2d-ad18-df4d7e5cb345
            }
        """
        group = resource['resource']['GroupKind']['Group']
        kind = resource['resource']['GroupKind']['Kind']
        child_details = parser.get_resource_details(
            group=group,
            kind=kind,
            name=resource['resource']['Name'],
            namespace=resource['resource']['Namespace'])
        if child_details:
            children = []
            for child in resource.get('resources', []):
                res = self.discover_child_resource(child)
                if res:
                    children.append(res)
            result = dict(
                group=group,
                kind=child_details['kind'],
                name=child_details['metadata']['name'],
                uid=child_details['metadata']['uid'],
                namespace=child_details['metadata'].get('namespace', ''),
                resources=children)
            return result
        else:
            return None

    def discover_ks_resources(self):
        """
            Parse result of flux tree kustomization to get detail of each
            children resource.

            save kustomization details into a list with following format:
            [
                {
                    "name": "myKustomization",
                    "namespace": "myNameSpace",
                    "udi": "kustomization-uid",
                    "resources": [
                        {
                            "kind": "resourceKind",
                            "name": "resourceName",
                            "namespace": "resourceNameSpace",
                            "udi": "resource-uid",
                            "resources: [
                                ...
                            ]
                        }
                    ]
                }
            ...
            ]
        """
        logger.info(" >>> Discover Kustomizations and children resources")
        ks_ref = []
        kustomizations = []
        for k in parser.get_kustomizations():
            kustomizations.append(
                dict(
                    name=k['metadata']['name'],
                    namespace=k['metadata']['namespace'],
                    kind=k['kind'],
                    uid=k['metadata']['uid']))
        for k in kustomizations:
            flux_tree = parser.get_flux_tree_for_kustomization(k['namespace'], k['name'])
            new_ks = dict(name=k['name'], namespace=k['namespace'], uid=k['uid'], resources=[])
            children_resources = []
            if flux_tree:
                for child_resource in flux_tree.get('resources', []):
                    child = self.discover_child_resource(child_resource)
                    if child:
                        children_resources.append(child)
            new_ks['resources'] = children_resources
            ks_ref.append(new_ks)
            logger.info(f" - Kustomization: {k['name']} has {len(children_resources)} resource(s)")
        self.ks_resources = ks_ref
        with open(f'{self.output_dir}/kustomizations.yaml', 'w') as f:
            f.write(yaml.dump(ks_ref))
        logger.info(" >>> Discover Kustomizations and children resources: done")

    def discover_images_used_by_ks_resources(self, img_filename, ks_filename):
        """
            parse all kustomizations to inspect children resources if any are using container image
        """
        logger.info(" >>> Discover images used by kustomizations")
        self.img_per_ks = {}
        nl = '\n'
        import time
        for kustomization in self.ks_resources:
            ks_name = f"{kustomization['namespace']}/{kustomization['name']}"
            self.img_per_ks[ks_name] = []
            for resource in kustomization['resources']:
                self.img_per_ks[ks_name] += self.discover_images_used_by_resource(resource)
                self.img_per_ks[ks_name] = list(set(self.img_per_ks[ks_name]))
            if len(self.img_per_ks[ks_name]):
                logger.info(
                    f" - kustomization: {ks_name} uses:{nl} "
                    f"{nl.join(['-'+img for img in self.img_per_ks[ks_name]])} ")
                time.sleep(1)
        with open(f"{self.output_dir}/{img_filename}", 'w') as f:
            f.write(yaml.safe_dump(self.img_per_ks))
        with open(f"{self.output_dir}/{ks_filename}", 'w') as f:
            f.write(yaml.safe_dump(self.ks_resources))

    def discover_images_used_by_resource(self, resource):
        """
            inspect a resource to see if any images are used and return a list of those images
        """
        images = []
        if resource['kind'] in KIND_WITH_IMAGES:
            res = self.get_resource_details(
                group=resource['group'],
                kind=resource['kind'],
                name=resource['name'],
                namespace=resource.get('namespace', '')
            )
            if resource['kind'] in KIND_WITH_IMAGES_TEMPLATE:
                template_spec = res['spec']['template']['spec']
                images += [container['image'] for container in template_spec['containers']]
                images += [container['image'] for container in template_spec.get('initContainers', [])]
            if resource['kind'] in KIND_WITH_IMAGES_WITHOUT_TEMPLATE:
                images += [container['image'] for container in res['spec']['containers']]
                images += [container['image'] for container in res['spec'].get('initContainers', [])]
        elif resource['kind'] in ['HelmRelease']:
            for _resource in resource['resources']:
                images += self.discover_images_used_by_resource(_resource)
        else:
            logger.debug(f"no image used in resource of kind {resource['kind']}")
        return images

    def discover_nodes_images(self):
        """
            update self.images with node.status.images
        """
        logger.info(" >>> Discover nodes images")
        nodes = self.api_core.list_node()
        for node in nodes.items:
            for img in node.status.images:
                repoDigest = None
                aliases = []
                for _str in img.names:
                    if 'sha256' in _str:
                        repoDigest = _str
                    else:
                        aliases.append(_str)
                if repoDigest:
                    existing_img = [_img for _img in self.images if _img['repoDigest'] == repoDigest]
                    if existing_img:
                        # update reference
                        for alias in aliases:
                            if alias not in existing_img[0]['aliases']:
                                existing_img[0]['aliases'].append(alias)
                                logger.info(f" - {alias}")
                            else:
                                logger.info(f" - {alias} exists already in reference")
                    else:
                        self.images.append(dict(repoDigest=repoDigest, aliases=aliases, kustomizations=[]))
        logger.info(" >>> Discover nodes images: done")

    def merge_images_info(self, filename):
        for ks in self.img_per_ks:
            self.update_image(ks, self.img_per_ks[ks])
        with open(f"{self.output_dir}/{filename}", 'w') as f:
            f.write(yaml.dump(self.images))

    def update_image(self, ks_name, ks):
        for img_alias in ks:
            img_alias_found_in_images = False
            for img in self.images:
                for alias in img['aliases']:
                    if len(img_alias) <= len(alias):
                        if alias[-len(img_alias):] == img_alias:
                            img['kustomizations'].append(ks_name)
                            img_alias_found_in_images = True
                            break
            if not img_alias_found_in_images:
                self.images.append(dict(repoDigest='unknown', aliases=[img_alias], kustomizations=[ks_name]))

    def discover_crictl_images(self, filename):
        """
            initialize self.images with information coming from crictl images
        """
        logger.info(f" >>> Parse crictl-image references {filename}")
        with open(filename, 'r') as f:
            raw_data = yaml.safe_load(f.read())
            for img in raw_data['images']:
                self.images.append(
                    dict(
                        repoDigest=img['repoDigests'][0],
                        aliases=img['repoTags'],
                        kustomizations=[]))
                logger.info(f" - {img['repoTags'][0]}")

    def discover_images(self):
        """
            main process
        """
        if self.crictl_images_ref:
            self.discover_crictl_images(self.crictl_images_ref)
        self.discover_nodes_images()
        self.discover_ks_resources()
        self.discover_images_used_by_ks_resources('images_per_ks.yaml', 'kustomizations.yaml')
        self.merge_images_info('ref_images.yaml')


parser = K8sParser(
    kubeconfig=args.kubeconfig,
    crictlimages=args.crictlimages,
    outputdir=args.outputdir)
parser.discover_images()
