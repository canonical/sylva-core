#!/usr/bin/env python
import re
import yaml
import requests


class IgnoreTagsLoader(yaml.Loader):
    """Custom YAML loader to ignore !reference tags."""
    def ignore_tag(self, tag, node):
        return self.construct_sequence(node)


def ignore_reference_tag(loader, node):
    """Ignore !reference tags in YAML content."""
    return loader.construct_sequence(node)


IgnoreTagsLoader.add_constructor('!reference', ignore_reference_tag)


def fetch_yaml_content(url):
    """Fetch YAML content from a given URL."""
    response = requests.get(url)
    response.raise_for_status()
    return response.text


def generate_k8s_version_map(content):
    """Generate Kubernetes version map from .gitlab-ci.yml content."""
    yaml_content = yaml.load(content, Loader=IgnoreTagsLoader)

    rke2_versions = yaml_content['.rke2_settings']['parallel']['matrix'][0]['K8S_VERSION']
    kubeadm_versions = yaml_content['.kubeadm_settings']['parallel']['matrix'][0]['K8S_VERSION']

    version_pairs = {}
    rke2_related_charts = ["ingress-nginx", "calico", "calico-crd"]
    charts_version_mapping = {chart: {} for chart in rke2_related_charts}

    for rke2_version in rke2_versions:
        major_minor = re.match(r'(\d+\.\d+)', rke2_version).group(1)
        kubeadm_version = next(
            (v for v in kubeadm_versions if v.startswith(major_minor)),
            None
        )
        if kubeadm_version:
            version_pairs[major_minor] = {
                'rke2': f'v{rke2_version}',
                'kubeadm': f'v{kubeadm_version}'
            }

    output = "_internal:\n  k8s_version_map:\n"
    for major_minor, versions in sorted(version_pairs.items()):
        key = f'"{major_minor}"'
        output += f"  {key}: \'{{{{ .Values.cluster.capi_providers.bootstrap_provider | eq \"cabpr\" | ternary \"{versions['rke2']}\" \"{versions['kubeadm']}\" }}}}'\n" # noqa E501

        rke2_chart_version_url = f"https://raw.githubusercontent.com/rancher/rke2/refs/tags/{versions['rke2']}/charts/chart_versions.yaml"
        rke2_yaml_content = fetch_yaml_content(rke2_chart_version_url)
        rke2_yaml_content = yaml.load(rke2_yaml_content, Loader=IgnoreTagsLoader)

        for data in rke2_yaml_content['charts']:
            for chart in rke2_related_charts:
                if chart in data['filename']:
                    charts_version_mapping[chart][major_minor] = data['version']

    result = convert_to_helm_chart_format(charts_version_mapping)
    output += yaml.dump(result)

    return output


def convert_to_helm_chart_format(data):
    """Convert chart version mapping to Helm chart format."""
    output = {"units": {}}
    for main_key, versions in data.items():
        output["units"][main_key] = {"helm_chart_version": {}}

        sorted_versions = sorted(versions.items())

        current_index = 0
        while current_index < len(sorted_versions):
            major_minor, version = sorted_versions[current_index]
            condition = f">={major_minor}.0"

            next_index = current_index + 1
            while next_index < len(sorted_versions) and sorted_versions[next_index][1] == version:
                next_index += 1

            if next_index < len(sorted_versions):
                next_major_minor = sorted_versions[next_index][0]
                condition += f",<{next_major_minor}.0"

            output["units"][main_key]["helm_chart_version"][version] = (
                f'{{{{ include "k8s-version-match" (tuple "{condition}" .Values._internal.k8s_version) }}}}'
            )

            current_index = next_index

    return output


def generate_sylva_diskimagebuilder_images(description):
    """Generate Sylva DiskImageBuilder images from release notes description."""
    output = "sylva_diskimagebuilder_images:\n"
    image_names = set()
    for line in description.split('\n'):
        matches = re.findall(r'oci://registry\.gitlab\.com/sylva-projects/sylva-elements/diskimage-builder/([^:]+)', line)
        image_names.update(matches)

    for image_name in sorted(image_names, reverse=True):
        output += f"  {image_name}:\n"
        output += "    os_images_oci_registry: sylva\n"
    return output


def main(release):
    """Main function to generate K8s version map and Sylva DiskImageBuilder images."""
    diskimage_build_project_id = 43786055

    gitlab_ci_url = f"https://gitlab.com/sylva-projects/sylva-elements/diskimage-builder/-/raw/{release}/.gitlab-ci.yml?ref_type=tags"
    ci_content = fetch_yaml_content(gitlab_ci_url)

    release_notes_url = f"https://gitlab.com/api/v4/projects/{diskimage_build_project_id}/releases/{release}"
    release_notes = requests.get(release_notes_url).json().get('description', '')

    k8s_versions = generate_k8s_version_map(ci_content)
    image_info = generate_sylva_diskimagebuilder_images(release_notes)

    print(k8s_versions)
    print(image_info)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python script.py <release>")
        sys.exit(1)

    main(sys.argv[1])
