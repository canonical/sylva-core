#!/usr/bin/env python3

"""
This script is used to parse units configuration and produce piece of documentation
"""

import argparse
import os
import re
import sys
import yaml

SCRIPT_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
ROOT_DIR = os.path.abspath(f"{SCRIPT_DIR}/..")
CHART_DIR = os.path.abspath(f"{ROOT_DIR}/charts/sylva-units")
SYLVA_UNITS_VALUES_FILE = f"{CHART_DIR}/values.yaml"
SYLVA_BOOTSTRAP_UNITS_VALUES_FILE = f"{CHART_DIR}/bootstrap.values.yaml"
SYLVA_MGMT_UNITS_VALUES_FILE = f"{CHART_DIR}/management.values.yaml"
SYLVA_WC_UNITS_VALUES_FILE = f"{CHART_DIR}/workload-cluster.values.yaml"
SYLVA_UNITS_VALUES_FILE = f"{CHART_DIR}/values.yaml"
TARGET_DOC_FILE = f"{CHART_DIR}/units-description.md"


def get_or_empty(dict, *keys):
    try:
        result = dict
        for k in keys:
            result = result[k]
        return result
    except Exception:
        return ""


def read_yaml_files(paths):
    files_concatenated_content = ""
    for path in paths:
        with open(path, 'r') as f:
            content = f.read().strip("\n---")
        files_concatenated_content += "\n---\n" + content
    return list(yaml.safe_load_all(files_concatenated_content))


def get_version_and_source(values, unit_name, unit):

    helmrelease_spec = get_or_empty(unit, "helmrelease_spec")
    if helmrelease_spec:
        source_type = "Helm"
    else:
        source_type = "Kustomize"

    unit_internal = get_or_empty(unit, "info", "internal")
    if unit_internal:
        return {"version": "N/A", "source_url": "", "source_type": source_type}

    forced_version = get_or_empty(unit, "info", "version")
    if forced_version:
        return {"version": forced_version, "source_url": "", "source_type": source_type}

    helm_chart_versions = get_or_empty(unit, "helm_chart_versions")
    if helm_chart_versions:
        version = ", ".join([str(k) for k in helm_chart_versions.keys()])
        helm_repo_url = get_or_empty(unit, "helm_repo_url")
        return {"source_url": helm_repo_url, "version": version, "source_type": source_type}

    helmrelease_spec_version = get_or_empty(unit, "helmrelease_spec", "chart", "spec", "version")
    if helmrelease_spec_version:
        helm_repo_url = get_or_empty(unit, "helm_repo_url")
        return {"source_url": helm_repo_url, "version": helmrelease_spec_version, "source_type": source_type}

    url = ""
    version = ""

    repo = get_or_empty(unit, "repo")
    if repo:
        url = get_or_empty(values, "source_templates", repo, "spec", "url")
        ref = get_or_empty(values, "source_templates", repo, "spec", "ref")
        if not ref:
            raise Exception(f"unit {unit_name} / repo {repo}, no spec.ref")
        tag = ref.get("tag")
        if tag:
            version = tag
        else:
            version = ref.get("branch") or ref.get("commit")
            if not version:
                raise Exception(f"unit {unit_name} / repo {repo}, spec.ref has neither tag, commit or branch (??)")

    # for units that are using "repo: sylva-core", if kustomization_spec.path is defined
    # we can infer source URL and version from the kustomization definition
    # (in that case the 'version' and 'url' found above would not matter)
    if repo == "sylva-core" and not get_or_empty(unit, "info", "internal"):  # (if repo is sylva-core and 'internal' is False or unspecified)
        kustomize_unit_path = get_or_empty(unit, "kustomization_spec", "path")
        if kustomize_unit_path:
            if '{{' in kustomize_unit_path:
                if kustomization_path := get_or_empty(unit, "info", "kustomization_path"):
                    kustomize_unit_path = kustomization_path
                else:
                    print(f"unit {unit_name} has a templatized kustomization path: {kustomize_unit_path}")
                    print(f" this isn't supported by this tool")
                    print(f" you need to set the path manually with units.{unit_name}.info.kustomization_path")
            kustomize_unit_version_source = search_version_in_kustomize_unit_files(kustomize_unit_path)
            if kustomize_unit_version_source:
                url = kustomize_unit_version_source["source"]
                version = kustomize_unit_version_source["version"]
            elif get_or_empty(unit, "info", "internal") == "":
                # if internal wasn't specified at all, we don't know what the user wants
                raise Exception(f"kustomize-based unit {unit_name}: 'info.internal' not set, implicitly False, "
                                f"but no source URL or version could be guessed. "
                                f"If this unit is fully defined in sylva-core then you need to set "
                                f"'info.internal: true', or, if this unit relies on something upstream we "
                                f"need to find out why the upstream URL and version aren't detected under {kustomize_unit_path}.")
            elif get_or_empty(unit, "info", "internal") is False:
                # if "internal: false" was specified, we throw an error
                raise Exception(f"kustomize-based unit {unit_name}: 'info.internal: true' but no source URL or version could "
                                f"be guessed from the kustomization definition under {kustomize_unit_path}.")

    return {"source_url": url, "version": version, "source_type": source_type}


