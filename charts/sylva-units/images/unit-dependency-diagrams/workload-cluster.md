## [Kustomization dependencies](https://fluxcd.io/flux/components/kustomize/kustomizations/#dependencies) diagrams

Following [mermaid](https://mermaid.js.org/syntax/stateDiagram.html) diagrams were created using [tools/unit-dependency-diagram](../../../../tools/unit-dependency-diagram).

> _Note:_ Where the diagram is too complex to be displayed by GitLab, the syntax can be dumped in https://mermaid.live/edit, where download to SVG action is available.

<Tabs groupId="flavor-tabs">

<TabItem value="kubeadm-capd" label='workload cluster for kubeadm-capd deployment'>

workload cluster for kubeadm-capd deployment:

```mermaid
%%{init: {'theme': 'dark'} }%%
graph TD;
  calico-crd --> calico
  cluster-reachable --> calico
  mgmt-cluster-ready --> calico
  root-dependency-1 --> calico
  cluster-reachable --> calico-crd
  mgmt-cluster-ready --> calico-crd
  namespace-defs --> calico-crd
  root-dependency-1 --> calico-crd
  mgmt-cluster-ready --> cluster
  root-dependency-1 --> cluster
  calico --> cluster-machines-ready
  cluster --> cluster-machines-ready
  cluster-ready --> cluster-machines-ready
  mgmt-cluster-ready --> cluster-machines-ready
  root-dependency-1 --> cluster-machines-ready
  cluster --> cluster-reachable
  mgmt-cluster-ready --> cluster-reachable
  root-dependency-1 --> cluster-reachable
  cluster --> cluster-ready
  mgmt-cluster-ready --> cluster-ready
  root-dependency-1 --> cluster-ready
  calico --> ingress-nginx
  cluster-machines-ready --> ingress-nginx
  cluster-reachable --> ingress-nginx
  mgmt-cluster-ready --> ingress-nginx
  namespace-defs --> ingress-nginx
  root-dependency-1 --> ingress-nginx
  calico --> kyverno
  cluster-machines-ready --> kyverno
  cluster-reachable --> kyverno
  mgmt-cluster-ready --> kyverno
  namespace-defs --> kyverno
  root-dependency-1 --> kyverno
  calico --> metallb
  cluster-machines-ready --> metallb
  cluster-reachable --> metallb
  mgmt-cluster-ready --> metallb
  namespace-defs --> metallb
  root-dependency-1 --> metallb
  root-dependency-1 --> mgmt-cluster-ready
  calico --> monitoring
  cluster-machines-ready --> monitoring
  cluster-reachable --> monitoring
  mgmt-cluster-ready --> monitoring
  monitoring-crd --> monitoring
  namespace-defs --> monitoring
  root-dependency-1 --> monitoring
  calico --> monitoring-crd
  cluster-machines-ready --> monitoring-crd
  cluster-reachable --> monitoring-crd
  mgmt-cluster-ready --> monitoring-crd
  namespace-defs --> monitoring-crd
  root-dependency-1 --> monitoring-crd
  cluster-reachable --> namespace-defs
  mgmt-cluster-ready --> namespace-defs
  root-dependency-1 --> namespace-defs
  calico --> sylva-prometheus-rules
  cluster-machines-ready --> sylva-prometheus-rules
  cluster-reachable --> sylva-prometheus-rules
  mgmt-cluster-ready --> sylva-prometheus-rules
  monitoring --> sylva-prometheus-rules
  namespace-defs --> sylva-prometheus-rules
  root-dependency-1 --> sylva-prometheus-rules
  cluster-machines-ready --> tigera-clusterrole
  cluster-reachable --> tigera-clusterrole
  mgmt-cluster-ready --> tigera-clusterrole
  namespace-defs --> tigera-clusterrole
  root-dependency-1 --> tigera-clusterrole
```

</TabItem>

<TabItem value="kubeadm-capo" label='workload cluster for kubeadm-capo deployment'>

workload cluster for kubeadm-capo deployment:

```mermaid
%%{init: {'theme': 'dark'} }%%
graph TD;
  calico-crd --> calico
  cluster-reachable --> calico
  mgmt-cluster-ready --> calico
  root-dependency-1 --> calico
  cluster-reachable --> calico-crd
  mgmt-cluster-ready --> calico-crd
  namespace-defs --> calico-crd
  root-dependency-1 --> calico-crd
  mgmt-cluster-ready --> capo-cloud-config
  root-dependency-1 --> capo-cloud-config
  capo-cloud-config --> capo-cluster-resources
  mgmt-cluster-ready --> capo-cluster-resources
  root-dependency-1 --> capo-cluster-resources
  calico --> cinder-csi
  cluster-machines-ready --> cinder-csi
  cluster-reachable --> cinder-csi
  mgmt-cluster-ready --> cinder-csi
  namespace-defs --> cinder-csi
  root-dependency-1 --> cinder-csi
  capo-cluster-resources --> cluster
  get-openstack-images --> cluster
  mgmt-cluster-ready --> cluster
  root-dependency-1 --> cluster
  calico --> cluster-machines-ready
  cluster --> cluster-machines-ready
  cluster-ready --> cluster-machines-ready
  mgmt-cluster-ready --> cluster-machines-ready
  root-dependency-1 --> cluster-machines-ready
  cluster --> cluster-reachable
  mgmt-cluster-ready --> cluster-reachable
  root-dependency-1 --> cluster-reachable
  cluster --> cluster-ready
  mgmt-cluster-ready --> cluster-ready
  root-dependency-1 --> cluster-ready
  capo-cloud-config --> get-openstack-images
  mgmt-cluster-ready --> get-openstack-images
  os-images-info --> get-openstack-images
  root-dependency-1 --> get-openstack-images
  calico --> ingress-nginx
  capo-cluster-resources --> ingress-nginx
  cluster-machines-ready --> ingress-nginx
  cluster-reachable --> ingress-nginx
  mgmt-cluster-ready --> ingress-nginx
  namespace-defs --> ingress-nginx
  root-dependency-1 --> ingress-nginx
  calico --> kyverno
  cluster-machines-ready --> kyverno
  cluster-reachable --> kyverno
  mgmt-cluster-ready --> kyverno
  namespace-defs --> kyverno
  root-dependency-1 --> kyverno
  root-dependency-1 --> mgmt-cluster-ready
  calico --> monitoring
  cluster-machines-ready --> monitoring
  cluster-reachable --> monitoring
  mgmt-cluster-ready --> monitoring
  monitoring-crd --> monitoring
  namespace-defs --> monitoring
  root-dependency-1 --> monitoring
  calico --> monitoring-crd
  cluster-machines-ready --> monitoring-crd
  cluster-reachable --> monitoring-crd
  mgmt-cluster-ready --> monitoring-crd
  namespace-defs --> monitoring-crd
  root-dependency-1 --> monitoring-crd
  cluster-reachable --> namespace-defs
  mgmt-cluster-ready --> namespace-defs
  root-dependency-1 --> namespace-defs
  mgmt-cluster-ready --> os-images-info
  root-dependency-1 --> os-images-info
  calico --> sylva-prometheus-rules
  cluster-machines-ready --> sylva-prometheus-rules
  cluster-reachable --> sylva-prometheus-rules
  mgmt-cluster-ready --> sylva-prometheus-rules
  monitoring --> sylva-prometheus-rules
  namespace-defs --> sylva-prometheus-rules
  root-dependency-1 --> sylva-prometheus-rules
  cluster-machines-ready --> tigera-clusterrole
  cluster-reachable --> tigera-clusterrole
  mgmt-cluster-ready --> tigera-clusterrole
  namespace-defs --> tigera-clusterrole
  root-dependency-1 --> tigera-clusterrole
```

</TabItem>

<TabItem value="kubeadm-capv" label='workload cluster for kubeadm-capv deployment'>

workload cluster for kubeadm-capv deployment:

```mermaid
%%{init: {'theme': 'dark'} }%%
graph TD;
  calico-crd --> calico
  cluster-reachable --> calico
  mgmt-cluster-ready --> calico
  root-dependency-1 --> calico
  cluster-reachable --> calico-crd
  mgmt-cluster-ready --> calico-crd
  namespace-defs --> calico-crd
  root-dependency-1 --> calico-crd
  mgmt-cluster-ready --> cluster
  root-dependency-1 --> cluster
  calico --> cluster-machines-ready
  cluster --> cluster-machines-ready
  cluster-ready --> cluster-machines-ready
  mgmt-cluster-ready --> cluster-machines-ready
  root-dependency-1 --> cluster-machines-ready
  cluster --> cluster-reachable
  mgmt-cluster-ready --> cluster-reachable
  root-dependency-1 --> cluster-reachable
  cluster --> cluster-ready
  mgmt-cluster-ready --> cluster-ready
  root-dependency-1 --> cluster-ready
  calico --> ingress-nginx
  cluster-machines-ready --> ingress-nginx
  cluster-reachable --> ingress-nginx
  mgmt-cluster-ready --> ingress-nginx
  namespace-defs --> ingress-nginx
  root-dependency-1 --> ingress-nginx
  calico --> kyverno
  cluster-machines-ready --> kyverno
  cluster-reachable --> kyverno
  mgmt-cluster-ready --> kyverno
  namespace-defs --> kyverno
  root-dependency-1 --> kyverno
  root-dependency-1 --> mgmt-cluster-ready
  calico --> monitoring
  cluster-machines-ready --> monitoring
  cluster-reachable --> monitoring
  mgmt-cluster-ready --> monitoring
  monitoring-crd --> monitoring
  namespace-defs --> monitoring
  root-dependency-1 --> monitoring
  calico --> monitoring-crd
  cluster-machines-ready --> monitoring-crd
  cluster-reachable --> monitoring-crd
  mgmt-cluster-ready --> monitoring-crd
  namespace-defs --> monitoring-crd
  root-dependency-1 --> monitoring-crd
  cluster-reachable --> namespace-defs
  mgmt-cluster-ready --> namespace-defs
  root-dependency-1 --> namespace-defs
  calico --> sylva-prometheus-rules
  cluster-machines-ready --> sylva-prometheus-rules
  cluster-reachable --> sylva-prometheus-rules
  mgmt-cluster-ready --> sylva-prometheus-rules
  monitoring --> sylva-prometheus-rules
  namespace-defs --> sylva-prometheus-rules
  root-dependency-1 --> sylva-prometheus-rules
  cluster-machines-ready --> tigera-clusterrole
  cluster-reachable --> tigera-clusterrole
  mgmt-cluster-ready --> tigera-clusterrole
  namespace-defs --> tigera-clusterrole
  root-dependency-1 --> tigera-clusterrole
  calico --> vsphere-cpi
  cluster-machines-ready --> vsphere-cpi
  cluster-reachable --> vsphere-cpi
  mgmt-cluster-ready --> vsphere-cpi
  namespace-defs --> vsphere-cpi
  root-dependency-1 --> vsphere-cpi
  calico --> vsphere-csi-driver
  cluster-machines-ready --> vsphere-csi-driver
  cluster-reachable --> vsphere-csi-driver
  mgmt-cluster-ready --> vsphere-csi-driver
  namespace-defs --> vsphere-csi-driver
  root-dependency-1 --> vsphere-csi-driver
```

</TabItem>

<TabItem value="rke2-capd" label='workload cluster for rke2-capd deployment'>

workload cluster for rke2-capd deployment:

```mermaid
%%{init: {'theme': 'dark'} }%%
graph TD;
  mgmt-cluster-ready --> cluster
  root-dependency-1 --> cluster
  cluster --> cluster-machines-ready
  cluster-ready --> cluster-machines-ready
  mgmt-cluster-ready --> cluster-machines-ready
  root-dependency-1 --> cluster-machines-ready
  cluster --> cluster-reachable
  mgmt-cluster-ready --> cluster-reachable
  root-dependency-1 --> cluster-reachable
  cluster --> cluster-ready
  mgmt-cluster-ready --> cluster-ready
  root-dependency-1 --> cluster-ready
  cluster-machines-ready --> ingress-nginx
  cluster-reachable --> ingress-nginx
  mgmt-cluster-ready --> ingress-nginx
  namespace-defs --> ingress-nginx
  root-dependency-1 --> ingress-nginx
  cluster-machines-ready --> kyverno
  cluster-reachable --> kyverno
  mgmt-cluster-ready --> kyverno
  namespace-defs --> kyverno
  root-dependency-1 --> kyverno
  cluster-machines-ready --> metallb
  cluster-reachable --> metallb
  mgmt-cluster-ready --> metallb
  namespace-defs --> metallb
  root-dependency-1 --> metallb
  root-dependency-1 --> mgmt-cluster-ready
  cluster-machines-ready --> namespace-defs
  cluster-reachable --> namespace-defs
  mgmt-cluster-ready --> namespace-defs
  root-dependency-1 --> namespace-defs
```

</TabItem>

<TabItem value="rke2-capo" label='workload cluster for rke2-capo deployment'>

workload cluster for rke2-capo deployment:

```mermaid
%%{init: {'theme': 'dark'} }%%
graph TD;
  mgmt-cluster-ready --> capo-cloud-config
  root-dependency-1 --> capo-cloud-config
  capo-cloud-config --> capo-cluster-resources
  mgmt-cluster-ready --> capo-cluster-resources
  root-dependency-1 --> capo-cluster-resources
  cluster-machines-ready --> cinder-csi
  cluster-reachable --> cinder-csi
  mgmt-cluster-ready --> cinder-csi
  namespace-defs --> cinder-csi
  root-dependency-1 --> cinder-csi
  capo-cluster-resources --> cluster
  get-openstack-images --> cluster
  mgmt-cluster-ready --> cluster
  root-dependency-1 --> cluster
  cluster --> cluster-machines-ready
  cluster-ready --> cluster-machines-ready
  mgmt-cluster-ready --> cluster-machines-ready
  root-dependency-1 --> cluster-machines-ready
  cluster --> cluster-reachable
  mgmt-cluster-ready --> cluster-reachable
  root-dependency-1 --> cluster-reachable
  cluster --> cluster-ready
  mgmt-cluster-ready --> cluster-ready
  root-dependency-1 --> cluster-ready
  capo-cloud-config --> get-openstack-images
  mgmt-cluster-ready --> get-openstack-images
  os-images-info --> get-openstack-images
  root-dependency-1 --> get-openstack-images
  capo-cluster-resources --> ingress-nginx
  cluster-machines-ready --> ingress-nginx
  cluster-reachable --> ingress-nginx
  mgmt-cluster-ready --> ingress-nginx
  namespace-defs --> ingress-nginx
  root-dependency-1 --> ingress-nginx
  cluster-machines-ready --> kyverno
  cluster-reachable --> kyverno
  mgmt-cluster-ready --> kyverno
  namespace-defs --> kyverno
  root-dependency-1 --> kyverno
  root-dependency-1 --> mgmt-cluster-ready
  cluster-machines-ready --> monitoring
  cluster-reachable --> monitoring
  mgmt-cluster-ready --> monitoring
  monitoring-crd --> monitoring
  namespace-defs --> monitoring
  root-dependency-1 --> monitoring
  cluster-machines-ready --> monitoring-crd
  cluster-reachable --> monitoring-crd
  mgmt-cluster-ready --> monitoring-crd
  namespace-defs --> monitoring-crd
  root-dependency-1 --> monitoring-crd
  cluster-machines-ready --> namespace-defs
  cluster-reachable --> namespace-defs
  mgmt-cluster-ready --> namespace-defs
  root-dependency-1 --> namespace-defs
  mgmt-cluster-ready --> os-images-info
  root-dependency-1 --> os-images-info
  cluster-machines-ready --> sylva-prometheus-rules
  cluster-reachable --> sylva-prometheus-rules
  mgmt-cluster-ready --> sylva-prometheus-rules
  monitoring --> sylva-prometheus-rules
  namespace-defs --> sylva-prometheus-rules
  root-dependency-1 --> sylva-prometheus-rules
```

</TabItem>

<TabItem value="rke2-capv" label='workload cluster for rke2-capv deployment'>

workload cluster for rke2-capv deployment:

```mermaid
%%{init: {'theme': 'dark'} }%%
graph TD;
  calico-crd --> calico
  cluster-reachable --> calico
  mgmt-cluster-ready --> calico
  root-dependency-1 --> calico
  cluster-reachable --> calico-crd
  mgmt-cluster-ready --> calico-crd
  namespace-defs --> calico-crd
  root-dependency-1 --> calico-crd
  mgmt-cluster-ready --> cluster
  root-dependency-1 --> cluster
  calico --> cluster-machines-ready
  cluster --> cluster-machines-ready
  cluster-ready --> cluster-machines-ready
  mgmt-cluster-ready --> cluster-machines-ready
  root-dependency-1 --> cluster-machines-ready
  cluster --> cluster-reachable
  mgmt-cluster-ready --> cluster-reachable
  root-dependency-1 --> cluster-reachable
  cluster --> cluster-ready
  mgmt-cluster-ready --> cluster-ready
  root-dependency-1 --> cluster-ready
  calico --> ingress-nginx
  cluster-machines-ready --> ingress-nginx
  cluster-reachable --> ingress-nginx
  mgmt-cluster-ready --> ingress-nginx
  namespace-defs --> ingress-nginx
  root-dependency-1 --> ingress-nginx
  calico --> kyverno
  cluster-machines-ready --> kyverno
  cluster-reachable --> kyverno
  mgmt-cluster-ready --> kyverno
  namespace-defs --> kyverno
  root-dependency-1 --> kyverno
  root-dependency-1 --> mgmt-cluster-ready
  calico --> monitoring
  cluster-machines-ready --> monitoring
  cluster-reachable --> monitoring
  mgmt-cluster-ready --> monitoring
  monitoring-crd --> monitoring
  namespace-defs --> monitoring
  root-dependency-1 --> monitoring
  calico --> monitoring-crd
  cluster-machines-ready --> monitoring-crd
  cluster-reachable --> monitoring-crd
  mgmt-cluster-ready --> monitoring-crd
  namespace-defs --> monitoring-crd
  root-dependency-1 --> monitoring-crd
  cluster-reachable --> namespace-defs
  mgmt-cluster-ready --> namespace-defs
  root-dependency-1 --> namespace-defs
  calico --> sylva-prometheus-rules
  cluster-machines-ready --> sylva-prometheus-rules
  cluster-reachable --> sylva-prometheus-rules
  mgmt-cluster-ready --> sylva-prometheus-rules
  monitoring --> sylva-prometheus-rules
  namespace-defs --> sylva-prometheus-rules
  root-dependency-1 --> sylva-prometheus-rules
  cluster-machines-ready --> tigera-clusterrole
  cluster-reachable --> tigera-clusterrole
  mgmt-cluster-ready --> tigera-clusterrole
  namespace-defs --> tigera-clusterrole
  root-dependency-1 --> tigera-clusterrole
  calico --> vsphere-cpi
  cluster-machines-ready --> vsphere-cpi
  cluster-reachable --> vsphere-cpi
  mgmt-cluster-ready --> vsphere-cpi
  namespace-defs --> vsphere-cpi
  root-dependency-1 --> vsphere-cpi
  calico --> vsphere-csi-driver
  cluster-machines-ready --> vsphere-csi-driver
  cluster-reachable --> vsphere-csi-driver
  mgmt-cluster-ready --> vsphere-csi-driver
  namespace-defs --> vsphere-csi-driver
  root-dependency-1 --> vsphere-csi-driver
```

</TabItem>

<TabItem value="rke2-capm3" label='workload cluster for rke2-capm3 deployment'>

workload cluster for rke2-capm3 deployment:

```mermaid
%%{init: {'theme': 'dark'} }%%
graph TD;
  cluster-bmh --> cluster
  mgmt-cluster-ready --> cluster
  root-dependency-1 --> cluster
  mgmt-cluster-ready --> cluster-bmh
  root-dependency-1 --> cluster-bmh
  cluster --> cluster-machines-ready
  cluster-ready --> cluster-machines-ready
  mgmt-cluster-ready --> cluster-machines-ready
  root-dependency-1 --> cluster-machines-ready
  cluster --> cluster-reachable
  mgmt-cluster-ready --> cluster-reachable
  root-dependency-1 --> cluster-reachable
  cluster --> cluster-ready
  mgmt-cluster-ready --> cluster-ready
  root-dependency-1 --> cluster-ready
  cluster-machines-ready --> ingress-nginx
  cluster-reachable --> ingress-nginx
  mgmt-cluster-ready --> ingress-nginx
  namespace-defs --> ingress-nginx
  root-dependency-1 --> ingress-nginx
  cluster-machines-ready --> kyverno
  cluster-reachable --> kyverno
  mgmt-cluster-ready --> kyverno
  namespace-defs --> kyverno
  root-dependency-1 --> kyverno
  cluster-machines-ready --> longhorn
  cluster-reachable --> longhorn
  longhorn-crd --> longhorn
  mgmt-cluster-ready --> longhorn
  namespace-defs --> longhorn
  root-dependency-1 --> longhorn
  cluster-machines-ready --> longhorn-crd
  cluster-reachable --> longhorn-crd
  mgmt-cluster-ready --> longhorn-crd
  namespace-defs --> longhorn-crd
  root-dependency-1 --> longhorn-crd
  root-dependency-1 --> mgmt-cluster-ready
  cluster-machines-ready --> monitoring
  cluster-reachable --> monitoring
  mgmt-cluster-ready --> monitoring
  monitoring-crd --> monitoring
  namespace-defs --> monitoring
  root-dependency-1 --> monitoring
  cluster-machines-ready --> monitoring-crd
  cluster-reachable --> monitoring-crd
  mgmt-cluster-ready --> monitoring-crd
  namespace-defs --> monitoring-crd
  root-dependency-1 --> monitoring-crd
  cluster-machines-ready --> namespace-defs
  cluster-reachable --> namespace-defs
  mgmt-cluster-ready --> namespace-defs
  root-dependency-1 --> namespace-defs
  cluster-machines-ready --> sylva-prometheus-rules
  cluster-reachable --> sylva-prometheus-rules
  mgmt-cluster-ready --> sylva-prometheus-rules
  monitoring --> sylva-prometheus-rules
  namespace-defs --> sylva-prometheus-rules
  root-dependency-1 --> sylva-prometheus-rules
```

</TabItem>

<TabItem value="rke2-capm3-virt" label='workload cluster for rke2-capm3-virt deployment'>

workload cluster for rke2-capm3-virt deployment:

```mermaid
%%{init: {'theme': 'dark'} }%%
graph TD;
  cluster-bmh --> cluster
  mgmt-cluster-ready --> cluster
  root-dependency-1 --> cluster
  mgmt-cluster-ready --> cluster-bmh
  root-dependency-1 --> cluster-bmh
  cluster --> cluster-machines-ready
  cluster-ready --> cluster-machines-ready
  mgmt-cluster-ready --> cluster-machines-ready
  root-dependency-1 --> cluster-machines-ready
  cluster --> cluster-reachable
  mgmt-cluster-ready --> cluster-reachable
  root-dependency-1 --> cluster-reachable
  cluster --> cluster-ready
  mgmt-cluster-ready --> cluster-ready
  root-dependency-1 --> cluster-ready
  cluster-machines-ready --> ingress-nginx
  cluster-reachable --> ingress-nginx
  mgmt-cluster-ready --> ingress-nginx
  namespace-defs --> ingress-nginx
  root-dependency-1 --> ingress-nginx
  cluster-machines-ready --> kyverno
  cluster-reachable --> kyverno
  mgmt-cluster-ready --> kyverno
  namespace-defs --> kyverno
  root-dependency-1 --> kyverno
  cluster-machines-ready --> longhorn
  cluster-reachable --> longhorn
  longhorn-crd --> longhorn
  mgmt-cluster-ready --> longhorn
  namespace-defs --> longhorn
  root-dependency-1 --> longhorn
  cluster-machines-ready --> longhorn-crd
  cluster-reachable --> longhorn-crd
  mgmt-cluster-ready --> longhorn-crd
  namespace-defs --> longhorn-crd
  root-dependency-1 --> longhorn-crd
  root-dependency-1 --> mgmt-cluster-ready
  cluster-machines-ready --> namespace-defs
  cluster-reachable --> namespace-defs
  mgmt-cluster-ready --> namespace-defs
  root-dependency-1 --> namespace-defs
```

</TabItem>

</Tabs>
