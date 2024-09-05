<!-- markdownlint-disable MD044 -->
| name | full description | maturity | internal | source | version |
| :----- | :----- | :----- | :----- | :----- | :----- |
| **cabpk** | installs Kubeadm CAPI bootstrap provider | core-component |  | [Kustomize](https://github.com/kubernetes-sigs/cluster-api/releases/download/v1.7.4/bootstrap-components.yaml) | v1.7.4 |
| **cabpr** | installs RKE2 CAPI bootstrap provider | core-component |  | [Kustomize](https://github.com/rancher/cluster-api-provider-rke2/releases/download/v0.6.0/bootstrap-components.yaml) | v0.6.0 |
| **capd** | installs Docker CAPI infra provider | core-component |  | [Kustomize](https://github.com/kubernetes-sigs/cluster-api//test/infrastructure/docker/config/default/?ref=v1.7.4) | v1.7.4 |
| **capi** | installs Cluster API core operator | core-component |  | [Kustomize](https://github.com/kubernetes-sigs/cluster-api/releases/download/v1.7.4/core-components.yaml) | v1.7.4 |
| **capm3** | installs Metal3 CAPI infra provider, for baremetal | core-component |  | [Kustomize](https://github.com/metal3-io/cluster-api-provider-metal3/releases/download/v1.7.1/infrastructure-components.yaml) | v1.7.1 |
| **capo** | installs OpenStack CAPI infra provider | core-component |  | [Kustomize](https://github.com/kubernetes-sigs/cluster-api-provider-openstack/releases/download/v0.10.4/infrastructure-components.yaml) | v0.10.4 |
| **capv** | installs vSphere CAPI infra provider | core-component |  | [Kustomize](https://github.com/kubernetes-sigs/cluster-api-provider-vsphere/releases/download/v1.11.0/infrastructure-components.yaml) | v1.11.0 |
| **cert-manager** | installs cert-manager, an X.509 certificate controller | core-component |  | [Helm](https://charts.jetstack.io) | v1.15.3 |
| **cluster** | holds the Cluster API definition for the cluster | core-component |  | [Helm](https://gitlab.com/sylva-projects/sylva-elements/helm-charts/sylva-capi-cluster.git) | 0.2.38 |
| **cluster-bmh** | definitions for Cluster API BareMetalHosts resources (capm3) | core-component |  | [Helm](https://gitlab.com/sylva-projects/sylva-elements/helm-charts/sylva-capi-cluster.git) | 0.2.38 |
| **flux-system** | contains Flux definitions *to manage the Flux system itself via gitops*<br/><br/>Note that Flux is always installed on the current cluster as a pre-requisite to installing the chart | core-component |  | [Kustomize](https://github.com/fluxcd/flux2/releases/download/v2.3.0/install.yaml) | v2.3.0 |
| **heat-operator** | installs OpenStack Heat operator | core-component |  | [Kustomize](https://gitlab.com/sylva-projects/sylva-elements/heat-operator.git/config/default?ref=0.0.10) | 0.0.10 |
| **kyverno** | installs Kyverno | core-component |  | [Helm](https://kyverno.github.io/kyverno) | 3.2.6 |
| **calico** | install Calico CNI | stable |  | [Helm](https://rke2-charts.rancher.io) | v3.27.200, v3.27.300 |
| **capo-contrail-bgpaas** | installs CAPO Contrail BGPaaS controller | stable |  | [Helm](https://gitlab.com/sylva-projects/sylva-elements/helm-charts/capo-contrail-bgpaas.git) | 1.0.4 |
| **cinder-csi** | installs OpenStack Cinder CSI | stable |  | [Helm](https://kubernetes.github.io/cloud-provider-openstack) | 2.30.0 |
| **cis-operator** | install CIS operator | stable |  | [Helm](https://charts.rancher.io) | 5.3.0 |
| **external-secrets-operator** | installs the External Secrets operator | stable |  | [Helm](https://charts.external-secrets.io) | 0.10.2 |
| **flux-webui** | installs Weave GitOps Flux web GUI | stable |  | [Helm](https://github.com/weaveworks/weave-gitops.git) | v0.38.0 |
| **gitea** | installs Gitea | stable |  | [Helm](https://dl.gitea.com/charts/) | 10.4.0 |
| **gitea-postgresql-ha** | installs PostgreSQL HA cluster for Gitea | stable |  | [Helm](https://charts.bitnami.com/bitnami) | 14.2.18 |
| **gitea-redis** | installs Redis cluster for Gitea | stable |  | [Helm](https://charts.bitnami.com/bitnami) | 11.0.3 |
| **harbor-postgres** | installs Postgresql for Harbor | stable |  | [Helm](https://charts.bitnami.com/bitnami) | 15.5.26 |
| **ingress-nginx** | installs Nginx ingress controller | stable |  | [Helm](https://rke2-charts.rancher.io) | 4.8.200, 4.10.102 |
| **k8s-gateway** | installs k8s gateway (coredns + plugin to resolve external service names to ingress IPs)<br/><br/>is here only to allow for DNS resolution of Ingress hosts (FQDNs), used for importing workload clusters into Rancher and for flux-webui to use Keycloak SSO | stable |  | [Helm](https://ori-edge.github.io/k8s_gateway/) | 2.4.0 |
| **keycloak** | initializes and configures Keycloak | stable |  | [Kustomize](https://raw.githubusercontent.com/keycloak/keycloak-k8s-resources/25.0.4/kubernetes/keycloaks.k8s.keycloak.org-v1.yml) | 25.0.4 |
| **keycloak-legacy-operator** | installs Keycloak "legacy" operator | stable |  | [Kustomize](https://raw.githubusercontent.com/keycloak/keycloak-realm-operator/1.0.0/deploy/crds/legacy.k8s.keycloak.org_externalkeycloaks_crd.yaml) | 1.0.0 |
| **libvirt-metal** | installs libvirt for baremetal emulation<br/><br/>this unit is used in bootstrap cluster for baremetal testing | stable |  | [Helm](https://gitlab.com/sylva-projects/sylva-elements/container-images/libvirt-metal.git) | 0.1.17 |
| **local-path-provisioner** | installs local-path CSI | stable |  | [Helm](https://github.com/rancher/local-path-provisioner.git) | v0.0.28 |
| **longhorn** | installs Longhorn CSI | stable |  | [Helm](https://charts.rancher.io/) | 103.3.1+up1.6.2 |
| **metal3** | installs SUSE-maintained Metal3 operator | stable |  | [Helm](https://suse-edge.github.io/charts) | 0.8.0 |
| **metallb** | installs MetalLB operator | stable |  | [Helm](https://metallb.github.io/metallb) | 0.14.8 |
| **monitoring** | installs monitoring stack | stable |  | [Helm](https://charts.rancher.io/) | 103.1.1+up45.31.1 |
| **multus** | installs Multus | stable |  | [Helm](https://rke2-charts.rancher.io/) | v4.0.2-build2024020802 |
| **os-image-server** | Deploys a web server on management cluster which serves OS images for baremetal clusters. | stable |  | [Helm](https://gitlab.com/sylva-projects/sylva-elements/helm-charts/os-image-server.git) | 2.1.0 |
| **postgres** | installs Postgresql for Keycloak | stable |  | [Helm](https://charts.bitnami.com/bitnami) | 15.5.26 |
| **rancher** | installs Rancher | stable |  | [Helm](https://releases.rancher.com/server-charts/latest) | 2.8.3 |
| **sriov** | installs SRIOV operator | stable |  | [Helm](https://charts.rancher.io/) | 103.0.0+up0.1.0 |
| **vault** | installs Vault<br/><br/>Vault assumes that the certificate vault-tls has been issued | stable |  | [Kustomize](https://raw.githubusercontent.com/banzaicloud/bank-vaults/1.19.0/operator/deploy/rbac.yaml) | 1.19.0 |
| **vault-config-operator** | installs Vault config operator | stable |  | [Helm](https://redhat-cop.github.io/vault-config-operator) | v0.8.29 |
| **vault-operator** | installs Vault operator | stable |  | [Helm](https://github.com/bank-vaults/vault-operator.git) | v1.22.2 |
| **vsphere-csi-driver** | installs Vsphere CSI | stable |  | [Kustomize](https://raw.githubusercontent.com/kubernetes-sigs/vsphere-csi-driver/v3.3.1/manifests/vanilla/vsphere-csi-driver.yaml) | v3.3.1 |
| **alertmanager-config** | generates the config for Alertmanager | beta |  | [Helm](https://gitlab.com/sylva-projects/sylva-elements/helm-charts/sylva-alertmanager-resources.git) | 0.0.2 |
| **alertmanager-jiralert** | installs Alertmanager webhook Jiralert<br/><br/>Jiralert is an Alertmanager wehbook that creates Jira issues | beta |  | [Helm](https://prometheus-community.github.io/helm-charts) | 1.7.1 |
| **alertmanager-jiralert-config** | generates the config for Jiralert Alertmanager webhook | beta |  | [Helm](https://gitlab.com/sylva-projects/sylva-elements/helm-charts/sylva-alertmanager-resources.git) | 0.0.2 |
| **calico-ready** | ensure Calico resources created by the Tigera operator are ready before running further steps<br/><br/>This unit will be enabled in bootstrap cluster to confirm management cluster CNI readiness and in various workload-cluster namespaces in management cluster to do the same for workload clusters | beta | True | Kustomize | N/A |
| **ceph-csi-cephfs** | Installs Ceph-CSI | beta |  | [Helm](https://ceph.github.io/csi-charts) | 3.12.1 |
| **flux-webui-init** | initializes and configures flux-webui | beta | True | Kustomize | N/A |
| **harbor** | installs Harbor | beta |  | [Helm](https://helm.goharbor.io) | 1.15.1 |
| **kube-storage-version-migrator** | installs kube-storage-version-migrator to assist apiVersion migrations | beta |  | [Kustomize](https://github.com/kubernetes-sigs/kube-storage-version-migrator/manifests?ref=v0.0.5) | v0.0.5 |
| **kubevirt** | installs kubevirt | beta |  | [Helm](https://suse-edge.github.io/charts) | 0.4.0 |
| **logging** | installs Rancher Fluentbit/Fluentd logging stack, for log collecting and shipping | beta |  | [Helm](https://charts.rancher.io/) | 103.1.2+up4.4.0 |
| **loki** | installs Loki log storage<br/><br/>installs Loki log storage in simple scalable mode | beta |  | Helm | v2.9.2 |
| **minio-monitoring-tenant** | creates a MinIO tenant for the monitoring stack<br/><br/>Loki and Thanos will use this MinIO S3 storage | beta |  | Helm | v5.0.13 |
| **minio-operator** | install MinIO operator<br/><br/>MinIO operator is used to manage multiple S3 tenants | beta |  | Helm | v5.0.13 |
| **neuvector** | installs Neuvector | beta |  | [Helm](https://neuvector.github.io/neuvector-helm) | 2.7.8 |
| **prometheus-pushgateway** | installs Prometheus Push-gateway exporter | beta |  | [Helm](https://prometheus-community.github.io/helm-charts) | 2.14.0 |
| **rancher-init** | initializes and configures Rancher | beta | True | Kustomize | N/A |
| **snmp-exporter** | installs SNMP exporter | beta |  | [Helm](https://prometheus-community.github.io/helm-charts) | 5.5.0 |
| **sylva-dashboards** | adds Sylva-specific Grafana dashboards | beta |  | [Helm](https://gitlab.com/sylva-projects/sylva-elements/helm-charts/sylva-dashboards.git) | 0.0.11 |
| **sylva-prometheus-rules** | installs prometheus rules using external helm chart & rules git repo | beta |  | [Helm](https://gitlab.com/sylva-projects/sylva-elements/helm-charts/sylva-prometheus-rules.git) | 0.0.13 |
| **sylva-thanos-rules** | installs Thanos rules using external helm chart & rules git repo | beta |  | [Helm](https://gitlab.com/sylva-projects/sylva-elements/helm-charts/sylva-thanos-rules.git) | 0.0.1 |
| **sylva-units-operator** | installs sylva-units operator | experimental |  | [Kustomize](https://gitlab.com/sylva-projects/sylva-elements/sylva-units-operator.git/config/default?ref=0.1.1) | 0.1.1 |
| **sylva-units-release-template** | create the default sylva-units-release-template used by workload-cluster CR | experimental | True | Kustomize | N/A |
| **thanos** | installs Thanos | beta |  | [Helm](https://charts.bitnami.com/bitnami) | 15.7.24 |
| **trivy-operator** | installs Trivy operator | beta |  | [Helm](https://aquasecurity.github.io/helm-charts/) | 0.24.1 |
| **workload-cluster-operator** | installs Sylva operator for managing workload clusters | experimental |  | [Kustomize](https://gitlab.com/sylva-projects/sylva-elements/workload-cluster-operator.git/config/default?ref=0.1.2) | 0.1.2 |
| **bootstrap-local-path** | installs localpath CSI in bootstrap cluster |  | True | Kustomize | N/A |
| **capd-metallb-config** | configures MetalLB in a capd context |  | True | Kustomize | N/A |
| **capi-providers-pivot-ready** | checks if management cluster is ready for pivot<br/><br/>This unit only has dependencies, but does not create resources. It is here only to have a single thing to look at to determine if everything is ready for pivot (see bootstrap.values.yaml pivot unit) |  | True | Kustomize | N/A |
| **capi-rancher-import** | installs the capi-rancher-import operator, which let's us import Cluster AIP workload clusters in management cluster's Rancher |  | True | Helm | N/A |
| **capo-cloud-config** | creates CAPO cloud-config used to produce Heat stack |  | True | Kustomize | N/A |
| **capo-cluster-resources** | installs OpenStack Heat stack for CAPO cluster prerequisites |  | True | Kustomize | N/A |
| **capo-v1alpha8-clear** | handles CAPO apiVersion v1alpha8 issues (clear CRD)<br/><br/>fixes CAPO CRDs to clear v1alpha8 from stored versions |  | True | Kustomize | N/A |
| **capo-v1alpha8-fix-crd** | handles CAPO apiVersion v1alpha8 issues (fix CRD)<br/><br/>fixes CAPO CRDs to use v1alpha7 as storage version |  | True | Kustomize | N/A |
| **capo-v1alpha8-fix-resources** | handles CAPO apiVersion v1alpha8 issues (fix resources)<br/><br/>migrates CAPO CRs from v1alpha8 back to v1alpha7 |  | True | Kustomize | N/A |
| **cis-operator-scan** | allows for running a CIS scan for management cluster<br/><br/>it generates a report which can be viewed and downloaded in CSV from the Rancher UI, at https://rancher.sylva/dashboard/c/local/cis/cis.cattle.io.clusterscan |  | True | Kustomize | N/A |
| **cluster-creator-login** | configures Rancher account used for workload cluster imports |  | True | Kustomize | N/A |
| **cluster-creator-policy** | Kyverno policy for cluster creator<br/><br/>This units defines a Kyverno policy to distribute the Kubeconfig of cluster creator<br/>in all workload cluster namespaces, to allow the import of workload clusters in<br/>Rancher. |  | True | Kustomize | N/A |
| **cluster-garbage-collector** | installs cronjob responsible for unused CAPI resources cleaning |  | True | Kustomize | N/A |
| **cluster-import** | imports workload cluster into Rancher |  | True | Kustomize | N/A |
| **cluster-machines-ready** | unit used to wait for all CAPI resources to be ready<br/><br/>This unit is here so that activity on all units is held off until all the CAPI resources are ready.<br/>This is a distinct unit from 'cluster-ready' because the readiness criteria is different: here<br/>we not only want the cluster to be ready to host some workload (which only requires some CAPI resources<br/>to be ready) we want all CAPI resources to be ready. |  | True | Kustomize | N/A |
| **cluster-node-deletion-timeout-fix** | Kyverno policy to fix CAPI nodeDeletionTimeout (temporary fix)<br/><br/>This policy fixes Machine definitions to force their spec.nodeDeletionTimeout.<br/>This is primarily meant to set this timeout to 0 (interpreted as "do infinite retries"<br/>by CAPI Machine controller), to avoid corner case issues due to a failed node<br/>deletion. See https://gitlab.com/sylva-projects/sylva-core/-/issues/1431. |  | True | Kustomize | N/A |
| **cluster-node-provider-id-blacklist** | Kyverno policy to prevent nodes from being recreated with a providerID that has already been used |  | True | Kustomize | N/A |
| **cluster-reachable** | ensure that created clusters are reachable, and make failure a bit more explicit if it is not the case<br/><br/>This unit will be enabled in bootstrap cluster to check connectivity to management cluster and in various workload-cluster namespaces in management cluster to check connectivity to workload clusters |  | True | Kustomize | N/A |
| **cluster-ready** | unit to check readiness of cluster CAPI objects<br/><br/>the healthChecks on this unit complements the one done in the 'cluster' unit, which in some cases can't cover all CAPI resources |  | True | Kustomize | N/A |
| **cluster-rke2-finalizer-fix** | Kyverno policy to clean a stray finalizer left by RKE2 on Nodes<br/><br/>Kyverno policy to delete the "wrangler.cattle.io/cisnetworkpolicy-node" finalizer<br/>that RKE2 sets on Nodes before version 1.28.9, and because it sometimes isn't<br/>removed, prevents deletion of Nodes. |  | True | Kustomize | N/A |
| **coredns** | configures DNS inside cluster |  | True | Kustomize | N/A |
| **descheduler** | install descheduler |  |  | [Helm](https://kubernetes-sigs.github.io/descheduler/) | 0.30.1 |
| **eso-secret-stores** | defines External Secrets stores |  | True | Kustomize | N/A |
| **first-login-rancher** | configure Rancher authentication for admin |  | True | Kustomize | N/A |
| **get-openstack-images** | Automatically push openstack images to Glance<br/><br/>Pushes OS images to Glance, if needed, and retrieves their UUIDs for use in cluster unit |  | True | Kustomize | N/A |
| **gitea-eso** | write secrets in gitea namespace in gitea expected format |  | True | Kustomize | N/A |
| **gitea-keycloak-resources** | deploys Gitea OIDC client in Sylva's Keycloak realm |  | True | Kustomize | N/A |
| **gitea-secrets** | create random secret that will be used by gitea application. secrets are sync with vault. |  | True | Kustomize | N/A |
| **grafana-init** | sets up Grafana certificate for Keycloak OIDC integration |  | True | Kustomize | N/A |
| **harbor-init** | sets up Harbor prerequisites<br/><br/>it generates namespace, certificate, admin password, OIDC configuration |  | True | Kustomize | N/A |
| **keycloak-add-client-scope** | configures Keycloak client-scope<br/><br/>a job to manually add a custom client-scope to sylva realm (on top of default ones) while CRD option does not yet provide good results (overrides defaults) |  | True | Kustomize | N/A |
| **keycloak-add-realm-role** | Creates Keycloak realm role<br/><br/>a job to manually create a custom realm role to sylva realm (on top of default ones) and assigns it to sylva-admin while CRD option does not allow updates. |  | True | Kustomize | N/A |
| **keycloak-add-truststore** | configures Keycloak truststore<br/><br/>a job to manually add a truststore to Keycloak instance, e.h. to enable LDAPS protocol when using user federation) |  | True | Kustomize | N/A |
| **keycloak-oidc-external-secrets** | configures OIDC secrets for Keycloak |  | True | Kustomize | N/A |
| **keycloak-resources** | configures keycloak resources |  | True | Kustomize | N/A |
| **kubevirt-manager** | deploys kubevirt-manager UI for kubevirt workloads |  | True | Kustomize | N/A |
| **kubevirt-test-vms** | deploys kubevirt VMs for testing |  | True | Kustomize | N/A |
| **kyverno-policies** | configures Kyverno policies |  | True | Kustomize | N/A |
| **kyverno-policy-prevent-mgmt-cluster-delete** | Kyverno policies to prevent deletion of critical resources for mgmt cluster |  | True | Kustomize | N/A |
| **kyverno-update-namespace-and-psa** | grants to Kyverno the permission to update namespaces using the "updatepsa" verb (Rancher-specific)<br/><br/>This unit allows Kyverno to define namespaces with specific PodSecurityAdmission levels. It is useful for situations where namespaces need to be mutated (with PSA labels) in order to accomodate privileged pods (for which PSA level restricted at cluster level is not enough), when namespace creation is not controlled |  | True | Kustomize | N/A |
| **logging-config** | Configures rancher-logging to ship logs to Loki |  | True | Kustomize | N/A |
| **loki-init** | sets up Loki certificate<br/><br/>it generate certificate |  | True | Kustomize | N/A |
| **longhorn-instance-manager-cleanup** | cronjob to cleanup Longhorn instance-manager pods that are preventing node drain |  | True | Kustomize | N/A |
| **management-cluster-configs** | copies configuration object in management cluster during bootstrap |  | True | Kustomize | N/A |
| **management-cluster-flux** | installs flux in management cluster during bootstrap |  | True | Kustomize | N/A |
| **management-flag** | dummy unit to identify management cluster<br/><br/>This unit will produce a configmap in management cluster that can be used by apply scripts to assert that they are properly targeting the management cluster |  | True | Kustomize | N/A |
| **management-namespace-defs** | creates sylva-system namespace in management cluster |  | True | Kustomize | N/A |
| **management-sylva-units** | installs sylva-units in management cluster during bootstrap |  | True | Helm | N/A |
| **metal3-automated-cleanup-fix** | fix metal3MachineTemplates produced by sylva-capi-cluster version =< 0.2.14 in sylva release =< 1.1.0 |  | True | Kustomize | N/A |
| **metal3-pdb** | add pdb to baremetal-operator pods |  | True | Kustomize | N/A |
| **mgmt-cluster-ready** | (workload cluster) this unit reflects the readiness of the mgmt cluster<br/><br/>this unit acts as simple dependency lock to prevent deploying a workload cluster before the mgmt cluster is ready |  | True | Kustomize | N/A |
| **minio-monitoring-tenant-init** | sets up MinIO certificate for minio-monitoring-tenant<br/><br/>it generate certificate |  | True | Kustomize | N/A |
| **minio-operator-init** | sets up MinIO certificate for minio-operator<br/><br/>it generate certificate |  | True | Kustomize | N/A |
| **multus-ready** | checks that Multus is ready<br/><br/>This unit only has dependencies, it does not create resources. It performs healthchecks outside of the multus unit, in order to properly target workload cluster when we deploy multus in it. |  | True | Kustomize | N/A |
| **namespace-defs** | creates sylva-system namespace and other namespaces to be used by various units |  | True | Kustomize | N/A |
| **neuvector-init** | sets up Neuvector prerequisites<br/><br/>it generates namespace, certificate, admin password, policy exception for using latest tag images (required for the pod managing the database of vulnerabilities since this DB is updated often) |  | True | Kustomize | N/A |
| **os-images-info** | Creates a list of os images<br/><br/>This unit creates a configmap containing the os images (and their details in the case of Sylva diskimage-builder ones)<br/>to be further served by os-image-server |  | True | Kustomize | N/A |
| **pivot** | moves ClusterAPI objects from bootstrap cluster to management cluster |  | True | Kustomize | N/A |
| **prometheus-flux** | Prometheus configuration for Flux controllers & resources<br/><br/>Adding podmonitors for flux controllers and custom labels to the flux resource metrics by configuring kube-state-metrics |  | True | Kustomize | N/A |
| **prometheus-resources** | Creates required ConfigMaps and Kyverno policies to enable SNMP monitoring by Prometheus |  | True | Kustomize | N/A |
| **rancher-keycloak-oidc-provider** | configures Rancher for Keycloak OIDC integration |  | True | Kustomize | N/A |
| **rancher-monitoring-clusterid-inject** | injects Rancher cluster ID in Helm values of Rancher monitoring chart |  | True | Kustomize | N/A |
| **root-dependency** | special unit ensuring ordered updates of all Kustomizations<br/><br/>All Kustomizations will depend on this Kustomization, whose name is `root-dependency-<n>` and changes at each update of the sylva-units Helm release. This Kustomization does not become ready before all other Kustomizations have been updated. All this ensures in a race-free way that during an update, units will be reconciled in an order matching dependency declarations. |  | True | Kustomize | N/A |
| **sandbox-privileged-namespace** | creates the sandbox namespace used to perform privileged operations like debugging a node |  | True | Kustomize | N/A |
| **shared-workload-clusters-settings** | manages parameters which would be shared between management and workload clusters |  | True | Kustomize | N/A |
| **single-replica-storageclass** | Create a longhorn storage class with a single replica |  | True | Kustomize | N/A |
| **sriov-resources** | configures SRIOV resources |  | True | Helm | N/A |
| **sylva-ca** | provides a Certificate Authority for units of the Sylva stack |  | True | Kustomize | N/A |
| **synchronize-secrets** | allows secrets from Vault to be consumed other units, relies on ExternalSecrets |  | True | Kustomize | N/A |
| **thanos-init** | sets up thanos certificate<br/><br/>it generates a multiple CN certificate for all Thanos components |  | True | Kustomize | N/A |
| **tigera-clusterrole** | is here to allow for upgrading Calico chart when upgrading cluster<br/><br/>For v1.25.x to v1.26.x, see https://gitlab.com/sylva-projects/sylva-core/-/issues/664 |  | True | Kustomize | N/A |
| **vault-oidc** | configures Vault to be used with OIDC |  | True | Kustomize | N/A |
| **vault-secrets** | generates random secrets in vault, configure password policy, authentication backends, etc... |  | True | Kustomize | N/A |
| **vsphere-cpi** | configures Vsphere Cloud controller manager |  | True | Helm | N/A |
