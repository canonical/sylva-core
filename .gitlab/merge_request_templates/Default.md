## What does this MR do and why?

%{first_multiline_commit}

### Related reference(s)

## Test coverage

<!-- Explain which tests have been added for covering the new behavior.
     As a last resort, indicate what kind of manual testing was done. -->

## CI configuration

Below you can choose test deployment variants to run in this MR's CI.

<details><summary> Click to open to CI configuration </summary>

**Legend:**

| Icon | Meaning                  | Available values                                                          |
|------|--------------------------|---------------------------------------------------------------------------|
| ☁   | **Infra Provider**       | `capd`, `capo`, `capm3`                                                   |
| 🚀  | **Bootstrap Provider**   | `kubeadm` (alias `kadm`), `rke2`                                          |
| 🐧  | **Node OS**              | `ubuntu`, `suse`                                                          |
| 🛠  | **Deployment Options**    | `light-deploy`, `dev-sources`, `ha`, `misc`, `maxsurge-0`, `logging`                                       |
| 🎬  | **Pipeline Scenarios**   | [Available scenario list and description](https://gitlab.com/sylva-projects/sylva-core/-/blob/main/.gitlab/README.md?ref_type=heads#scenario-description)  |

<!-- DEPLOYMENT FLAVOR DEFINITION START -->

* [x] 🎬 preview ☁ capd 🚀 kadm 🐧 ubuntu
* [ ] 🎬 preview ☁ capo 🚀 rke2 🐧 suse
* [ ] 🎬 preview ☁ capm3 🚀 rke2 🐧 ubuntu

* [x] ☁ capd 🚀 kadm 🛠 light-deploy 🐧 ubuntu
* [x] ☁ capd 🚀 rke2 🛠 light-deploy 🐧 suse

* [x] ☁ capo 🚀 rke2 🐧 suse
* [x] ☁ capo 🚀 kadm 🐧 ubuntu
* [ ] ☁ capo 🚀 rke2 🎬 rolling-update 🛠 ha 🐧 ubuntu
* [ ] ☁ capo 🚀 kadm 🎬 wkld-k8s-upgrade 🐧 ubuntu
* [ ] ☁ capo 🚀 rke2 🎬 rolling-update-no-wkld 🛠 ha,misc 🐧 suse
* [ ] ☁ capo 🚀 rke2 🎬 sylva-upgrade-from-1.3.x 🛠 ha,misc 🐧 ubuntu

* [x] ☁ capm3 🚀 rke2 🐧 suse
* [x] ☁ capm3 🚀 kadm 🐧 ubuntu
* [ ] ☁ capm3 🚀 kadm 🎬 rolling-update-no-wkld 🛠 ha,misc 🐧 ubuntu
* [ ] ☁ capm3 🚀 rke2 🎬 wkld-k8s-upgrade 🛠 ha 🐧 suse
* [ ] ☁ capm3 🚀 kadm 🎬 rolling-update 🛠 ha 🐧 ubuntu
* [ ] ☁ capm3 🚀 rke2 🎬 sylva-upgrade-from-1.3.x 🛠 misc,ha 🐧 suse
* [ ] ☁ capm3 🚀 kadm 🎬 rolling-update 🛠 ha 🐧 suse

* [x] ☁ capm3 🚀 ck8s 🎬 no-wkld 🛠 light-deploy,k8s-1.31 🐧 ubuntu

<!-- DEPLOYMENT FLAVOR DEFINITION END -->

### Global config for deployment pipelines

* [ ] autorun pipelines                    <!-- AUTORUN  OPTION -->
* [x] allow failure on pipelines           <!-- ALLOW FAILURE OPTION -->
* [ ] record sylvactl events               <!-- SYLVACTL RECORD OPTION -->

Notes:

* Enabling `autorun` will make deployment pipelines to be run automatically without human interaction
* Disabling `allow failure` will make deployment pipelines mandatory for pipeline success.
* if both `autorun` and `allow failure` are disabled, deployment pipelines will need manual triggering but will be blocking the pipeline

</details>

**Be aware:** after configuration change, pipeline is not triggered automatically.
Please run it manually (by clicking the `run pipeline` button in Pipelines tab) or push new code.
