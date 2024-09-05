#!/usr/bin/python3
#
# This script allows parsing the output of 'kustomize build' piped into it
# and extracting values from the sylva-units HelmRelease on different paths.

import sys
import yaml
import base64
from optparse import OptionParser
from yamlMerge import recursive_dict_combine


# Extract HelmRelease/sylva-units values from different paths based on values_path
def extract_helm_release_values_from(helm_release_manifest, values_path):
    resources = []
    if values_path == ".spec.valuesFrom":
        for item in helm_release_manifest.get("spec", {}).get("valuesFrom", []):
            kind = item["kind"]
            name = item["name"]
            values_key = item.get("valuesKey", None)
            if kind and name:
                resources.append({"kind": kind, "name": name, "valuesKey": values_key})
    elif values_path == ".spec.values":
        values = helm_release_manifest.get("spec", {}).get("values", {})
        resources = ({"values": values})
    elif values_path == ".spec.chart.spec.valuesFiles":
        values_files = helm_release_manifest.get("spec", {}).get("chart", {}).get("spec", {}).get("valuesFiles", [])
        resources = ({"valuesFiles": values_files})
    return resources


def do_nothing(*args, **xargs):
    pass


def main(values_path):
    # Load the YAML documents from standard input
    kustomize_yaml = list(yaml.safe_load_all(sys.stdin))
    if kustomize_yaml:
        helm_release_manifest_doc = None
        # Search for the HelmRelease manifest in the list of YAML documents
        for yaml_doc in kustomize_yaml:
            if yaml_doc.get("kind") == "HelmRelease" and yaml_doc.get("metadata", {}).get("name") == "sylva-units":
                helm_release_manifest_doc = yaml_doc
                break

        if helm_release_manifest_doc:
            if values_path == ".spec.valuesFrom":
                result = {}  # Initialize result as an empty dictionary
                secrets_configmaps_data = []  # Initialize list to store YAML contents of Secrets and ConfigMaps
                helm_release_values_from = extract_helm_release_values_from(helm_release_manifest_doc, values_path)
                if helm_release_values_from:
                    # Very importantly, we get the contents of resources found in HelmRelease.spec.valuesFrom
                    # and merge in the order they were found
                    for item in helm_release_values_from:
                        values_key = item.get("valuesKey", "values")
                        for yaml_doc in kustomize_yaml:
                            if (
                                yaml_doc.get("kind") == item["kind"] and
                                yaml_doc.get("metadata", {}).get("name") == item["name"]
                            ):
                                data = yaml_doc.get("data", {}).get(values_key, "")
                                if item["kind"] == "Secret":
                                    data = base64.b64decode(data).decode("utf-8")
                                parsed_data = yaml.safe_load(data)
                                if parsed_data is None:
                                    continue  # Ignore empty files
                                elif not isinstance(parsed_data, dict):
                                    print(f'Error: data provided for {item["kind"]}/{item["name"]}'
                                          f'is not a dict (data: {parsed_data})')
                                    sys.exit(1)
                                else:
                                    secrets_configmaps_data.append(parsed_data)
                    # Merge YAML contents of Secrets and ConfigMaps
                    while secrets_configmaps_data:
                        result = recursive_dict_combine(result, secrets_configmaps_data.pop(0), do_nothing)

                    print(yaml.dump(result))  # Print merged contents as YAML

            elif values_path == ".spec.values" or values_path == ".spec.chart.spec.valuesFiles":
                print(yaml.dump(extract_helm_release_values_from(helm_release_manifest_doc, values_path)))
        else:
            print("HelmRelease manifest not found.")


if __name__ == "__main__":
    parser = OptionParser(usage="""

%prog [options]

Program reads manifests from stdin and attempts to return sylva-units values, based on the --values-path option for:
 - HelmRelease.spec.valuesFrom, gets the contents of objects from this list (if referenced objects are present in \
   provided stdin manifests) and merges them (emulating Helm behavior when merging values), then outputs that
 - HelmRelease.spec.values, outputs the dictionary of values
 - HelmRelease.spec.chart.spec.valuesFiles, outputs the list of files
    """)
    parser.add_option("--values-path", choices=[".spec.valuesFrom", ".spec.values", ".spec.chart.spec.valuesFiles"],
                      default=".spec.valuesFrom",
                      help='path to extract values from HelmRelease')
    parser.add_option("-d", "--debug", action="store_true",
                      default=False,
                      help='debug')

    (options, args) = parser.parse_args()

    values_path = options.values_path

    if options.debug:
        debug_fn = print
    else:
        debug_fn = do_nothing

    main(values_path)
