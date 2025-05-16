## Units for software components integrated into Sylva

<!-- markdownlint-disable MD044 -->
| name | full description | maturity | source | version |
| :----- | :----- | :----- | :----- | :----- |
| **cabpk** | installs Kubeadm CAPI bootstrap provider | core-component | [Kustomization](https://github.com/kubernetes-sigs/cluster-api/releases/download/v1.8.6/bootstrap-components.yaml) | v1.8.6 |
| **cabpr** | installs RKE2 CAPI bootstrap provider | core-component | [Kustomization](https://github.com/rancher/cluster-api-provider-rke2/releases/download/v0.7.1/bootstrap-components.yaml) | v0.7.1 |
| **capd** | installs Docker CAPI infra provider | core-component | [Kustomization](https://github.com/kubernetes-sigs/cluster-api//test/infrastructure/docker/config/default/?ref=v1.8.6) | v1.8.6 |
| **capi** | installs Cluster API core operator | core-component | [Kustomization](https://github.com/kubernetes-sigs/cluster-api/releases/download/v1.8.6/core-components.yaml) | v1.8.6 |
| **capm3** | installs Metal3 CAPI infra provider, for baremetal | core-component | [Kustomization](https://github.com/metal3-io/cluster-api-provider-metal3/releases/download/v1.8.3/infrastructure-components.yaml) | v1.8.3 |
| **capo** | installs OpenStack CAPI infra provider | core-component | [Kustomization](https://github.com/kubernetes-sigs/cluster-api-provider-openstack/releases/download/v0.11.6/infrastructure-components.yaml) | v0.11.6 |
| **capv** | installs vSphere CAPI infra provider | core-component | [Kustomization](https://github.com/kubernetes-sigs/cluster-api-provider-vsphere/releases/download/v1.12.0/infrastructure-components.yaml) | v1.12.0 |
| **cert-manager** | installs cert-manager, an X.509 certificate controller | core-component | [Helm chart](https://charts.jetstack.io) | v1.15.4 |
| **flux-system** | contains Flux definitions *to manage the Flux system itself via gitops*<br/><br/>Note that Flux is always installed on the current cluster as a pre-requisite to installing the chart | core-component | Kustomization |  |
| **kyverno** | installs Kyverno | core-component | [Helm chart](https://kyverno.github.io/kyverno) | 3.3.9 |
| **calico** | install Calico CNI | stable | [Helm chart](https://rke2-charts.rancher.io) | v3.28.200, v3.29.200 |
| **cinder-csi** | installs OpenStack Cinder CSI | stable | [Helm chart](https://kubernetes.github.io/cloud-provider-openstack) | 2.31.2 |
| **cis-operator** | install CIS operator | stable | [Helm chart](https://charts.rancher.io) | 105.0.0+up7.0.0 |
| **cnpg-operator** | Cloud Native PostgreSQL (CNPG) Operator | stable | [Helm chart](https://cloudnative-pg.github.io/charts) | 0.22.1 |
| **external-secrets-operator** | installs the External Secrets operator | stable | [Helm chart](https://charts.external-secrets.io) | 0.10.4 |
| **flux-webui** | installs Weave GitOps Flux web GUI | stable | [Helm chart](https://github.com/weaveworks/weave-gitops.git) | v0.38.0 |
| **gitea** | installs Gitea | stable | [Helm chart](https://dl.gitea.com/charts/) | 10.4.1 |
| **gitea-postgresql-ha** | installs PostgreSQL HA cluster for Gitea | stable | [Helm chart](https://github.com/bitnami/charts.git) | postgresql-ha/14.2.30 |
| **gitea-redis** | installs Redis cluster for Gitea | stable | [Helm chart](https://github.com/bitnami/charts.git) | redis-cluster/11.0.8 |
| **harbor-postgres** | installs Postgresql for Harbor | stable | [Helm chart](https://github.com/bitnami/charts.git) | postgresql/15.5.36 |
| **ingress-nginx** | installs Nginx ingress controller | stable | [Helm chart](https://rke2-charts.rancher.io) | 4.10.501, 4.12.003 |
| **k8s-gateway** | installs k8s gateway (coredns + plugin to resolve external service names to ingress IPs)<br/><br/>is here only to allow for DNS resolution of Ingress hosts (FQDNs), used for importing workload clusters into Rancher and for flux-webui to use Keycloak SSO | stable | [Helm chart](https://ori-edge.github.io/k8s_gateway/) | 2.4.0 |
| **kepler** | installs Kepler (Kubernetes-based Efficient Power Level Exporter) exporter for Prometheus | stable | [Helm chart](https://sustainable-computing-io.github.io/kepler-helm-chart) | 0.5.12 |
| **keycloak** | initializes and configures Keycloak | stable | [Kustomization](https://raw.githubusercontent.com/keycloak/keycloak-k8s-resources/26.0.8/kubernetes/keycloaks.k8s.keycloak.org-v1.yml) | 26.0.8 |
| **keycloak-legacy-operator** | installs Keycloak "legacy" operator | stable | [Kustomization](https://raw.githubusercontent.com/keycloak/keycloak-realm-operator/1.0.0/deploy/crds/legacy.k8s.keycloak.org_externalkeycloaks_crd.yaml) | 1.0.0 |
| **local-path-provisioner** | installs local-path CSI | stable | [Helm chart](https://github.com/rancher/local-path-provisioner.git) | v0.0.31 |
| **longhorn** | installs Longhorn CSI | stable | [Helm chart](https://charts.rancher.io/) | 104.2.2+up1.7.3 |
| **metal3** | installs SUSE-maintained Metal3 operator | stable | [Helm chart](https://suse-edge.github.io/charts) | 0.8.3 |
| **metallb** | installs MetalLB operator | stable | [Helm chart](https://metallb.github.io/metallb) | 0.14.9 |
| **monitoring** | installs monitoring stack | stable | [Helm chart](https://charts.rancher.io/) | 104.1.2+up57.0.3 |
| **multus** | installs Multus | stable | [Helm chart](https://rke2-charts.rancher.io/) | v4.1.001 |
| **postgres** | installs Postgresql for Keycloak | stable | [Helm chart](https://github.com/bitnami/charts.git) | postgresql/15.5.36 |
| **rancher** | installs Rancher | stable | [Helm chart](https://releases.rancher.com/server-charts/stable) | 2.9.3 |
| **sriov-network-operator** | installs SR-IOV operator | stable | [Helm chart](https://suse-edge.github.io/charts/) | 1.3.0 |
| **vault** | installs Vault<br/><br/>Vault assumes that the certificate vault-tls has been issued | stable | [Kustomization](https://raw.githubusercontent.com/banzaicloud/bank-vaults/1.19.0/operator/deploy/rbac.yaml) | 1.19.0 |
| **vault-config-operator** | installs Vault config operator | stable | [Helm chart](https://redhat-cop.github.io/vault-config-operator) | v0.8.29 |
| **vault-operator** | installs Vault operator | stable | [Helm chart](https://github.com/bank-vaults/vault-operator.git) | v1.22.3 |
| **vsphere-csi-driver** | installs Vsphere CSI | stable | [Kustomization](https://raw.githubusercontent.com/kubernetes-sigs/vsphere-csi-driver/v3.3.1/manifests/vanilla/vsphere-csi-driver.yaml) | v3.3.1 |
| **alertmanager-jiralert** | installs Alertmanager webhook Jiralert<br/><br/>Jiralert is an Alertmanager wehbook that creates Jira issues | beta | [Helm chart](https://prometheus-community.github.io/helm-charts) | 1.7.2 |
| **cabpoa** | installs OKD/OpenShift CAPI bootstrap/controlplane provider | experimental | [Kustomization](https://github.com/openshift-assisted/cluster-api-agent/releases/download/v0.2.0/bootstrap-components.yaml) | v0.2.0 |
| **ceph-csi-cephfs** | Installs Ceph-CSI | beta | [Helm chart](https://ceph.github.io/csi-charts) | 3.12.3 |
| **harbor** | installs Harbor | beta | [Helm chart](https://helm.goharbor.io) | 1.15.2 |
| **kubevirt** | installs kubevirt | beta | [Helm chart](https://suse-edge.github.io/charts) | 0.4.0 |
| **kubevirt-cdi** | manages Kubevirt CDI - Container Data Importer | beta | [Helm chart](https://suse-edge.github.io/charts) | 0.4.0 |
| **logging** | installs Rancher Fluentbit/Fluentd logging stack, for log collecting and shipping | beta | [Helm chart](https://charts.rancher.io/) | 103.1.2+up4.4.0 |
| **loki** | installs Loki log storage<br/><br/>installs Loki log storage in simple scalable mode | beta | [Helm chart](https://github.com/grafana/loki.git) | v3.3.2 |
| **minio-logging** | creates a MinIO tenant for the logging stack, used as S3 storage by Loki | beta | [Helm chart](https://github.com/minio/operator.git) | v5.0.16 |
| **minio-monitoring** | creates a MinIO tenant for the monitoring stack, used as S3 storage by Thanos | beta | [Helm chart](https://github.com/minio/operator.git) | v5.0.16 |
| **minio-operator** | install MinIO operator<br/><br/>MinIO operator is used to manage multiple S3 tenants | beta | [Helm chart](https://github.com/minio/operator.git) | v5.0.16 |
| **neuvector** | installs Neuvector | beta | [Helm chart](https://neuvector.github.io/neuvector-helm) | 2.8.3 |
| **nfs-ganesha** | manages NFS Ganesha CSI provisioner | experimental | [Helm chart](https://kubernetes-sigs.github.io/nfs-ganesha-server-and-external-provisioner/) | 1.8.0 |
| **openshift-assisted-installer** | installs assisted installer operator for OKD | experimental | [Kustomization](https://raw.githubusercontent.com/openshift/assisted-service/v2.33.0/hack/crds/hive.openshift.io_clusterdeployments.yaml) | v2.33.0 |
| **prometheus-pushgateway** | installs Prometheus Push-gateway exporter | beta | [Helm chart](https://prometheus-community.github.io/helm-charts) | 2.15.0 |
| **snmp-exporter** | installs SNMP exporter | beta | [Helm chart](https://prometheus-community.github.io/helm-charts) | 5.6.0 |
| **thanos** | installs Thanos | beta | [Helm chart](https://github.com/bitnami/charts.git) | thanos/15.8.0 |
| **trivy-operator** | installs Trivy operator | beta | [Helm chart](https://aquasecurity.github.io/helm-charts/) | 0.24.1 |
| **descheduler** | install descheduler |  | [Helm chart](https://kubernetes-sigs.github.io/descheduler/) | 0.31.0 |

## Units for operators, tools or Helm charts maintained in Sylva project

<!-- markdownlint-disable MD044 -->
| name | full description | source | version |
| :----- | :----- | :----- | :----- |
| **cluster** | holds the Cluster API definition for the cluster | [Helm chart](https://gitlab.com/sylva-projects/sylva-elements/helm-charts/sylva-capi-cluster.git) | 0.4.21 |
| **cluster-bmh** | definitions for Cluster API BareMetalHosts resources (capm3) | [Helm chart](https://gitlab.com/sylva-projects/sylva-elements/helm-charts/sylva-capi-cluster.git) | 0.4.21 |
| **heat-operator** | installs OpenStack Heat operator | [Kustomization](https://gitlab.com/sylva-projects/sylva-elements/heat-operator.git/config/default?ref=0.0.11) | 0.0.11 |
| **capo-contrail-bgpaas** | installs CAPO Contrail BGPaaS controller | [Helm chart](https://gitlab.com/sylva-projects/sylva-elements/helm-charts/capo-contrail-bgpaas.git) | 1.0.4 |
| **libvirt-metal** | installs libvirt for baremetal emulation<br/><br/>this unit is used in bootstrap cluster for baremetal testing | [Helm chart](https://gitlab.com/sylva-projects/sylva-elements/container-images/libvirt-metal.git) | 0.1.22 |
| **os-image-server** | Deploys a web server on management cluster which serves OS images for baremetal clusters. | [Helm chart](https://gitlab.com/sylva-projects/sylva-elements/helm-charts/os-image-server.git) | 2.1.4 |
| **alertmanager-config** | generates the config for Alertmanager | [Helm chart](https://gitlab.com/sylva-projects/sylva-elements/helm-charts/sylva-alertmanager-resources.git) | 0.0.3 |
| **alertmanager-jiralert-config** | generates the config for Jiralert Alertmanager webhook | [Helm chart](https://gitlab.com/sylva-projects/sylva-elements/helm-charts/sylva-alertmanager-resources.git) | 0.0.3 |
| **sylva-dashboards** | adds Sylva-specific Grafana dashboards | [Helm chart](https://gitlab.com/sylva-projects/sylva-elements/helm-charts/sylva-dashboards.git) | 0.0.14 |
| **sylva-logging-flows** | configures logging flows and output to export the platform logs to an external server | [Helm chart](https://gitlab.com/sylva-projects/sylva-elements/helm-charts/sylva-logging-flows.git) | 0.0.1 |
| **sylva-prometheus-rules** | installs prometheus rules using external helm chart & rules git repo | [Helm chart](https://gitlab.com/sylva-projects/sylva-elements/helm-charts/sylva-prometheus-rules.git) | 0.0.15 |
| **sylva-thanos-rules** | installs Thanos rules using external helm chart & rules git repo | [Helm chart](https://gitlab.com/sylva-projects/sylva-elements/helm-charts/sylva-thanos-rules.git) | 0.0.3 |
| **sylva-units-operator** | installs sylva-units operator | [Kustomization](https://gitlab.com/sylva-projects/sylva-elements/sylva-units-operator.git/config/default?ref=v0.1.6) | v0.1.6 |
| **workload-cluster-operator** | installs Sylva operator for managing workload clusters | [Kustomization](https://gitlab.com/sylva-projects/sylva-elements/workload-cluster-operator.git/config/default?ref=0.1.3) | 0.1.3 |
| **workload-team-defs** | installs the workload-team-defs chart<br/><br/>installs the workload-team-defs chart to install the workload cluster through CRD | [Helm chart](https://gitlab.com/sylva-projects/sylva-elements/helm-charts/workload-team-defs.git) | 0.1.1 |

## Units internal to Sylva

<!-- markdownlint-disable MD044 -->
| name | full description | source |
| :----- | :----- | :----- |
| **bootstrap-local-path** | installs localpath CSI in bootstrap cluster | Kustomization |
| **calico-ready** | ensure Calico resources created by the Tigera operator are ready before running further steps<br/><br/>This unit will be enabled in bootstrap cluster to confirm management cluster CNI readiness and in various workload-cluster namespaces in management cluster to do the same for workload clusters | Kustomization |
| **calico-rke2-chart-cleanup** | remove rke2-deployed HelmChart resources for Calico | Kustomization |
| **capi-providers-pivot-ready** | checks if management cluster is ready for pivot<br/><br/>This unit only has dependencies, but does not create resources. It is here only to have a single thing to look at to determine if everything is ready for pivot (see bootstrap.values.yaml pivot unit) | Kustomization |
| **capi-rancher-import** | installs the capi-rancher-import operator, which let's us import Cluster AIP workload clusters in management cluster's Rancher | Helm chart |
| **capo-cloud-config** | creates CAPO cloud-config used to produce Heat stack | Kustomization |
| **capo-cluster-resources** | installs OpenStack Heat stack for CAPO cluster prerequisites | Kustomization |
| **cis-operator-scan** | allows for running a CIS scan for management cluster<br/><br/>it generates a report which can be viewed and downloaded in CSV from the Rancher UI, at https://rancher.sylva/dashboard/c/local/cis/cis.cattle.io.clusterscan | Kustomization |
| **cluster-creator-login** | configures Rancher account used for workload cluster imports | Kustomization |
| **cluster-creator-policy** | Kyverno policy for cluster creator<br/><br/>This units defines a Kyverno policy to distribute the Kubeconfig of cluster creator<br/>in all workload cluster namespaces, to allow the import of workload clusters in<br/>Rancher. | Kustomization |
| **cluster-garbage-collector** | installs cronjob responsible for unused CAPI resources cleaning | Kustomization |
| **cluster-import** | imports workload cluster into Rancher | Kustomization |
| **cluster-machines-ready** | unit used to wait for all CAPI resources to be ready<br/><br/>This unit is here so that activity on all units is held off until all the CAPI resources are ready.<br/>This is a distinct unit from 'cluster-ready' because the readiness criteria is different: here<br/>we not only want the cluster to be ready to host some workload (which only requires some CAPI resources<br/>to be ready) we want all CAPI resources to be ready. | Kustomization |
| **cluster-node-deletion-timeout-fix** | Kyverno policy to fix CAPI nodeDeletionTimeout (temporary fix)<br/><br/>This policy fixes Machine definitions to force their spec.nodeDeletionTimeout.<br/>This is primarily meant to set this timeout to 0 (interpreted as "do infinite retries"<br/>by CAPI Machine controller), to avoid corner case issues due to a failed node<br/>deletion. See https://gitlab.com/sylva-projects/sylva-core/-/issues/1431. | Kustomization |
| **cluster-node-provider-id-blacklist** | Kyverno policy to prevent nodes from being recreated with a providerID that has already been used | Kustomization |
| **cluster-prevent-rke2-helmcharts-calico-metallb** | Kyverno policy to prevent RKE2 HelmCharts from being recreated for MetaLB and Calico | Kustomization |
| **cluster-reachable** | ensure that created clusters are reachable, and make failure a bit more explicit if it is not the case<br/><br/>This unit will be enabled in bootstrap cluster to check connectivity to management cluster and in various workload-cluster namespaces in management cluster to check connectivity to workload clusters | Kustomization |
| **cluster-ready** | unit to check readiness of cluster CAPI objects<br/><br/>the healthChecks on this unit complements the one done in the 'cluster' unit, which in some cases can't cover all CAPI resources | Kustomization |
| **cluster-vip** | Defines the cluster-vip Service for MetalLB load-balancing<br/><br/>MetalLB will only handle the VIP if it has a corresponding service with endpoints, but we don't want that the API access (6443) relies on kube-proxy, because on RKE2 agent nodes, kube-proxy uses RKE2 internal load-balancing proxy that may fall-back to the VIP to access the API, which could create a deadlock if endpoints are not up-to-date.<br/>The cluster-vip Service that plays this role. This unit manages this resource, taking over the control after the initial creation of this Service by a cloud-init post command on the first node). | Kustomization |
| **coredns** | configures DNS inside cluster | Kustomization |
| **eso-secret-stores** | defines External Secrets stores | Kustomization |
| **first-login-rancher** | configure Rancher authentication for admin | Kustomization |
| **flux-webui-init** | initializes and configures flux-webui | Kustomization |
| **get-openstack-images** | Automatically push openstack images to Glance<br/><br/>Pushes OS images to Glance, if needed, and retrieves their UUIDs for use in cluster unit | Kustomization |
| **gitea-eso** | write secrets in gitea namespace in gitea expected format | Kustomization |
| **gitea-keycloak-resources** | deploys Gitea OIDC client in Sylva's Keycloak realm | Kustomization |
| **gitea-secrets** | create random secret that will be used by gitea application. secrets are sync with vault. | Kustomization |
| **grafana-init** | sets up Grafana certificate for Keycloak OIDC integration | Kustomization |
| **harbor-init** | sets up Harbor prerequisites<br/><br/>it generates namespace, certificate, admin password, OIDC configuration | Kustomization |
| **keycloak-add-client-scope** | configures Keycloak client-scope<br/><br/>a job to manually add a custom client-scope to sylva realm (on top of default ones) while CRD option does not yet provide good results (overrides defaults) | Kustomization |
| **keycloak-add-realm-role** | Creates Keycloak realm role<br/><br/>a job to manually create a custom realm role to sylva realm (on top of default ones) and assigns it to sylva-admin while CRD option does not allow updates. | Kustomization |
| **keycloak-add-truststore** | configures Keycloak truststore<br/><br/>a job to manually add a truststore to Keycloak instance, e.h. to enable LDAPS protocol when using user federation) | Kustomization |
| **keycloak-oidc-external-secrets** | configures OIDC secrets for Keycloak | Kustomization |
| **keycloak-postgres** | Deploy Postgres cluster for Keycloak using Cloud Native PostgreSQL (CNPG) | Kustomization |
| **keycloak-resources** | configures keycloak resources | Kustomization |
| **kube-storage-version-migrator** | installs kube-storage-version-migrator to assist apiVersion migrations | Kustomization |
| **kubevirt-manager** | deploys kubevirt-manager UI for kubevirt workloads | Kustomization |
| **kubevirt-test-vms** | deploys kubevirt VMs for testing | Kustomization |
| **kyverno-metal3-policies** | kyverno policies specific to capm3-system | Kustomization |
| **kyverno-policies** | configures Kyverno policies | Kustomization |
| **kyverno-policies-ready** | additional delay to ensure that kyverno webhooks are properly installed in api-server | Kustomization |
| **kyverno-policy-prevent-mgmt-cluster-delete** | Kyverno policies to prevent deletion of critical resources for mgmt cluster | Kustomization |
| **kyverno-policy-rancher-webhook-ha** | Kyverno policy for rancher-webhook HA | Kustomization |
| **kyverno-update-namespace-and-psa** | grants to Kyverno the permission to update namespaces using the "updatepsa" verb (Rancher-specific)<br/><br/>This unit allows Kyverno to define namespaces with specific PodSecurityAdmission levels. It is useful for situations where namespaces need to be mutated (with PSA labels) in order to accomodate privileged pods (for which PSA level restricted at cluster level is not enough), when namespace creation is not controlled | Kustomization |
| **kyverno-vault-restart-policy** | restart vault after certs renewal | Kustomization |
| **logging-config** | Configures rancher-logging to ship logs to Loki | Kustomization |
| **loki-credentials-secret** | create a secret containing tenant's loki credentials | Kustomization |
| **loki-init** | sets up Loki certificate<br/><br/>it generate certificate | Kustomization |
| **longhorn-engine-image-cleanup** | kyverno cleanup policy to delete old Longhorn engineimages that are left-over after upgrade | Kustomization |
| **longhorn-instance-manager-cleanup** | cronjob to cleanup Longhorn instance-manager pods that are preventing node drain | Kustomization |
| **management-cluster-configs** | copies configuration object in management cluster during bootstrap | Kustomization |
| **management-cluster-flux** | installs flux in management cluster during bootstrap | Kustomization |
| **management-flag** | dummy unit to identify management cluster<br/><br/>This unit will produce a configmap in management cluster that can be used by apply scripts to assert that they are properly targeting the management cluster | Kustomization |
| **management-namespace-defs** | creates sylva-system namespace in management cluster | Kustomization |
| **management-sylva-units** | installs sylva-units in management cluster during bootstrap | Helm chart |
| **metal3-pdb** | add pdb to baremetal-operator pods | Kustomization |
| **metallb-resources** | configures metallb resources | Helm chart |
| **mgmt-cluster-ready** | (workload cluster) this unit reflects the readiness of the mgmt cluster<br/><br/>this unit acts as simple dependency lock to prevent deploying a workload cluster before the mgmt cluster is ready | Kustomization |
| **minio-logging-init** | sets up secrets and certificates for minio-logging | Kustomization |
| **minio-monitoring-init** | sets up secrets and certificates for minio-monitoring | Kustomization |
| **minio-operator-init** | sets up MinIO certificate for minio-operator<br/><br/>it generate certificate | Kustomization |
| **multus-ready** | checks that Multus is ready<br/><br/>This unit only has dependencies, it does not create resources. It performs healthchecks outside of the multus unit, in order to properly target workload cluster when we deploy multus in it. | Kustomization |
| **namespace-defs** | creates sylva-system namespace and other namespaces to be used by various units | Kustomization |
| **neuvector-init** | sets up Neuvector prerequisites<br/><br/>it generates namespace, certificate, admin password, policy exception for using latest tag images (required for the pod managing the database of vulnerabilities since this DB is updated often) | Kustomization |
| **nfs-ganesha-init** | Define persistent volume claim for NFS Ganesha | Kustomization |
| **os-images-info** | Creates a list of os images<br/><br/>This unit creates a configmap containing the os images (and their details in the case of Sylva diskimage-builder ones)<br/>to be further served by os-image-server | Kustomization |
| **pivot** | moves ClusterAPI objects from bootstrap cluster to management cluster | Kustomization |
| **prometheus-custom-metrics** | Prometheus configuration for custom resource metrics<br/><br/>Adding podmonitors for flux controllers and create custom metrics for various resources by configuring kube-state-metrics | Kustomization |
| **prometheus-resources** | Creates required ConfigMaps and Kyverno policies to enable SNMP monitoring by Prometheus | Kustomization |
| **rancher-custom-roles** | configures custom roles for Rancher | Kustomization |
| **rancher-default-roles** | Create Rancher role templates<br/><br/>This unit creates a set of additional role templates which are likely to be needed by many<br/>clusters. | Kustomization |
| **rancher-init** | initializes and configures Rancher | Kustomization |
| **rancher-keycloak-oidc-provider** | configures Rancher for Keycloak OIDC integration | Kustomization |
| **rancher-monitoring-clusterid-inject** | injects Rancher cluster ID in Helm values of Rancher monitoring chart | Kustomization |
| **refresh-metal3machinetemplates** | Recreate metal3machinetemplates resources via the reconciliation of cluster helmrelease | Kustomization |
| **rke2-helmchart-prevent-uninstall** | Kyverno policy to prevent key Helm charts from being uninstalled by RKE2 HelmChart controller | Kustomization |
| **root-dependency** | special unit ensuring ordered updates of all Kustomizations<br/><br/>All Kustomizations will depend on this Kustomization, whose name is `root-dependency-<n>` and changes at each update of the sylva-units Helm release. This Kustomization does not become ready before all other Kustomizations have been updated.<br/>This unit also manages the `root-dependency-<n>` HelmRelease that acts as a lock to prevent HelmReleases from reconciling before units they depend on are ready.<br/>All this ensures in a race-free way that during an update, units will be reconciled in an order matching dependency declarations. | Helm chart |
| **sandbox-privileged-namespace** | creates the sandbox namespace used to perform privileged operations like debugging a node | Kustomization |
| **shared-workload-clusters-settings** | manages parameters which would be shared between management and workload clusters | Kustomization |
| **single-replica-storageclass** | DEPRECATED longhorn storage class with a single replica<br/><br/>This unit is preserved for migration purposes, it will be removed after sylva 1.2 release<br/>Single replicas PVC were causing data replication churn during rolling updates of nodes<br/>See https://gitlab.com/sylva-projects/sylva-core/-/issues/1648 | Kustomization |
| **sriov** | obsolete - replaced by sriov-network-operator<br/><br/>dummy unit which only enables sriov-network-operator for backwark compatibility | Kustomization |
| **sriov-resources** | configures SRIOV resources | Helm chart |
| **sylva-ca** | configures the Certificate Authority for units of the Sylva stack | Kustomization |
| **synchronize-secrets** | allows secrets from Vault to be consumed other units, relies on ExternalSecrets | Kustomization |
| **test-nfs-ganesha** | Perform testing for RWX enabled PVs created from NFS Ganesha | Kustomization |
| **thanos-credentials-secret** | create a secret containing tenant's thanos credentials | Kustomization |
| **thanos-init** | sets up thanos certificate<br/><br/>it generates a multiple CN certificate for all Thanos components | Kustomization |
| **two-replicas-storageclass** | Create a longhorn storage class with a two replicas | Kustomization |
| **vault-oidc** | configures Vault to be used with OIDC | Kustomization |
| **vault-secrets** | generates random secrets in vault, configure password policy, authentication backends, etc... | Kustomization |
| **vsphere-cpi** | configures Vsphere Cloud controller manager | Helm chart |
