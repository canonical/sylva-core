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
| 🛠  | **Deployment Options**    | `light-deploy`, `oci`, `ha`, `misc`                                       |
| 🎬  | **Pipeline Scenarios**   | `rolling-update`, `mgmt-rolling-update`, `k8s-upgrade`, `sylva-upgrade`, `sylva-upgrade-from-x.x.X`, `simple-update`, `preview`, `nightly` |

<!-- DEPLOYMENT FLAVOR DEFINITION START -->

* [ ] 🎬preview ☁capd 🚀kadm 🐧ubuntu 🛠oci
* [ ] 🎬preview ☁capo 🚀rke2 🐧suse
* [ ] 🎬preview ☁capm3 🚀rke2 🐧ubuntu

* [x] ☁capd 🚀kubeadm 🛠light-deploy 🐧ubuntu
* [x] ☁capd 🚀rke2 🛠oci,light-deploy 🐧suse

* [x] ☁capo 🚀rke2 🛠oci 🐧suse
* [x] ☁capo 🚀kadm 🛠oci 🐧ubuntu
* [ ] ☁capo 🚀rke2 🎬rolling-update 🛠ha 🐧ubuntu
* [ ] ☁capo 🚀kadm 🎬k8s-upgrade 🐧ubuntu
* [ ] ☁capo 🚀rke2 🎬mgmt-rolling-update 🛠ha,misc 🐧suse
* [ ] ☁capo 🚀rke2 🎬sylva-upgrade 🛠ha,misc 🐧ubuntu

* [x] ☁capm3 🚀rke2 🐧suse
* [x] ☁capm3 🚀kadm 🛠oci 🐧ubuntu
* [ ] ☁capm3 🚀kadm 🎬mgmt-rolling-update 🛠ha,misc 🐧ubuntu
* [ ] ☁capm3 🚀rke2 🎬k8s-upgrade 🛠ha 🐧suse
* [ ] ☁capm3 🚀kadm 🎬rolling-update 🛠ha 🐧ubuntu
* [ ] ☁capm3 🚀rke2 🎬sylva-upgrade 🛠misc,ha 🐧suse
* [ ] ☁capm3 🚀kadm 🎬rolling-update 🛠ha 🐧suse

<!-- DEPLOYMENT FLAVOR DEFINITION END -->
</details>

**Be aware:** after configuration change, pipeline is not triggered automatically.
Please run it manually (by clicking the `run pipeline` button in Pipelines tab) or push new code.
