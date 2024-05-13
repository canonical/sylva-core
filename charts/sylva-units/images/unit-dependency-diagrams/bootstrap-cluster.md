## [Kustomization dependencies](https://fluxcd.io/flux/components/kustomize/kustomizations/#dependencies) diagrams

Following [mermaid](https://mermaid.js.org/syntax/stateDiagram.html) diagrams were created using [tools/unit-dependency-diagram](../../../../tools/unit-dependency-diagram).

> _Note:_ Where the diagram is too complex to be displayed by GitLab, the syntax can be dumped in https://mermaid.live/edit, where download to SVG action is available.

<Tabs groupId="flavor-tabs">

<TabItem value="kubeadm-capd" label='bootstrap cluster for kubeadm-capd deployment'>

bootstrap cluster for kubeadm-capd deployment:

```mermaid
%%{init: {'theme': 'neutral'} }%%
graph TD;
  cert-manager --> cabpk
  calico-crd --> calico
  cluster-reachable --> calico
  cluster-reachable --> calico-crd
  namespace-defs --> calico-crd
  cert-manager --> capd
  cert-manager --> capi
  cabpk --> cluster
  capd --> cluster
  capi --> cluster
  calico --> cluster-machines-ready
  cluster --> cluster-machines-ready
  cluster-ready --> cluster-machines-ready
  cluster --> cluster-reachable
  cluster --> cluster-ready
  management-cluster-flux --> management-cluster-configs
  management-namespace-defs --> management-cluster-configs
  calico --> management-cluster-flux
  cluster-reachable --> management-cluster-flux
  cluster-reachable --> management-namespace-defs
  cluster-machines-ready --> management-sylva-units
  management-cluster-configs --> management-sylva-units
  management-namespace-defs --> management-sylva-units
  cluster-machines-ready --> pivot
  management-sylva-units --> pivot
  cluster-reachable --> tigera-clusterrole
```

</TabItem>

<TabItem value="kubeadm-capo" label='bootstrap cluster for kubeadm-capo deployment'>

bootstrap cluster for kubeadm-capo deployment:

```mermaid
%%{init: {'theme': 'neutral'} }%%
graph TD;
  cert-manager --> cabpk
  calico-crd --> calico
  cluster-reachable --> calico
  cluster-reachable --> calico-crd
  namespace-defs --> calico-crd
  cert-manager --> capi
  cert-manager --> capo
  capo-cloud-config --> capo-cluster-resources
  heat-operator --> capo-cluster-resources
  cabpk --> cluster
  capi --> cluster
  capo --> cluster
  capo-cluster-resources --> cluster
  get-openstack-images --> cluster
  calico --> cluster-machines-ready
  cluster --> cluster-machines-ready
  cluster-ready --> cluster-machines-ready
  cluster --> cluster-reachable
  cluster --> cluster-ready
  bootstrap-local-path --> get-openstack-images
  capo-cloud-config --> get-openstack-images
  os-images-info --> get-openstack-images
  management-cluster-flux --> management-cluster-configs
  management-namespace-defs --> management-cluster-configs
  calico --> management-cluster-flux
  cluster-reachable --> management-cluster-flux
  cluster-reachable --> management-namespace-defs
  cluster-machines-ready --> management-sylva-units
  management-cluster-configs --> management-sylva-units
  management-namespace-defs --> management-sylva-units
  cluster-machines-ready --> pivot
  management-sylva-units --> pivot
  cluster-reachable --> tigera-clusterrole
```

</TabItem>

<TabItem value="kubeadm-capv" label='bootstrap cluster for kubeadm-capv deployment'>

bootstrap cluster for kubeadm-capv deployment:

```mermaid
%%{init: {'theme': 'neutral'} }%%
graph TD;
  cert-manager --> cabpk
  calico-crd --> calico
  cluster-reachable --> calico
  cluster-reachable --> calico-crd
  namespace-defs --> calico-crd
  cert-manager --> capi
  cert-manager --> capv
  cabpk --> cluster
  capi --> cluster
  capv --> cluster
  calico --> cluster-machines-ready
  cluster --> cluster-machines-ready
  cluster-ready --> cluster-machines-ready
  cluster --> cluster-reachable
  cluster --> cluster-ready
  management-cluster-flux --> management-cluster-configs
  management-namespace-defs --> management-cluster-configs
  calico --> management-cluster-flux
  cluster-reachable --> management-cluster-flux
  cluster-reachable --> management-namespace-defs
  cluster-machines-ready --> management-sylva-units
  management-cluster-configs --> management-sylva-units
  management-namespace-defs --> management-sylva-units
  cluster-machines-ready --> pivot
  management-sylva-units --> pivot
  cluster-reachable --> tigera-clusterrole
  cabpk --> vsphere-cpi
  capi --> vsphere-cpi
  capv --> vsphere-cpi
```

</TabItem>

<TabItem value="rke2-capd" label='bootstrap cluster for rke2-capd deployment'>

bootstrap cluster for rke2-capd deployment:

```mermaid
%%{init: {'theme': 'neutral'} }%%
graph TD;
  cert-manager --> cabpr
  cert-manager --> capd
  cert-manager --> capi
  cabpr --> cluster
  capd --> cluster
  capi --> cluster
  cluster --> cluster-machines-ready
  cluster-ready --> cluster-machines-ready
  cluster --> cluster-reachable
  cluster --> cluster-ready
  management-cluster-flux --> management-cluster-configs
  management-namespace-defs --> management-cluster-configs
  cluster-reachable --> management-cluster-flux
  cluster-reachable --> management-namespace-defs
  cluster-machines-ready --> management-sylva-units
  management-cluster-configs --> management-sylva-units
  management-namespace-defs --> management-sylva-units
  cluster-machines-ready --> pivot
  management-sylva-units --> pivot
```

</TabItem>

<TabItem value="rke2-capo" label='bootstrap cluster for rke2-capo deployment'>

bootstrap cluster for rke2-capo deployment:

```mermaid
%%{init: {'theme': 'neutral'} }%%
graph TD;
  cert-manager --> cabpr
  cert-manager --> capi
  cert-manager --> capo
  capo-cloud-config --> capo-cluster-resources
  heat-operator --> capo-cluster-resources
  cabpr --> cluster
  capi --> cluster
  capo --> cluster
  capo-cluster-resources --> cluster
  get-openstack-images --> cluster
  cluster --> cluster-machines-ready
  cluster-ready --> cluster-machines-ready
  cluster --> cluster-reachable
  cluster --> cluster-ready
  bootstrap-local-path --> get-openstack-images
  capo-cloud-config --> get-openstack-images
  os-images-info --> get-openstack-images
  management-cluster-flux --> management-cluster-configs
  management-namespace-defs --> management-cluster-configs
  cluster-reachable --> management-cluster-flux
  cluster-reachable --> management-namespace-defs
  cluster-machines-ready --> management-sylva-units
  management-cluster-configs --> management-sylva-units
  management-namespace-defs --> management-sylva-units
  cluster-machines-ready --> pivot
  management-sylva-units --> pivot
```

</TabItem>

<TabItem value="rke2-capv" label='bootstrap cluster for rke2-capv deployment'>

bootstrap cluster for rke2-capv deployment:

```mermaid
%%{init: {'theme': 'neutral'} }%%
graph TD;
  cert-manager --> cabpr
  cert-manager --> capi
  cert-manager --> capv
  cabpr --> cluster
  capi --> cluster
  capv --> cluster
  cluster --> cluster-machines-ready
  cluster-ready --> cluster-machines-ready
  cluster --> cluster-reachable
  cluster --> cluster-ready
  management-cluster-flux --> management-cluster-configs
  management-namespace-defs --> management-cluster-configs
  cluster-reachable --> management-cluster-flux
  cluster-reachable --> management-namespace-defs
  cluster-machines-ready --> management-sylva-units
  management-cluster-configs --> management-sylva-units
  management-namespace-defs --> management-sylva-units
  cluster-machines-ready --> pivot
  management-sylva-units --> pivot
  cabpr --> vsphere-cpi
  capi --> vsphere-cpi
  capv --> vsphere-cpi
```

</TabItem>

<TabItem value="rke2-capm3" label='bootstrap cluster for rke2-capm3 deployment'>

bootstrap cluster for rke2-capm3 deployment:

```mermaid
%%{init: {'theme': 'neutral'} }%%
graph TD;
  cert-manager --> cabpr
  cert-manager --> capi
  cert-manager --> capm3
  metal3 --> capm3
  cabpr --> cluster
  capi --> cluster
  capm3 --> cluster
  cluster-bmh --> cluster
  kyverno-policies --> cluster
  os-image-server --> cluster
  metal3 --> cluster-bmh
  cluster --> cluster-machines-ready
  cluster-ready --> cluster-machines-ready
  cluster --> cluster-reachable
  cluster --> cluster-ready
  kyverno --> kyverno-policies
  management-cluster-flux --> management-cluster-configs
  management-namespace-defs --> management-cluster-configs
  cluster-reachable --> management-cluster-flux
  cluster-reachable --> management-namespace-defs
  cluster-machines-ready --> management-sylva-units
  management-cluster-configs --> management-sylva-units
  management-namespace-defs --> management-sylva-units
  bootstrap-local-path --> metal3
  cert-manager --> metal3
  namespace-defs --> metal3
  kyverno-policies --> namespace-defs
  bootstrap-local-path --> os-image-server
  ingress-nginx --> os-image-server
  os-images-info --> os-image-server
  cluster-machines-ready --> pivot
  management-sylva-units --> pivot
```

</TabItem>

<TabItem value="rke2-capm3-virt" label='bootstrap cluster for rke2-capm3-virt deployment'>

bootstrap cluster for rke2-capm3-virt deployment:

```mermaid
%%{init: {'theme': 'neutral'} }%%
graph TD;
  cert-manager --> cabpr
  cert-manager --> capi
  cert-manager --> capm3
  metal3 --> capm3
  cabpr --> cluster
  capi --> cluster
  capm3 --> cluster
  cluster-bmh --> cluster
  kyverno-policies --> cluster
  libvirt-metal --> cluster
  os-image-server --> cluster
  libvirt-metal --> cluster-bmh
  metal3 --> cluster-bmh
  cluster --> cluster-machines-ready
  cluster-ready --> cluster-machines-ready
  cluster --> cluster-reachable
  cluster --> cluster-ready
  kyverno --> kyverno-policies
  ingress-nginx --> libvirt-metal
  multus-ready --> libvirt-metal
  management-cluster-flux --> management-cluster-configs
  management-namespace-defs --> management-cluster-configs
  cluster-reachable --> management-cluster-flux
  cluster-reachable --> management-namespace-defs
  cluster-machines-ready --> management-sylva-units
  management-cluster-configs --> management-sylva-units
  management-namespace-defs --> management-sylva-units
  bootstrap-local-path --> metal3
  cert-manager --> metal3
  multus --> metal3
  namespace-defs --> metal3
  multus --> multus-ready
  kyverno-policies --> namespace-defs
  bootstrap-local-path --> os-image-server
  ingress-nginx --> os-image-server
  os-images-info --> os-image-server
  cluster-machines-ready --> pivot
  management-sylva-units --> pivot
```

</TabItem>

</Tabs>
