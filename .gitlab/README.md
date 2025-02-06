# Sylva CI - Deployment Pipelines Generation Guide

In Sylva-core, `.gitlab/ci/scripts/generate_deployment_jobs.py` script generates the available deployment pipelines for each merge request.

This document details the script’s functionality and explains how to customize pipelines for your specific needs.

## Developer Workflow

### Basic Usage

When you create a new merge request on Sylva-core, a default list of deployment pipelines appears in the merge request description, with some pipelines pre-selected to run.

You can adjust the pipelines by selecting or deselecting these checkboxes. **Note**: After making changes, click **Run Pipeline** in 'pipelines' tab to apply them.

A maximum of 8 pipelines can be selected at once.

If the default options do not meet your requirements, refer to the **Advanced Usage** section below.

### Advanced Usage

To customize the default pipeline list, edit the merge request description by adding or removing pipelines between the placeholders below:

```markdown
<!-- DEPLOYMENT FLAVOR DEFINITION START -->

* [x] 🎬preview ☁capd 🚀kadm 🐧ubuntu 🛠oci
* [ ] 🎬preview ☁capo 🚀rke2 🐧suse
* [ ] 🎬preview ☁capm3 🚀rke2 🐧ubuntu

* [x] ☁capd 🚀kubeadm 🛠light-deploy 🐧ubuntu
* [ ] ☁capd 🚀rke2 🛠oci,light-deploy 🐧suse

* [ ] ☁capo 🚀rke2 🐧ubuntu
* [ ] ☁capo 🚀kadm 🛠oci 🐧suse
* [ ] ☁capo 🚀rke2 🎬rolling-update 🛠ha 🐧ubuntu
* [ ] ☁capo 🚀rke2 🎬mgmt-rolling-update 🛠ha,misc 🐧suse
* [ ] ☁capo 🚀rke2 🎬sylva-upgrade 🛠misc 🐧ubuntu

* [x] ☁capm3 🚀rke2 🐧suse
* [ ] ☁capm3 🚀kadm 🛠oci 🐧ubuntu
* [ ] ☁capm3 🚀rke2 🎬sylva-upgrade 🛠misc,ha 🐧suse
* [x] ☁capm3 🚀rke2 🎬mgmt-rolling-update 🛠ha,misc 🐧ubuntu
* [ ] ☁capm3 🚀kadm 🎬rolling-update 🛠ha 🐧suse

<!-- DEPLOYMENT FLAVOR DEFINITION END -->
```

#### Pipeline Syntax

Each pipeline entry should adhere to this format:

```markdown
* [ ] ☁<infra_provider> 🚀<bootstrap_provider> 🎬<scenario (optional)> 🛠<options (optional)> 🐧<os>
```

#### Icon Legend

| Icon | Description                  | Values Available                                                                     |
|------|------------------------------|--------------------------------------------------------------------------------------|
| ☁    | **Infrastructure Provider**  | `capd`, `capo`, `capm3`                                                              |
| 🚀    | **Bootstrap Provider**      | `kubeadm` (or `kadm`), `rke2`                                                        |
| 🐧    | **Operating System**        | `ubuntu`, `suse`                                                                     |
| 🎬    | **Pipeline Scenarios**      | `rolling-update`, `mgmt-rolling-update`, `k8s-upgrade`, `mgmt-sylva-upgrade`, `sylva-upgrade`, `sylva-upgrade-from-x.x.x` `simple-update`, `preview` |
| 🛠    | **Deployment Options**      | `light-deploy`, `dev-sources`, `ha`, `misc`                                                   |

**Note**: You can freely combine these components, but certain combinations may be incompatible (e.g., `capd` deployments do not support updates). The script does not currently manage all incompatibility rules.

## Script Documentation

The script runs automatically within the CI pipeline.

### Inputs and Environment Variables

The script uses several environment variables and configuration files to define deployment specifications:

- **ALLOWED_DEPLOYMENT_INFRA**: Comma-separated list of allowed deployment infrastructures (default: `capd,capo,capm3`).
- **ALLOWED_DEPLOYMENT_SCENARIO**: Comma-separated list of permitted deployment scenarios (default: `simple-update,rolling-update,mgmt-rolling-update,rolling-update,k8s-upgrade,sylva-upgrade,nightly,preview`).
- **DEPLOY_CHILD_PIPELINE_COUNT_LIMIT**: Maximum number of child pipelines allowed for a merge request (default: `8`).
- **DEPLOYMENT_DESCRIPTION_OVERRIDE**: CI variable to override the CI configuration when needed.
- **DEPLOYMENT_DESCRIPTION**: Specifies deployment options, containing the key for schedule pipeline definitions.
- **CI_MERGE_REQUEST_DESCRIPTION**: Description of the merge request.
- **CI_MERGE_REQUEST_LABELS**: GitLab merge request labels (`~ci-allow-failure` label allows pipelines to fail).

### Configuration Files

- **PREDEFINED_PIPELINES_CONFIG_FILE**: YAML file for scheduled pipeline configurations (default: `.gitlab/ci/configuration/predefined-pipelines-config.yaml`).
- **DEFAULT_MR_DESCRIPTION**: Default merge request description file (default: `.gitlab/merge_request_templates/Default.md`).
- **TEMPLATE_FILE**: Base YAML deployment file (default: `.gitlab/ci/deployments-base.yml`), containing scenario definitions.