def search_version_in_kustomize_unit_files(kustomize_unit_path):

    kustomize_unit_files = [
        os.path.join(ROOT_DIR, path, file)
        for path, subdirs, files in os.walk(kustomize_unit_path)
        for file in files
        if file.endswith('.yaml') or file.endswith('.yml')
    ]
    yaml_objects = read_yaml_files(kustomize_unit_files)

    possible_paths = [
        "kind=Kustomization/resources/0",
        "kind=Kustomization/resources/1",
        ]
    possible_regexp = [
        r"(?:ref=|/)(v?[\d.]+(?:[\w.-]+)?)(?:/|$)",
    ]
    for path in possible_paths:
        yaml_focus = yaml_objects
        try:
            for step in path.split("/"):
                if "=" in step:
                    [key, value] = step.split("=")
                    yaml_focus = [elem for elem in yaml_focus if key in elem and elem[key] == value]
                    if len(yaml_focus) == 1:
                        yaml_focus = yaml_focus[0]
                elif step.isdigit():
                    yaml_focus = yaml_focus[int(step)]
                else:
                    yaml_focus = yaml_focus[step]

            for regexp in possible_regexp:
                r = re.compile(regexp)
                try:
                    version = r.search(str(yaml_focus)).groups()[0]
                    return {
                        "source": str(yaml_focus),
                        "version": version,
                    }
                except Exception:
                    continue
        except Exception:
            continue


def generate_units_metadata():
    units_data = dict()
    main_values = read_yaml_files([SYLVA_UNITS_VALUES_FILE])[0]
    main_units = main_values["units"]
    units = main_units

    bootstrap_values = read_yaml_files([SYLVA_BOOTSTRAP_UNITS_VALUES_FILE])[0]
    bootstrap_units = bootstrap_values["units"]
    for unit_name, unit in bootstrap_units.items():
        if unit_name not in main_units.keys():
            units[unit_name] = unit

    mgmt_values = read_yaml_files([SYLVA_MGMT_UNITS_VALUES_FILE])[0]
    mgmt_units = mgmt_values["units"]
    for unit_name, unit in mgmt_units.items():
        if unit_name not in main_units.keys():
            units[unit_name] = unit

    wc_values = read_yaml_files([SYLVA_WC_UNITS_VALUES_FILE])[0]
    wc_units = wc_values["units"]
    for unit_name, unit in wc_units.items():
        if unit_name not in main_units.keys():
            units[unit_name] = unit

    units_data = []
    for unit_name, unit in units.items():
        try:
            version_and_source = get_version_and_source(main_values, unit_name, unit)
            units_data.append(
                {
                    "name": unit_name,
                    "description": get_or_empty(unit, "info", "description"),
                    "details": get_or_empty(unit, "info", "details"),
                    "maturity": get_or_empty(unit, "info", "maturity"),
                    "internal": get_or_empty(unit, "info", "internal"),
                    "hidden": get_or_empty(unit, "info", "hidden"),
                    "source_url": version_and_source["source_url"],
                    "source_type": version_and_source["source_type"],
                    "version": version_and_source["version"],
                }
            )
            if version_and_source["source_url"]:
                units_data[-1]["source"] = f"[{version_and_source['source_type']}]({version_and_source['source_url']})"
            else:
                units_data[-1]["source"] = version_and_source["source_type"]
        except Exception as e:
            print(f"Failed to generate documentation for unit {unit_name}:")
            raise
    return units_data


