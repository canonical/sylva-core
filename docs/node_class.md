# Utilizing the Node Class in Sylva

## Introduction

The Sylva project aims to establish a unified set of worker classes to streamline configurations and improve project implementation. This document outlines the proposal for standardizing worker classes within Sylva, focusing on their main features, configurations, and how they cater to different application requirements.

## Standard Node Classes

Sylva introduces three primary node classes, alongside customizable options, to accommodate various computing and networking needs. Each class is tailored to specific performance and configuration requirements:

- **Generic Node Class**: Ideal for IT and non-intensive network workloads, offering a baseline performance with optimized footprint and without specialized configurations such as huge-pages or CPU pinning.
  
- **Intensive Node Class**: Designed for workloads that demand intensive computing power and predictable performance but less flexibility, featuring huge-pages and static CPU manager settings for CPU pinning.
  
- **SR-IOV Node Class**: Targets high network performance and near real-time computing, supporting huge pages, SR-IOV, CPU pinning, NUMA topology awareness, and system CPU isolation.
  
- **Custom Node Class**: Provides flexibility for custom kernel, boot, and kubelet settings to meet specific CNF requirements.

Starting from Sylva V1.0.0, the generic node class is predefined. Users can define additional node classes by modifying the `cluster.node_classes` property.

### Deployment Considerations

When deploying Sylva, the defined node classes become available for both management and workload clusters through the `shared_workload_clusters_values` configmaps.

It is possible to select a node class for :

- the entire cluster : `cluster.default_node_class`
- the control plane: `cluster.control_plane.node_class`
- machine deployments (default value): `cluster.machine_deployment_default.node_class`
- a specific machine deployment: `cluster.machine_deployments.X.node_class`

Node classes are only available on RKE2 clusters. It has not yet been implemented for Kubeadm.

## kernel configuration

### Huge pages

**Configurable Sizes**: Supports 2M and 1G huge pages, with allocations up to 90% of total memory.

**Example**: 70% of memory is allocated for 2M hugePage and 20% of memory for 1G.

```yaml
node_classes:
  <node_class_name>:
    kernel_cmdline:
      hugepages:
        enabled: true
          2M_percentage_total: "0.7" # 70% of the memory will be reserved for 2M huge page
          1G_percentage_total: "0.2" # 20% of the memory will be reserved for 2M huge page
          default_size: 2M
```

### Additional Kernel Options

**Purpose**: Activate specific kernel options like Intel_iommu, sriov_numvfs, and system CPU isolation.

**Example**: Enabling SR-IOV options

```yaml
node_classes:
  <node_class_name>:
    kernel_cmdline:
      extra_options: "Intel_iommu=on Intel_iommu=pt sriov_numvfs=32"
```

## Kubelet configurations

Customize kubelet settings to optimize node performance and resource management. For a comprehensive list of configurable parameters, visit the [Kubernetes documentation](https://kubernetes.io/docs/tasks/administer-cluster/kubelet-config-file/).

**Example**: Customizing Eviction Hard Limits

```yaml
node_classes:
  <node_class_name>:
    kubelet_config_file_options:
      evictionHard:
        memory.available: "500Mi"
        nodefs.available: "10%"
        nodefs.inodesFree: "5%"
        imagefs.available: "15%"
```

## Node Taint/Labels/Annotations

Define taints, labels, and annotations to manage node behavior and workload allocation effectively.

**Example**: Customizing Eviction Hard Limits

```yaml
node_classes:
  <node_class_name>:
    nodeTaints: {}
    nodeLabels:
      sylva.org/node-label: true
    nodeAnnotations:
      sylva.org/node-annotation: true
```

## Additionnal commands

Specify pre and post-bootstrap commands for further customization and optimization of node setup.

```yaml
node_classes:
  <node_class_name>:
    additional_commands:
      pre_bootstrap_commands: []
      post_bootstrap_commands: []
```

## Examples

Below are YAML configuration examples for the intensive and SR-IOV node classes, illustrating how to apply the discussed settings and options.

- **Intensive node_class example**

```yaml
node_classes:
  intensive:
    kernel_cmdline:
      hugepages:
        enabled: true
          2M_percentage_total: "0.7"
          1G_percentage_total: "0.2"
          default_size: 2M
      extra_options: ""
    kubelet_extra_args: {}
    kubelet_config_file_options:
      featureGates:
        CPUManager: true
      cpuManagerPolicy: static
      kubeReserved:
        cpu: "500m"
        memory: "1Gi"
      systemReserved:
        cpu: "500m"
        memory: "1Gi"
      evictionHard:
        memory.available: "500Mi"
        nodefs.available: "10%"
        nodefs.inodesFree: "5%"
        imagefs.available: "15%"
    nodeTaints: {}
    nodeLabels:
      sylva.org/annotate-node-label-intensive: true
    nodeAnnotations: {}
    additional_commands:
      pre_bootstrap_commands: []
      post_bootstrap_commands: []
```

- **SR-IOV node_class example**

```yaml
node_classes:
  sriov:
    kernel_cmdline:
      hugepages:
        enabled: true
        2M_percentage_total: "0.7"
        1G_percentage_total: "0.2"
        default_size: 2M
      extra_options: "Intel_iommu=on Intel_iommu=pt sriov_numvfs=32"
    kubelet_extra_args: {}
    kubelet_config_file_options:
      featureGates:
        CPUManager: true
        CPUManagerPolicyOptions: true
        CPUManagerPolicyBetaOptions: true
        CPUManagerPolicyAlphaOptions: true
        MemoryManager: true
        TopologyManager: true
        TopologyManagerPolicyOptions: true
      memoryManagerPolicy: static
      cpuManagerPolicy: static
      cpuManagerPolicyOptions:
        full-pcpus-only=true
        distribute-cpus-across-numa=true
      topologyManagerPolicy: single-numa-node
      topologyManagerScope: pod
      kubeReserved:
        cpu: "500m"
        memory: "1Gi"
      systemReserved:
        cpu: "500m"
        memory: "1Gi"
      reservedSystemCPUs: "0-7,64-71"
      evictionHard:
        memory.available: "500Mi"
        nodefs.available: "10%"
        nodefs.inodesFree: "5%"
        imagefs.available: "15%"
    nodeTaints: {}
    nodeLabels:
      sylva.org/annotate-node-label-sriov: true
    nodeAnnotations: {}
    additional_commands:
      pre_bootstrap_commands: []
      post_bootstrap_commands: []
```
