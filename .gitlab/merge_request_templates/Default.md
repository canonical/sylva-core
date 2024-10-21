## What does this MR do and why?

%{first_multiline_commit}

### Related reference(s)

## Test coverage

## CI configuration

Below you can choose test deployment variants to run in this MR's CI.

<details><summary> Click to open to CI configuration </summary>

**Legend:**

| Icon | Meaning                  | Available values                                                          |
|------|--------------------------|---------------------------------------------------------------------------|
| ☁   | **Infra Provider**       | `capd`, `capo`, `capm3`                                                   |
| 🚀  | **Bootstrap Provider**   | `kubeadm` (alias `kadm`), `rke2`                                          |
| 🎸  | **Node OS**              | `ubuntu`, `suse`                                                          |
| 🛠  | **Deployment Options**    | `light-deploy`, `oci`, `ha`, `misc`                                       |
| 🎬  | **Pipeline Scenarios**   | `rolling-update`, `mgmt-rolling-update`, `sylva-upgrade`, `simple-update`, `preview` |

<!-- DEPLOYMENT FLAVOR DEFINITION START -->

* [x] 🎬preview ☁capd 🚀kadm 🐧ubuntu 🛠oci
* [ ] 🎬preview ☁capo 🚀rke2 🐧suse
* [ ] 🎬preview ☁capm3 🚀rke2 🐧ubuntu

* [x] ☁capd 🚀kubeadm 🛠light-deploy 🎸ubuntu
* [ ] ☁capd 🚀rke2 🛠oci,light-deploy 🐧suse

* [ ] ☁capo 🚀rke2 🎸ubuntu
* [ ] ☁capo 🚀kadm 🛠oci 🎸suse
* [ ] ☁capo 🚀rke2 🎬rolling-update 🛠ha 🐧ubuntu
* [ ] ☁capo 🚀rke2 🎬mgmt-rolling-update 🛠ha,misc 🐧suse
* [ ] ☁capo 🚀rke2 🎬sylva-upgrade 🛠misc 🎸ubuntu

* [x] ☁capm3 🚀rke2 🎸suse
* [ ] ☁capm3 🚀kadm 🛠oci  🎸ubuntu
* [ ] ☁capm3 🚀rke2 🎬sylva-upgrade 🛠misc,ha 🐧suse
* [x] ☁capm3 🚀rke2 🎬mgmt-rolling-update 🛠ha,misc 🐧ubuntu
* [ ] ☁capm3 🚀kadm 🎬rolling-update 🛠ha 🐧suse

<!-- DEPLOYMENT FLAVOR DEFINITION END -->
</details>

**Be aware:** after configuration change, pipeline is not triggered automatically.
Please run it manually or push new code.