def sort_by_name(unit):
    return unit["name"]


def sort_by_maturity(unit):
    maturity_weight = {
        "core-component": "A",
        "stable": "B",
        "beta": "C",
        "experimental": "C",
        "": "Z",
    }
    return f"{maturity_weight[unit['maturity']]}{unit['name']}"


def convert_to_markdown_table(units, headers, sort_function=sort_by_name):
    header_md_lines = ["| " + " | ".join(headers) + " |"]
    header_md_lines += ["| " + " | ".join([':-----'] * len(headers)) + " |"]
    table_md_lines = []
    units.sort(key=sort_function)
    for unit in units:
        if unit.get("hidden", False):
            continue
        items = [str(unit[key]).strip().replace("\n", "<br/>") for key in headers]
        table_md_lines.append("| " + " | ".join(items) + " |")
    md_content = "<!-- markdownlint-disable MD044 -->\n"
    md_content += "\n".join(header_md_lines + table_md_lines)
    md_content += "\n"
    return md_content


def generate_external_units_version_maturity():
    units_data = generate_units_metadata()
    units_data_without_internals = [unit for unit in units_data if unit["internal"]]
    headers = ["name", "description", "maturity", "source", "version"]
    return convert_to_markdown_table(units_data_without_internals, headers, sort_by_maturity)


def generate_units_description():
    units_data = generate_units_metadata()
    headers = ["name", "description", "details"]
    return convert_to_markdown_table(units_data, headers)


def generate_full_md_table():
    units_data = generate_units_metadata()
    for unit in units_data:
        if unit.get("hidden", False):
            continue
        unit["name"] = f"**{unit['name']}**"
        unit["full description"] = f"{unit['description']}"
        if unit['details']:
            unit["full description"] += f"<br/><br/>{unit['details']}"
    headers = ["name", "full description", "maturity", "internal", "source", "version"]
    return convert_to_markdown_table(units_data, headers, sort_by_maturity)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Sylva units documentation generator",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "doc_format",
        help="Which kind of documentation to generate",
        nargs='?',
        choices=["check", "components-versions", "units-description"],
    )
    args = parser.parse_args()

    if args.doc_format is None:
        with open(TARGET_DOC_FILE, 'w') as f:
            f.write(generate_full_md_table())

    if args.doc_format == "check":
        expected = generate_full_md_table()
        with open(TARGET_DOC_FILE, 'r') as f:
            actual = f.read()
        if expected != actual:
            FAIL = '\033[91m'
            END = '\033[0m'
            message = f"{FAIL}[ERROR]{END} {os.path.relpath(TARGET_DOC_FILE, ROOT_DIR)} is not up to date \n"
            message += f"Please run `{os.path.relpath(sys.argv[0], ROOT_DIR)}` before pushing commit"
            print(message, file=sys.stderr)
            sys.exit(1)

    # exemples of units data formatting
    if args.doc_format == "components-versions":
        print(generate_external_units_version_maturity())
    if args.doc_format == "units-description":
        print(generate_units_description())
