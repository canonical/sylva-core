## Install OKD Single Node Cluster

Currently, OKD cannot be used as a management cluster. Some Sylva units may require modification, particularly regarding security context handling, to function properly on OKD. For example, when installing FluxCD on OKD, the following change is necessary: [Flux OpenShift installation](https://fluxcd.io/flux/installation/configuration/openshift/). Separate tasks will need to be planned to enable these Sylva units on OKD.

In this setup, the management cluster will be a Kubernetes cluster, such as an RKE2 cluster, while OKD will be deployed as a workload cluster.

In the first phase, only a single-node cluster installation via the CAPI provider is tested. The multi-node cluster installation will be enabled in the next phase.

## OKD Installer Components

As far as Sylva stack is concerned, there are two components that work together to install OKD. They are Assisted Installer and OpenShift Agent CAPI provider.

The OpenShift Agent CAPI provider only works with CAPM3 as infrastructure provider so it is abbreviated as `cabpob`. It works like an adaptation layer: it provides the CAPI contract; under the hood it interacts with assisted installer to do the install job. Here is [documentation of the OpenShift CAPI provider architecture]( https://github.com/openshift-assisted/cluster-api-agent/blob/master/docs/architecture_design.md)

The heavy lift work is done by assisted-installer component. It will build a live iso based on the information provided by the OpenShift Agent CAPI provider, serve the image, instruct the install and collect the install logs.

## DNS Requirements

The assisted installer has two service endpoints: assisted-service and assisted-images. On a k8s management cluster, The external URLs to these service endpoints are provided by nginx ingress.

Because the assised-installer is running on the management cluster, the DNS entries for the assisted installer external URL just need to point to the VIP of the management cluster. The dns entries are static nature and can be provided by the management cluster via the Sylva k8s-gateway unit, or an external dns service provided outside of Sylva stack.

OKD or OpenShift cluster k8s api URLs are name based, and they are:

- `api.<cluster-name>.<domain-name>`

- `api-int.<cluster-name>.<domain-name>`

- `*.apps.<cluster-name>.<domain-name>`

In a multi-cluster architecrure, a management cluster will install and manage multiple workload clusters. Each OKD workload cluster will need to have the above three DNS entries corresponding to its cluster. In production, we expect an external dns service outside of Sylva stack will fullfil the DNS requirements with pre-populated DNS entries for all workload clusters. An alternative to the external dns service approach is to enhance the Sylva k8s-gateway unit so it will be able to add the cluster DNS entries when a cluster is created, and remove the cluster DNS entries when a cluster is deleted. This alternative work is being tracked by: https://gitlab.com/sylva-projects/sylva-core/-/issues/1573

## How to Specify cluster_virtual_ip for Single Node Cluster

OKD single node cluster deployment does not support VIP. The assigned node IP address (DHCP or static) is used instead as cluster_virtual_ip.

### Using DHCP Assignment

When DHCP is used to assign IP address to the node, in order to assign a deterministic cluster_virtual_ip address to the cluster, a static mac-to-ip mapping  can be used. For example if using dnsmasq to provide DHCP service, such a mapping looks like,

```
dhcp-host=00:60:2f:31:81:01,192.168.222.31,okd-sno
```

Because the MAC address of the baremetal host is fixed, so it will get a fixed IP address assigned and that IP address will be used as cluster_virtual_ip.

### Using Static IP Address

A static IP address assignment can be used as well.

[NMStateConfig](https://github.com/openshift/assisted-service/blob/master/config/crd/bases/agent-install.openshift.io_nmstateconfigs.yaml) can be used to provision the OKD node with a static IP address through the OpenShift CAPI provider, here is a example of how to provision a static IP address via a NMStateConfig CR and refer to the NMStateConfig from a AgentControlPlane,

```
apiVersion: agent-install.openshift.io/v1beta1
kind: NMStateConfig
metadata:
  name: okd-sno-nmstate
  namespace: test-capi
  labels:
    cluster-name: okd-sno
spec:
  interfaces:
    - name: "enp1s0"
      macAddress: "00:60:2f:31:81:01"
  config:
    interfaces:
      - name: enp1s0
        type: ethernet
        state: up
        ipv4:
          address:
          - ip: 192.168.222.31
            prefix-length: 24
          enabled: true
          dhcp: false
    routes:
      config:
      - destination: 0.0.0.0/0
        next-hop-address: 192.168.222.1
        next-hop-interface: enp1s0
    dns-resolver:
      config:
        server:
          - 192.168.222.1
        search:
          - lab.home
---
apiVersion: controlplane.cluster.x-k8s.io/v1alpha1
kind: AgentControlPlane
metadata:
  name: okd-sno
  namespace: test-capi
spec:
  agentBootstrapConfigSpec:
    nmStateConfigLabelSelector:
      matchLabels:
        cluster-name: okd-sno     # use a label to match the NMStateConfig CR
# the rest of AgentControlPlane CR are skipped
```

To leverage the NMStateConfig, sylva-capi-cluster helm template will need update.

### IPAM

Because OKD single node cluster does not support VIP, to get deterministic address for cluster_virtual_ip, IPAM can not be used with single node cluster deployment.

## Sample Configurations

In this section, we will demonstrate an RKE2 management cluster with `cabpob` and `okd-assisted-installer` enabled, alongside the OKD workload cluster.

The OKD cluster installation requires static DNS entries for the assisted installer service, as well as DNS entries for each workload cluster. Therefore, we will begin with the sample DNS settings."

### DNS Server Settings

Here is a sample dnsmasq setting (with the irrelevant parts removed) that will work with OKD single node cluster deployment when DHCP is used,

```
local=/lab.home/
domain=lab.home                          # {{ .Values.cluster.okd.baseDomain }} is lab.home
dhcp-range=192.168.222.20,192.168.222.99
dhcp-host=00:60:2f:31:81:01,192.168.222.31,okd-sno   # {{ .Values.cluster.name }} is okd-sno

# per workload cluster DNS entries for this OKD cluster
address=/api.okd-sno.lab.home/192.168.222.31
address=/api-int.okd-sno.lab.home/192.168.222.31
address=/.apps.okd-sno.lab.home/192.168.222.31

# assisted installer DNS entries for all OKD clusters, this points to the mgmt cluster
address=/vm-assisted-service.example.com/192.168.222.100
address=/vm-image-service.example.com/192.168.222.100
```

Note: the above dnsmasq sample setting containers the DNS entries for the assisted installer. These entries are static DNS entries and point to the management cluster. Since an external dnsmasq is used here with pre-popualted DNS entries for the workload clusters, so the static DNS entries are provided by the same dnsmasq. The k8s-gateway unit mentioned earlier is not used to provide the static DNS entries for the assisted installer.

### Management Cluster Configuration

Here is a sample of management cluster (the rke2-capm3 is the only tested variant) values needed for deploying an OKD workload cluster on baremetal infra:

```
cluster:
  capm3:
    dns_servers:
    - <external DNS server IP>
units:
  cabpob:
    enabled: true
  okd-assisted-installer:
    enabled: true
  longhorn:
    enabled: false         # longhorn does not work with assisted installer yet
  capm3:
    enabled: true
  metal3:
    enabled: true
okd:
  assisted:
    # the following dns entries are served by an external dnsmasq, not by k8s-gateway unit
    serviceHostname: vm-assisted-service.example.com
    imageHostname: vm-image-service.example.com
```

Note: the DNS entries for okd.serviceHostname and okd.imageHostname are served by the dnsmasq illustrated in the DNS settings section. The management cluster gets the dnsmasq server address via `.cluster.capm3.dns_servers`, so that it can resolve the static DNS entries for the assisted installer and the per workload cluster k8s API DNS entries mentioned earlier.

The DNS server IP address can also be acquired through DHCP. So in the next section where DHCP is used for the OKD workload cluster configuration, there is no setting for `.cluster.capm3.dns_servers`.

The assisted installer has not been tested to work with longhorn so the longhorn unit is disabled here.

### OKD Workload Cluster Configuration

Here is a sample of OKD CAPM3 workload cluster values:

```
cluster:
  name: okd-sno
  agent_config_format: "ignition"
  capi_providers:
    infra_provider: capm3
    bootstrap_provider: cabpob
  control_plane_replicas: 1
  capm3:
    # For OKD, the only capm3-image spec required is `machine_image_format: live-iso`, rest are dummy values
    machine_image_checksum: https://foo/bar.sha256sum
    machine_image_checksum_type: sha256
    machine_image_format: live-iso
    machine_image_url: https://foo/bar
  okd:
    version: v4.14.0
    releaseImage: quay.io/okd/scos-release:4.14.0-0.okd-scos-2024-01-30-032525
    baseDomain: lab.home
    sshAuthorizedKey: # put a ssh public key here for username "core"
    pullSecret: # put a pull secret here
units:
  longhorn-crd:
    enabled: false
  longhorn:
    enabled: false
  multus-ready:
    enabled: false
  sriov-crd:
    enabled: false
  cluster-machines-ready:
    enabled: false
  monitoring-crd:
    enabled: false
  monitoring:
    enabled: false
  calico-crd:
    enabled: false
  calico:
    enabled: false
  tigera-clusterrole:
    enabled: false
```

Note in the above configuration sample, cluster.name and cluster.okd.baseDomain will form the DNS entries required for the OKD cluster as mentioned in the DNS settings section.

Values for machine_image_* under cluster.capm3 are required. This is because in the sylva-capi-cluster repo the templates/_helpers.tpl has the following logic:

```
  {{- if ($def.image_key | default "") -}}
      ...
  {{- else -}}
checksum: {{ $def.machine_image_checksum }}
checksumType: {{ $def.machine_image_checksum_type }}
format: {{ $def.machine_image_format }}
url: {{ $def.machine_image_url }}
  {{- end -}}
```

For OKD the `image_key` is not used so the `machine_image_*` values are required, otherwise the [`sylva-capi-cluster` chart](https://gitlab.com/sylva-projects/sylva-elements/helm-charts/sylva-capi-cluster) templating will fail.

The okd.pullSecret is required but can be a dummy value, one can create the base64 value like:

```
echo -n '{"auths":{"fake":{"auth":"aWQ6cGFzcwo="}}}' | base64
```

OKD has a default user "core", the purpose of okd.sshAuthorizedKey is to login to the OKD node as this user.
