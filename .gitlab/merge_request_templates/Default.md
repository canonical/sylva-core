## What does this MR do and why?

%{first_multiline_commit}

### Related reference(s)

## Test coverage

## CI configuration

<details><summary> Click to open to CI configuration </summary>

Here you can choose test deployment flavors to run into CI.

* [x] Enable option 1

<details><summary> Run standard deployment pipelines with random infra/bootstrap/OS (default) </summary>        <!-- OPTION 1 DEFINITION START -->

What kind of infra provider must be tested (random pick if no choice selected):

* [ ] infra provider: capd (Docker)
* [ ] infra provider: capm3-virt (Baremetal emulation)
* [~] infra provider: capo (OpenStack - needs specific rights)

What kind of bootstrap provider must be tested (random pick if no choice selected):

* [ ] bootstrap provider: kubeadm (cabpk)
* [ ] bootstrap provider: rke2 (cabpr)

What kind of node OS must be tested (random pick if no choice selected):

* [ ] node os: ubuntu (Ubuntu)
* [ ] node os: suse (OpenSuse)

What kind of deployment options must be tested (random pick if no choice selected):

* [ ] artifact source: oci (Force use of OCI artifacts)
* [ ] artifact source: git (Force use Git artifacts)
* [x] management cluster availability mode: mgmt-ha (High availability with several CP nodes, unavailable for capd)
* [ ] management cluster availability mode: mgmt-single-node (Quick single CP node deployment)
* [x] workload cluster availability mode: wkld-ha (High availability with several CP nodes, unavailable for capd)
* [ ] workload cluster availability mode: wkld-single-node (Quick single CP node deployment)
* [ ] deployment variant: none (Use floating IP, only for capo)
* [ ] deployment variant: capo-fip (Use floating IP, only for capo)

What kind of deployment scenario must be tested:

* [ ] scenario: mgmt-only-no-update
* [ ] scenario: mgmt+wkld-no-update
* [ ] scenario: mgmt+wkld-simple-update (**Default**, no rolling update triggered)
* [ ] scenario: mgmt-rolling-update (Management cluster rolling upgrade)
* [ ] scenario: wkld-rolling-update (Workload cluster rolling upgrade)
* [ ] scenario: k8s-upgrade (Workload cluster K8s version upgrade)
* [ ] scenario: migration (Sylva version migration from 1.1.1 to main)

Which optional units must be enabled:

* [ ] optional unit: kubevirt
* [ ] optional unit: harbor
* [ ] optional unit: sriov
* [ ] optional unit: neuvector
* [ ] optional unit: gitea

Select here global options (applied to all deployment):

* [~] global option: skip-tests (Do not run tests)
* [~] global option: allow-failure (Allow deployment pipeline to fail)
* [~] global option: no-monitoring (No monitoring stack enabled)

</details>          <!-- OPTION 1 DEFINITION END -->

* [ ] Enable option 2

<details><summary> Explicitly define deployments flavors </summary>     <!-- OPTION 2 DEFINITION START -->

Legend:
  ☁ => infra provider, 🚀 => bootstrap provider, 🎸 => node OS, 🛠 => deployment options  

* [ ] ☁capm3-virt 🚀kubeadm 🎸ubuntu 🛠migration
* [ ] ☁capo 🚀rke2 🎸suse 🛠oci,k8s-upgrade
* [ ] ☁capo 🚀rke2 🎸ubuntu 🛠kubevirt

</details>     <!-- OPTION 2 DEFINITION END -->

**Be aware:** after configuration change, pipeline is not triggered automatically.
Please run it manually or push new code.

</details>
