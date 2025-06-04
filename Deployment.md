## Canonical Kubernetes deployment with Sylva


### Prepare the environment

```bash

git clone https://gitlab.com/sylva-projects/sylva-core
cd sylva-core

```

### Deploy the managenement cluster


Run ./bootstrap.sh:

```bash

BOOTSTRAP_WATCH_TIMEOUT_MIN=200 ./bootstrap.sh environment-values/ck8s-capm3-virt/

```

Logs of the deployment:

```bash
📥 Installing sylva-toolbox binaries

🔎 Validate input files

🔃 Preparing bootstrap cluster
Creating kind cluster with following config:
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
networking:
  podSubnet: "100.100.0.0/16"
  serviceSubnet: "100.96.0.0/16"
nodes:
  - role: control-plane
    extraMounts:
      - hostPath: /home/avladu/projects/sylva-core-latest/tools/kind/systemd/nomasquerade.service
        containerPath: /etc/systemd/system/nomasquerade.service
      - hostPath: /home/avladu/projects/sylva-core-latest/tools/kind/systemd/iptables.sh
        containerPath: /usr/local/bin/iptables.sh
Creating cluster "sylva" ...
 ✓ Ensuring node image (kindest/node:v1.31.0) 🖼
 ✓ Preparing nodes 📦
 ✓ Writing configuration 📜
 ✓ Starting control-plane 🕹️
 ✓ Installing CNI 🔌
 ✓ Installing StorageClass 💾
Set kubectl context to "kind-sylva"
You can now use your cluster with:

kubectl cluster-info --context kind-sylva

Not sure what to do next? 😅  Check out https://kind.sigs.k8s.io/docs/user/quick-start/
Created symlink /etc/systemd/system/multi-user.target.wants/nomasquerade.service → /etc/systemd/system/nomasquerade.service.

🔃 Install flux
namespace/flux-system created
resourcequota/critical-pods-flux-system created
customresourcedefinition.apiextensions.k8s.io/buckets.source.toolkit.fluxcd.io created
customresourcedefinition.apiextensions.k8s.io/gitrepositories.source.toolkit.fluxcd.io created
customresourcedefinition.apiextensions.k8s.io/helmcharts.source.toolkit.fluxcd.io created
customresourcedefinition.apiextensions.k8s.io/helmreleases.helm.toolkit.fluxcd.io created
customresourcedefinition.apiextensions.k8s.io/helmrepositories.source.toolkit.fluxcd.io created
customresourcedefinition.apiextensions.k8s.io/kustomizations.kustomize.toolkit.fluxcd.io created
customresourcedefinition.apiextensions.k8s.io/ocirepositories.source.toolkit.fluxcd.io created
customresourcedefinition.apiextensions.k8s.io/helmreleases.helm.toolkit.fluxcd.io created
customresourcedefinition.apiextensions.k8s.io/helmrepositories.source.toolkit.fluxcd.io created
customresourcedefinition.apiextensions.k8s.io/kustomizations.kustomize.toolkit.fluxcd.io created
customresourcedefinition.apiextensions.k8s.io/ocirepositories.source.toolkit.fluxcd.io created
serviceaccount/helm-controller created
serviceaccount/kustomize-controller created
serviceaccount/source-controller created
clusterrole.rbac.authorization.k8s.io/crd-controller-flux-system created
clusterrole.rbac.authorization.k8s.io/flux-edit-flux-system created
clusterrole.rbac.authorization.k8s.io/flux-view-flux-system created
clusterrolebinding.rbac.authorization.k8s.io/cluster-reconciler-flux-system created
clusterrolebinding.rbac.authorization.k8s.io/crd-controller-flux-system created
service/source-controller created
deployment.apps/helm-controller created
deployment.apps/kustomize-controller created
deployment.apps/source-controller created
networkpolicy.networking.k8s.io/allow-egress created
networkpolicy.networking.k8s.io/allow-scraping created
networkpolicy.networking.k8s.io/allow-webhooks created

⏳ Wait for Flux to be ready...
deployment.apps/helm-controller condition met
deployment.apps/kustomize-controller condition met
deployment.apps/source-controller condition met

🔎 Validate sylva-units values for management cluster
[INFO] Using 8d7aa74bf3e7c800368ad47de891143ce1d501f3
namespace/sylva-units-preview created
configmap/capm3-virt-ha-values created
configmap/capm3-virt-values created
configmap/sylva-units-values created
secret/sylva-units-secrets created
helmrelease.helm.toolkit.fluxcd.io/sylva-units created
gitrepository.source.toolkit.fluxcd.io/sylva-units created
trigger reconciliation of sylva-units HelmRelease...
  helmrelease.helm.toolkit.fluxcd.io/sylva-units annotated
not using --resume-suspended
 ✓ GitRepository/sylva-units - Resource is ready
 ✓ HelmChart/sylva-units-preview-sylva-units - Resource is ready
 ✓ HelmRelease/sylva-units - Resource is ready
 ✓ All Done: resource HelmRelease/sylva-units-preview/sylva-units is ready!

🗑 Delete preview chart and namespace for management cluster
helmrelease.helm.toolkit.fluxcd.io/sylva-units
gitrepository.source.toolkit.fluxcd.io/sylva-core
namespace "sylva-units-preview" deleted
Context "kind-sylva" modified.
📜 Install sylva-units Helm release and associated resources
[INFO] Using 8d7aa74bf3e7c800368ad47de891143ce1d501f3
namespace/sylva-system created
configmap/sylva-units-values created
configmap/capm3-virt-ha-values created
configmap/capm3-virt-values created
secret/sylva-units-secrets created
helmrelease.helm.toolkit.fluxcd.io/sylva-units created
gitrepository.source.toolkit.fluxcd.io/sylva-units created

🎯 Trigger reconciliation of units
trigger reconciliation of sylva-units HelmRelease...
  helmrelease.helm.toolkit.fluxcd.io/sylva-units annotated
 ✓ GitRepository/sylva-units - Resource is ready
 ✓ HelmChart/sylva-system-sylva-units - Resource is ready
 ✓ HelmRelease/sylva-units - Resource is ready
 ✓ All Done: resource HelmRelease/sylva-system/sylva-units is ready!

⏳ Wait for bootstrap units and management cluster to be ready
 ✓ GitRepository/sylva-core - Resource is ready
 ✓ GitRepository/sylva-core - Resource is ready
 ✓ HelmChart/sylva-system-cluster - Resource is ready
 ✓ HelmChart/sylva-system-cluster-bmh - Resource is ready
 ✓ HelmChart/sylva-system-libvirt-metal - Resource is ready
 ✓ HelmChart/sylva-system-os-image-server - Resource is ready
 ✓ HelmRelease/cluster - Resource is ready
 ✓ HelmRelease/cluster-bmh - Resource is ready
 ✓ HelmRelease/libvirt-metal - Resource is ready
 ✓ HelmRelease/os-image-server - Resource is ready: OS images are served at URLs like: https://127.0.0.1/<filename>(.sha256sum)
 ✓ HelmRepository/unit-cert-manager - Resource is ready
 ✓ HelmRepository/unit-external-secrets-operator - Resource is ready
 ✓ HelmRepository/unit-ingress-nginx - Resource is ready
 ✓ HelmRepository/unit-kyverno - Resource is ready
 ✓ HelmRepository/unit-metal3 - Resource is ready
 ✓ HelmRepository/unit-multus - Resource is ready
 ✓ Kustomization/bootstrap-local-path - Resource is ready
 ✓ Kustomization/cert-manager - Resource is ready
 ✓ Kustomization/external-secrets-operator - Resource is ready
 ✓ Kustomization/kyverno - Resource is ready
 ✓ Kustomization/kyverno-policies - Resource is ready
 ✓ Kustomization/multus - Resource is ready
 ✓ Kustomization/multus-ready - Resource is ready
 ✓ Kustomization/namespace-defs - Resource is ready
 ✓ Kustomization/os-images-info - Resource is ready
 ✓ Kustomization/sylva-ca - Resource is ready
 ✓ HelmChart/sylva-system-cert-manager - Resource is ready
 ✓ HelmChart/sylva-system-external-secrets-operator - Resource is ready
 ✓ HelmChart/sylva-system-ingress-nginx - Resource is ready
 ✓ HelmChart/sylva-system-kyverno - Resource is ready
 ✓ HelmChart/sylva-system-metal3 - Resource is ready
 ✓ HelmChart/sylva-system-multus - Resource is ready
 ✓ HelmRelease/cert-manager - Resource is ready
  ✓ HelmRepository/unit-external-secrets-operator - Resource is ready
 ✓ HelmRepository/unit-ingress-nginx - Resource is ready
 ✓ HelmRepository/unit-kyverno - Resource is ready
 ✓ HelmRepository/unit-longhorn - Resource is ready
 ✓ HelmRepository/unit-longhorn-crd - Resource is ready
 ✓ HelmRepository/unit-metal3 - Resource is ready
 ✓ HelmRepository/unit-multus - Resource is ready
 ✓ Kustomization/bootstrap-local-path - Resource is ready
 ✓ Kustomization/cert-manager - Resource is ready
 ✓ Kustomization/external-secrets-operator - Resource is ready
 ✓ Kustomization/kyverno - Resource is ready
 ✓ Kustomization/kyverno-policies - Resource is ready
 ✓ Kustomization/multus - Resource is ready
 ✓ Kustomization/multus-ready - Resource is ready
 ✓ Kustomization/namespace-defs - Resource is ready
 ✓ Kustomization/os-images-info - Resource is ready
 ✓ Kustomization/sylva-ca - Resource is ready
 ✓ HelmChart/sylva-system-cert-manager - Resource is ready
 ✓ HelmChart/sylva-system-external-secrets-operator - Resource is ready
 ✓ HelmChart/sylva-system-ingress-nginx - Resource is ready
 ✓ HelmChart/sylva-system-kyverno - Resource is ready
 ✓ HelmChart/sylva-system-longhorn - Resource is ready
 ✓ HelmChart/sylva-system-longhorn-crd - Resource is ready
 ✓ HelmChart/sylva-system-metal3 - Resource is ready
 ✓ HelmChart/sylva-system-multus - Resource is ready
 ✓ HelmRelease/cert-manager - Resource is ready
 ✓ HelmRelease/external-secrets-operator - Resource is ready
 ✓ HelmRelease/ingress-nginx - Resource is ready
 ✓ HelmRelease/kyverno - Resource is ready
 ✓ HelmRelease/longhorn-crd - Resource is ready
 ✓ HelmRelease/metal3 - Resource is ready
 ✓ HelmRelease/multus - Resource is ready
 ✓ Kustomization/cabpck - Resource is ready
 ✓ Kustomization/capi - Resource is ready
 ✓ Kustomization/ingress-nginx-init - Resource is ready
 ✓ Kustomization/metal3-sylva-ca-init - Resource is ready
 ✓ Kustomization/ingress-nginx - Resource is ready
 ✓ Kustomization/libvirt-metal - Resource is ready
 ✓ Kustomization/metal3 - Resource is ready
 ✓ Kustomization/os-image-server - Resource is ready: OS images are served at URLs like: https://127.0.0.1/<filename>(.sha256sum)
 ✓ Kustomization/capm3 - Resource is ready
 ✓ Kustomization/kyverno-metal3-policies - Resource is ready
 ✓ Kustomization/cluster-bmh - Resource is ready
 ✓ Kustomization/cluster - Resource is ready
 ✓ Kustomization/cluster-reachable - Resource is ready
 ✓ Kustomization/cluster-ready - Resource is ready
 ✓ Kustomization/management-namespace-defs - Resource is ready
 ✓ Kustomization/cluster-machines-ready - Resource is ready
 ✓ Kustomization/longhorn-crd - Resource is ready
 ✓ Kustomization/longhorn - Resource is ready
 ✓ Kustomization/management-cluster-flux - Resource is ready
 ✓ Kustomization/management-cluster-configs - Resource is ready
 ✓ Kustomization/management-sylva-units - Resource is ready
 ✓ All Done: resource Kustomization/sylva-system/management-sylva-units is ready!

⏳ Wait for units installed on management cluster to be ready
I0604 08:45:26.676918   37967 request.go:752] "Waited before sending request" delay="1.197561502s" reason="client-side throttling, not priority and fairness" verb="PATCH" URL=""
I0604 08:57:03.628849   37967 request.go:752] "Waited before sending request" delay="1.19726786s" reason="client-side throttling, not priority and fairness" verb="PATCH" URL="h"
 ✓ GitRepository/bitnami-postgresql - Resource is ready
 ✓ GitRepository/bitnami-thanos - Resource is ready
 ✓ GitRepository/devnull - Resource is ready
 ✓ GitRepository/local-path-provisioner - Resource is ready
 ✓ GitRepository/minio-operator - Resource is ready
 ✓ GitRepository/os-image-server - Resource is ready
 ✓ GitRepository/sylva-alertmanager-resources - Resource is ready
 ✓ GitRepository/sylva-capi-cluster - Resource is ready
 ✓ GitRepository/sylva-core - Resource is ready
 ✓ GitRepository/sylva-dashboards - Resource is ready
 ✓ GitRepository/sylva-prometheus-rules - Resource is ready
 ✓ GitRepository/sylva-snmp-resources - Resource is ready
 ✓ GitRepository/sylva-thanos-rules - Resource is ready
 ✓ GitRepository/vault-operator - Resource is ready
 ✓ GitRepository/weave-gitops - Resource is ready
 ✓ GitRepository/workload-team-defs - Resource is ready
 ✓ HelmChart/sylva-system-alertmanager-config - Resource is ready
 ✓ HelmChart/sylva-system-cluster - Resource is ready
 ✓ HelmChart/sylva-system-cluster-bmh - Resource is ready
 ✓ HelmChart/sylva-system-flux-webui - Resource is ready
 ✓ HelmChart/sylva-system-harbor-postgres - Resource is ready
 ✓ HelmChart/sylva-system-local-path-provisioner - Resource is ready
 ✓ HelmChart/sylva-system-minio-monitoring - Resource is ready
 ✓ HelmChart/sylva-system-minio-operator - Resource is ready
 ✓ HelmChart/sylva-system-os-image-server - Resource is ready
 ✓ HelmChart/sylva-system-root-dependency-2 - Resource is ready
 ✓ HelmChart/sylva-system-snmp-exporter-config - Resource is ready
 ✓ HelmChart/sylva-system-sylva-dashboards - Resource is ready
 ✓ HelmChart/sylva-system-sylva-prometheus-rules - Resource is ready
 ✓ HelmChart/sylva-system-sylva-thanos-rules - Resource is ready
 ✓ HelmChart/sylva-system-thanos - Resource is ready
 ✓ HelmChart/sylva-system-vault-operator - Resource is ready
 ✓ HelmChart/sylva-system-workload-team-defs - Resource is ready
 ✓ HelmRelease/root-dependency-2 - Resource is ready
 ✓ HelmRelease/snmp-exporter-config - Resource is ready
 ✓ HelmRelease/sylva-dashboards - Resource is ready
 ✓ HelmRelease/sylva-prometheus-rules - Resource is ready
 ✓ HelmRelease/sylva-thanos-rules - Resource is ready
 ✓ HelmRelease/thanos - Resource is ready: Thanos UI can be reached at https://thanos.172.18.0.2.nip.io (thanos.172.18.0.2.nip.io must resolve to 192.168.100.2)
  ✓ HelmRelease/vault-operator - Resource is ready
 ✓ HelmRelease/workload-team-defs - Resource is ready
 ✓ HelmRepository/unit-calico - Resource is ready
 ✓ HelmRepository/unit-calico-crd - Resource is ready
 ✓ HelmRepository/unit-cert-manager - Resource is ready
 ✓ HelmRepository/unit-cnpg-operator - Resource is ready
 ✓ HelmRepository/unit-crossplane - Resource is ready
 ✓ HelmRepository/unit-external-secrets-operator - Resource is ready
 ✓ HelmRepository/unit-harbor - Resource is ready
 ✓ HelmRepository/unit-ingress-nginx - Resource is ready
 ✓ HelmRepository/unit-k8s-gateway - Resource is ready
 ✓ HelmRepository/unit-kyverno - Resource is ready
 ✓ HelmRepository/unit-longhorn - Resource is ready
 ✓ HelmRepository/unit-longhorn-crd - Resource is ready
 ✓ HelmRepository/unit-metal3 - Resource is ready
 ✓ HelmRepository/unit-monitoring - Resource is ready
 ✓ HelmRepository/unit-monitoring-crd - Resource is ready
 ✓ HelmRepository/unit-prometheus-pushgateway - Resource is ready
 ✓ HelmRepository/unit-rancher - Resource is ready
 ✓ HelmRepository/unit-rancher-turtles - Resource is ready
 ✓ HelmRepository/unit-snmp-exporter - Resource is ready
 ✓ HelmRepository/unit-vault-config-operator - Resource is ready
 ✓ Kustomization/root-dependency-2 - Resource is ready
 ✓ Kustomization/validating-admission-policies - Resource is ready
 ✓ HelmChart/sylva-system-calico - Resource is ready
 ✓ HelmChart/sylva-system-calico-crd - Resource is ready
 ✓ HelmChart/sylva-system-cert-manager - Resource is ready
 ✓ HelmChart/sylva-system-cnpg-operator - Resource is ready
 ✓ HelmChart/sylva-system-crossplane - Resource is ready
 ✓ HelmChart/sylva-system-external-secrets-operator - Resource is ready
 ✓ HelmChart/sylva-system-harbor - Resource is ready
 ✓ HelmChart/sylva-system-ingress-nginx - Resource is ready
 ✓ HelmChart/sylva-system-k8s-gateway - Resource is ready
 ✓ HelmChart/sylva-system-kyverno - Resource is ready
 ✓ HelmChart/sylva-system-longhorn - Resource is ready
 ✓ HelmChart/sylva-system-longhorn-crd - Resource is ready
 ✓ HelmChart/sylva-system-metal3 - Resource is ready
 ✓ HelmChart/sylva-system-monitoring - Resource is ready
 ✓ HelmChart/sylva-system-monitoring-crd - Resource is ready
 ✓ HelmChart/sylva-system-prometheus-pushgateway - Resource is ready
 ✓ HelmChart/sylva-system-rancher - Resource is ready
 ✓ HelmChart/sylva-system-rancher-turtles - Resource is ready
 ✓ HelmChart/sylva-system-snmp-exporter - Resource is ready
 ✓ HelmChart/sylva-system-vault-config-operator - Resource is ready
 ✓ HelmRelease/alertmanager-config - Resource is ready
 ✓ HelmRelease/calico - Resource is ready
 ✓ HelmRelease/calico-crd - Resource is ready
 ✓ HelmRelease/cert-manager - Resource is ready
 ✓ HelmRelease/cluster - Resource is ready
 
 
 ✓ HelmRelease/cluster-bmh - Resource is ready
 ✓ HelmRelease/cnpg-operator - Resource is ready
 ✓ HelmRelease/crossplane - Resource is ready
 ✓ HelmRelease/external-secrets-operator - Resource is ready
 ✓ HelmRelease/flux-webui - Resource is ready: Flux Web UI can be reached at https://flux.172.18.0.2.nip.io (It must resolve to 192.168.100.2)
 ✓ HelmRelease/harbor - Resource is ready: Harbor UI can be reached at https://harbor.172.18.0.2.nip.io (It must resolve to 192.168.100.2)
 ✓ HelmRelease/harbor-postgres - Resource is ready
 ✓ HelmRelease/ingress-nginx - Resource is ready
 ✓ HelmRelease/k8s-gateway - Resource is ready
 ✓ HelmRelease/kyverno - Resource is ready
 ✓ HelmRelease/local-path-provisioner - Resource is ready
 ✓ HelmRelease/longhorn - Resource is ready
 ✓ HelmRelease/longhorn-crd - Resource is ready
 ✓ HelmRelease/metal3 - Resource is ready
 ✓ HelmRelease/minio-monitoring - Resource is ready: MinIO monitoring tenant console can be reached at https://minio-monitoring-console.172.18.0.2.nip.io (It must resolve to 192.168.100.2)
 ✓ HelmRelease/minio-operator - Resource is ready: minio operator console can be reached at https://minio-operator-console.172.18.0.2.nip.io (It must resolve to 192.168.100.2)
 ✓ HelmRelease/monitoring - Resource is ready: Grafana UI can be reached at https://grafana.172.18.0.2.nip.io (grafana.172.18.0.2.nip.io must resolve to 192.168.100.2)
 ✓ HelmRelease/monitoring-crd - Resource is ready
 ✓ HelmRelease/os-image-server - Resource is ready: OS images are served at URLs like: https://192.168.100.2/<filename>(.sha256sum)
 ✓ HelmRelease/prometheus-pushgateway - Resource is ready
 ✓ HelmRelease/rancher - Resource is ready: Rancher UI can be reached at https://rancher.172.18.0.2.nip.io (It must resolve to 192.168.100.2)
 ✓ HelmRelease/rancher-turtles - Resource is ready
 ✓ HelmRelease/snmp-exporter - Resource is ready
 ✓ HelmRelease/vault-config-operator - Resource is ready
 ✓ Kustomization/flux-system - Resource is ready
 ✓ Kustomization/management-flag - Resource is ready
 ✓ Kustomization/namespace-defs - Resource is ready
 ✓ Kustomization/monitoring-crd - Resource is ready
 ✓ Kustomization/kyverno - Resource is ready
 ✓ Kustomization/kyverno-policies - Resource is ready
 ✓ Kustomization/longhorn-crd - Resource is ready
 ✓ Kustomization/longhorn-instance-manager-cleanup - Resource is ready
 ✓ Kustomization/metal3-pdb - Resource is ready
 ✓ Kustomization/os-images-info - Resource is ready
 ✓ Kustomization/calico-crd - Resource is ready
 ✓ Kustomization/cert-manager - Resource is ready
 ✓ Kustomization/cluster-node-provider-id-blacklist - Resource is ready
 ✓ Kustomization/external-secrets-operator - Resource is ready
 ✓ Kustomization/longhorn - Resource is ready
 ✓ Kustomization/sylva-ca - Resource is ready
 ✓ Kustomization/cabpck - Resource is ready
 ✓ Kustomization/calico - Resource is ready
 ✓ Kustomization/capi - Resource is ready
 ✓ Kustomization/cluster-node-deletion-timeout-fix - Resource is ready
 ✓ Kustomization/ingress-nginx-init - Resource is ready
 ✓ Kustomization/metal3-sylva-ca-init - Resource is ready
 ✓ Kustomization/ingress-nginx - Resource is ready


 ✓ Kustomization/metal3 - Resource is ready
 ✓ Kustomization/os-image-server - Resource is ready: OS images are served at URLs like: https://192.168.100.2/<filename>(.sha256sum)
 ✓ Kustomization/capm3 - Resource is ready
 ✓ Kustomization/kyverno-metal3-policies - Resource is ready
 ✓ Kustomization/cluster-bmh - Resource is ready
 ✓ Kustomization/cluster - Resource is ready
 ✓ Kustomization/cluster-ready - Resource is ready
 ✓ Kustomization/cluster-machines-ready - Resource is ready
 ✓ Kustomization/cnpg-operator - Resource is ready
 ✓ Kustomization/coredns - Resource is ready
 ✓ Kustomization/crossplane-init - Resource is ready
 ✓ Kustomization/flux-webui-init - Resource is ready
 ✓ Kustomization/grafana-init - Resource is ready
 ✓ Kustomization/k8s-gateway - Resource is ready
 ✓ Kustomization/keycloak-postgres - Resource is ready
 ✓ Kustomization/kyverno-policies-ready - Resource is ready
 ✓ Kustomization/kyverno-policy-prevent-mgmt-cluster-delete - Resource is ready
 ✓ Kustomization/local-path-provisioner - Resource is ready
 ✓ Kustomization/longhorn-engine-image-cleanup - Resource is ready
 ✓ Kustomization/minio-operator-init - Resource is ready
 ✓ Kustomization/prometheus-custom-metrics - Resource is ready
 ✓ Kustomization/prometheus-resources - Resource is ready
 ✓ Kustomization/rancher-init - Resource is ready
 ✓ Kustomization/refresh-metal3machinetemplates - Resource is ready
 ✓ Kustomization/single-replica-storageclass - Resource is ready
 ✓ Kustomization/snmp-exporter-config - Resource is ready
 ✓ Kustomization/sylva-units-operator - Resource is ready
 ✓ Kustomization/thanos-credentials-secret - Resource is ready
 ✓ Kustomization/two-replicas-storageclass - Resource is ready
 ✓ Kustomization/vault-config-operator - Resource is ready
 ✓ Kustomization/vault-operator - Resource is ready
 ✓ Kustomization/workload-cluster-operator - Resource is ready
 ✓ Kustomization/workload-team-defs - Resource is ready
 ✓ Kustomization/alertmanager-config - Resource is ready
 ✓ Kustomization/capi-providers-pivot-ready - Resource is ready
 ✓ Kustomization/cluster-garbage-collector - Resource is ready
 ✓ Kustomization/crossplane - Resource is ready
 ✓ Kustomization/mgmt-cluster-state-values - Resource is ready
 ✓ Kustomization/minio-operator - Resource is ready: minio operator console can be reached at https://minio-operator-console.172.18.0.2.nip.io (It must resolve to 192.168.100.2
 ✓ Kustomization/vault - Resource is ready: Vault UI can be reached at https://vault.172.18.0.2.nip.io (It must resolve to 192.168.100.2)
 
 ✓ Kustomization/vault-secrets - Resource is ready
 ✓ Kustomization/eso-secret-stores - Resource is ready
 ✓ Kustomization/kyverno-vault-restart-policy - Resource is ready
 ✓ Kustomization/minio-monitoring-init - Resource is ready
 ✓ Kustomization/synchronize-secrets - Resource is ready
 ✓ Kustomization/thanos-init - Resource is ready
 ✓ Kustomization/thanos-statefulsets-cleanup - Resource is ready
 ✓ Kustomization/keycloak - Resource is ready: Keycloak admin console can be reached at https://keycloak.172.18.0.2.nip.io/admin/master/console, user 'admin', password in Vault at secret/keycloak (It must resolve to 192.168.100.2)
 ✓ Kustomization/keycloak-legacy-operator - Resource is ready
 ✓ Kustomization/keycloak-resources - Resource is ready
 ✓ Kustomization/minio-monitoring - Resource is ready: MinIO monitoring tenant console can be reached at https://minio-monitoring-console.172.18.0.2.nip.io (It must resolve to 192.168.100.2)
 ✓ Kustomization/rancher - Resource is ready: Rancher UI can be reached at https://rancher.172.18.0.2.nip.io (It must resolve to 192.168.100.2)
 ✓ Kustomization/rancher-custom-roles - Resource is ready
 ✓ Kustomization/rancher-default-roles - Resource is ready
 ✓ Kustomization/rancher-monitoring-clusterid-inject - Resource is ready
 ✓ Kustomization/rancher-turtles - Resource is ready
 ✓ Kustomization/sylva-thanos-rules - Resource is ready
 ✓ Kustomization/thanos - Resource is ready: Thanos UI can be reached at https://thanos.172.18.0.2.nip.io (thanos.172.18.0.2.nip.io must resolve to 192.168.100.2)
 ✓ Kustomization/vault-oidc - Resource is ready
 ✓ Kustomization/first-login-rancher - Resource is ready
 ✓ Kustomization/keycloak-add-client-scope - Resource is ready
 ✓ Kustomization/keycloak-add-realm-role - Resource is ready
 ✓ Kustomization/keycloak-oidc-external-secrets - Resource is ready
 ✓ Kustomization/monitoring - Resource is ready: Grafana UI can be reached at https://grafana.172.18.0.2.nip.io (grafana.172.18.0.2.nip.io must resolve to 192.168.100.2)
 ✓ Kustomization/prometheus-pushgateway - Resource is ready
 ✓ Kustomization/rancher-keycloak-oidc-provider - Resource is ready
 ✓ Kustomization/snmp-exporter - Resource is ready
 ✓ Kustomization/sylva-dashboards - Resource is ready
 ✓ Kustomization/sylva-prometheus-rules - Resource is ready
 ✓ Kustomization/flux-webui - Resource is ready: Flux Web UI can be reached at https://flux.172.18.0.2.nip.io (It must resolve to 192.168.100.2)
 ✓ Kustomization/harbor-init - Resource is ready
 ✓ Kustomization/harbor-postgres - Resource is ready
 ✓ Kustomization/harbor - Resource is ready: Harbor UI can be reached at https://harbor.172.18.0.2.nip.io (It must resolve to 192.168.100.2)
 ✓ Kustomization/sylva-units-status - Resource is ready
 ✓ All Done: resource Kustomization/sylva-system/sylva-units-status is ready!


✔ Sylva is ready, everything deployed in management cluster
   Management cluster nodes:
NAME                                 STATUS   ROLES                  AGE   VERSION
management-cluster-management-cp-0   Ready    control-plane,worker   44m   v1.31.6
management-cluster-management-cp-1   Ready    control-plane,worker   27m   v1.31.6
management-cluster-management-cp-2   Ready    control-plane,worker   35m   v1.31.6
management-cluster-management-md-0   Ready    worker                 34m   v1.31.6

🌱 You can access following UIs
* flux-webui - Flux Web UI can be reached at https://flux.172.18.0.2.nip.io (It must resolve to 192.168.100.2)
* harbor - Harbor UI can be reached at https://harbor.172.18.0.2.nip.io (It must resolve to 192.168.100.2)
* monitoring - Grafana UI can be reached at https://grafana.172.18.0.2.nip.io (grafana.172.18.0.2.nip.io must resolve to 192.168.100.2)
* rancher - Rancher UI can be reached at https://rancher.172.18.0.2.nip.io (It must resolve to 192.168.100.2)
* thanos - Thanos UI can be reached at https://thanos.172.18.0.2.nip.io (thanos.172.18.0.2.nip.io must resolve to 192.168.100.2)
* vault - Vault UI can be reached at https://vault.172.18.0.2.nip.io (It must resolve to 192.168.100.2)

🎉 All done
```

Verify the bootstrap cluster nodes:

```bash

$: kubectl get node -A

NAME                  STATUS   ROLES           AGE   VERSION
sylva-control-plane   Ready    control-plane   77m   v1.31.0
```

Verify the bootstrap cluster pods:

```bash
$: kubectl get pod -A

NAMESPACE            NAME                                                         READY   STATUS      RESTARTS   AGE
cabpck-system        cabpck-bootstrap-controller-manager-57f7cf8cff-qn5hv         2/2     Running     0          73m
cacpck-system        cacpck-controller-manager-67f45d67b-qhh7t                    1/1     Running     0          73m
capi-system          capi-controller-manager-79dd77688-6j79n                      1/1     Running     0          73m
capm3-system         capm3-controller-manager-585bb4c989-ntvlf                    1/1     Running     0          70m
capm3-system         ipam-controller-manager-5c7dd5df4f-tcpff                     1/1     Running     0          70m
cert-manager         cert-manager-67bf4568c6-kvp2z                                1/1     Running     0          75m
cert-manager         cert-manager-cainjector-689d8fd7f7-mxwlz                     1/1     Running     0          75m
cert-manager         cert-manager-webhook-5f5cc99d7f-frm9r                        1/1     Running     0          75m
external-secrets     external-secrets-operator-67fcc88947-54dvh                   1/1     Running     0          75m
external-secrets     external-secrets-operator-cert-controller-55d8747c6d-cbg9n   1/1     Running     0          75m
external-secrets     external-secrets-operator-webhook-5cfc4578cb-rxcn9           1/1     Running     0          75m
flux-system          helm-controller-5c666cd9c9-7tnlf                             1/1     Running     0          77m
flux-system          kustomize-controller-578b46c68c-scwck                        1/1     Running     0          77m
flux-system          source-controller-687579d548-m22pn                           1/1     Running     0          77m
kube-system          coredns-6f6b679f8f-psghq                                     1/1     Running     0          77m
kube-system          coredns-6f6b679f8f-rpdmv                                     1/1     Running     0          77m
kube-system          etcd-sylva-control-plane                                     1/1     Running     0          77m
kube-system          kindnet-5rhw4                                                1/1     Running     0          77m
kube-system          kube-apiserver-sylva-control-plane                           1/1     Running     0          77m
kube-system          kube-controller-manager-sylva-control-plane                  1/1     Running     0          77m
kube-system          kube-proxy-qg2dx                                             1/1     Running     0          77m
kube-system          kube-scheduler-sylva-control-plane                           1/1     Running     0          77m
kube-system          multus-26jqz                                                 1/1     Running     0          75m
kube-system          multus-rke2-whereabouts-bplzz                                1/1     Running     0          75m
kube-system          rke2-ingress-nginx-controller-pbzd6                          1/1     Running     0          73m
kyverno              kyverno-admission-controller-868cdcc9fd-jrrtd                1/1     Running     0          75m
kyverno              kyverno-background-controller-59fddcc8d-zw7pm                1/1     Running     0          75m
kyverno              kyverno-cleanup-controller-6cc758444d-856nc                  1/1     Running     0          75m
kyverno              kyverno-reports-controller-f8bc788f9-tctm2                   1/1     Running     0          75m
local-path-storage   local-path-provisioner-ccc7bf7fc-zlnrv                       1/1     Running     0          77m
os-images            ubuntu-noble-plain-ck8s-1-31-6-0                             1/1     Running     0          72m
sylva-system         cluster-machines-ready-zxbh7                                 0/1     Completed   0          47m
sylva-system         libvirt-metal-management-cp-0-0                              3/3     Running     0          72m
sylva-system         libvirt-metal-management-cp-1-0                              3/3     Running     0          72m
sylva-system         libvirt-metal-management-cp-2-0                              3/3     Running     0          72m
sylva-system         libvirt-metal-management-md-0-0                              3/3     Running     0          72m
sylva-system         libvirt-metal-workload-cp-0-0                                3/3     Running     0          72m
sylva-system         libvirt-metal-workload-cp-1-0                                3/3     Running     0          72m
sylva-system         libvirt-metal-workload-cp-2-0                                3/3     Running     0          72m
sylva-system         libvirt-metal-workload-md-0-0                                3/3     Running     0          72m
sylva-system         management-cluster-configs-wzpbp                             0/1     Completed   0          53m
sylva-system         os-images-info-pnzp9                                         0/1     Completed   0          74m
sylva-system         pivot-7dmbn                                                  0/1     Completed   0          39m
```

Verify the management cluster nodes:

```bash
$: kubectl --kubeconfig management-cluster-kubeconfig get node -A

NAME                                 STATUS   ROLES                  AGE   VERSION
management-cluster-management-cp-0   Ready    control-plane,worker   56m   v1.31.6
management-cluster-management-cp-1   Ready    control-plane,worker   39m   v1.31.6
management-cluster-management-cp-2   Ready    control-plane,worker   47m   v1.31.6
management-cluster-management-md-0   Ready    worker                 47m   v1.31.6
```


Verify the management cluster pods:

```bash
$: kubectl --kubeconfig management-cluster-kubeconfig get pod -A

NAMESPACE                          NAME                                                           READY   STATUS      RESTARTS      AGE
cabpck-system                      cabpck-bootstrap-controller-manager-57f7cf8cff-4lhn2           2/2     Running     0             35m
cacpck-system                      cacpck-controller-manager-67f45d67b-qmhq6                      1/1     Running     0             35m
calico-system                      calico-kube-controllers-6b8799c556-7t5h8                       1/1     Running     0             56m
calico-system                      calico-node-bqr2x                                              1/1     Running     0             40m
calico-system                      calico-node-d2xt4                                              1/1     Running     0             48m
calico-system                      calico-node-fdwck                                              1/1     Running     0             48m
calico-system                      calico-node-vgnqv                                              1/1     Running     0             56m
calico-system                      calico-typha-7c8bb65b8f-bdl46                                  1/1     Running     0             56m
calico-system                      calico-typha-7c8bb65b8f-zswgz                                  1/1     Running     0             48m
capi-system                        capi-controller-manager-79dd77688-nstmg                        1/1     Running     0             35m
capi-system                        capi-controller-manager-79dd77688-rhsbm                        1/1     Running     0             35m
capm3-system                       capm3-controller-manager-796944f5c6-bnhsz                      1/1     Running     0             31m
capm3-system                       capm3-controller-manager-796944f5c6-jkdsk                      1/1     Running     0             31m
capm3-system                       ipam-controller-manager-7487967d67-s788h                       1/1     Running     0             31m
capm3-system                       ipam-controller-manager-7487967d67-zjhg4                       1/1     Running     0             31m
cattle-fleet-local-system          fleet-agent-0                                                  2/2     Running     0             16m
cattle-fleet-system                fleet-controller-8899ffb8b-72f7r                               3/3     Running     0             20m
cattle-fleet-system                gitjob-74f56c4cb7-zvv44                                        1/1     Running     0             20m
cattle-monitoring-system           alertmanager-rancher-monitoring-alertmanager-0                 2/2     Running     0             17m
cattle-monitoring-system           alertmanager-rancher-monitoring-alertmanager-1                 2/2     Running     0             17m
cattle-monitoring-system           rancher-monitoring-grafana-9dbff487f-jmr8w                     3/3     Running     0             17m
cattle-monitoring-system           rancher-monitoring-kube-state-metrics-745f7f98c9-4cjvx         1/1     Running     0             17m
cattle-monitoring-system           rancher-monitoring-operator-7f66845b68-j8bsk                   1/1     Running     0             17m
cattle-monitoring-system           rancher-monitoring-prometheus-adapter-5d559f65c8-dspw8         1/1     Running     0             17m
cattle-monitoring-system           rancher-monitoring-prometheus-node-exporter-h6kk9              1/1     Running     0             17m
cattle-monitoring-system           rancher-monitoring-prometheus-node-exporter-n94sl              1/1     Running     0             17m
cattle-monitoring-system           rancher-monitoring-prometheus-node-exporter-q9knw              1/1     Running     0             17m
cattle-monitoring-system           rancher-monitoring-prometheus-node-exporter-xtjj5              1/1     Running     0             17m
cattle-system                      helm-operation-7szwx                                           0/2     Completed   0             17m
cattle-system                      helm-operation-jr5zx                                           0/2     Completed   0             19m
cattle-system                      helm-operation-qlbkk                                           0/2     Completed   0             19m
cattle-system                      helm-operation-rqm75                                           0/2     Completed   0             20m
cattle-system                      helm-operation-zvjpp                                           0/2     Completed   0             16m
cattle-system                      rancher-5b8b485fdd-4ktrs                                       1/1     Running     0             22m
cattle-system                      rancher-5b8b485fdd-c6tvq                                       1/1     Running     0             22m
cattle-system                      rancher-5b8b485fdd-g8lhz                                       1/1     Running     0             24m
cattle-system                      rancher-webhook-56d5cdb4f-psl5c                                1/1     Running     0             18m
cattle-system                      rancher-webhook-56d5cdb4f-zp6pv                                1/1     Running     0             18m
cert-manager                       cert-manager-67bf4568c6-7mgg9                                  1/1     Running     0             37m
cert-manager                       cert-manager-67bf4568c6-zl5vt                                  1/1     Running     0             37m
cert-manager                       cert-manager-cainjector-689d8fd7f7-mhsmp                       1/1     Running     0             37m
cert-manager                       cert-manager-cainjector-689d8fd7f7-zxl7k                       1/1     Running     0             37m
cert-manager                       cert-manager-webhook-5f5cc99d7f-8p4mw                          1/1     Running     0             37m
cert-manager                       cert-manager-webhook-5f5cc99d7f-j4q5j                          1/1     Running     0             37m
cert-manager                       cert-manager-webhook-5f5cc99d7f-j5cdl                          1/1     Running     0             37m
cnpg-system                        cnpg-operator-cloudnative-pg-7dff548b47-rplrv                  1/1     Running     0             37m
crossplane-system                  crossplane-8689dff669-pzkzz                                    1/1     Running     0             34m

crossplane-system                  crossplane-8689dff669-pzkzz                                    1/1     Running     0             35m
crossplane-system                  crossplane-rbac-manager-68d6586bc8-kgt94                       1/1     Running     0             35m
external-secrets                   external-secrets-operator-67fcc88947-pv6h8                     1/1     Running     0             37m
external-secrets                   external-secrets-operator-cert-controller-55d8747c6d-w68hv     1/1     Running     0             37m
external-secrets                   external-secrets-operator-webhook-5cfc4578cb-wzjr7             1/1     Running     0             37m
flux-system                        flux-webui-weave-gitops-55f45474d8-wfw4x                       1/1     Running     0             18m
flux-system                        helm-controller-747c7bdfcb-f6tz9                               1/1     Running     0             56m
flux-system                        kustomize-controller-7f8dc49978-8grxv                          1/1     Running     0             56m
flux-system                        notification-controller-64b89b8595-vg5t9                       1/1     Running     0             56m
flux-system                        source-controller-94cbbdfb-5qppf                               1/1     Running     0             56m
harbor                             harbor-core-6c8cd5744f-dl5hc                                   1/1     Running     0             15m
harbor                             harbor-exporter-6b6bf964c4-znszh                               1/1     Running     0             15m
harbor                             harbor-jobservice-6f856d6569-jz7mv                             1/1     Running     2 (15m ago)   15m
harbor                             harbor-portal-6bd5bcc7c-j66ms                                  1/1     Running     0             15m
harbor                             harbor-postgres-primary-0                                      1/1     Running     0             18m
harbor                             harbor-postgres-read-0                                         1/1     Running     0             18m
harbor                             harbor-postgres-read-1                                         1/1     Running     0             17m
harbor                             harbor-postgres-read-2                                         1/1     Running     0             17m
harbor                             harbor-redis-0                                                 1/1     Running     0             15m
harbor                             harbor-registry-545bfbb78c-5vcmf                               2/2     Running     0             15m
k8s-gateway                        k8s-gateway-6875b4b6f6-9szpf                                   1/1     Running     0             38m
k8s-gateway                        k8s-gateway-6875b4b6f6-lm5zw                                   1/1     Running     0             37m
k8s-gateway                        k8s-gateway-6875b4b6f6-rswjs                                   1/1     Running     0             37m
keycloak                           cnpg-keycloak-1                                                1/1     Running     0             36m
keycloak                           cnpg-keycloak-2                                                1/1     Running     0             35m
keycloak                           cnpg-keycloak-3                                                1/1     Running     0             34m
keycloak                           keycloak-0                                                     1/1     Running     0             18m
keycloak                           keycloak-1                                                     1/1     Running     0             19m
keycloak                           keycloak-2                                                     1/1     Running     0             20m
keycloak                           keycloak-add-client-scope-dl5gh                                0/1     Completed   0             19m
keycloak                           keycloak-add-realm-role-bsssd                                  0/1     Completed   0             19m
keycloak                           keycloak-operator-5fc4467d7b-6brks                             1/1     Running     0             26m
keycloak                           keycloak-realm-operator-6c975d8cf7-6wp5w                       1/1     Running     0             21m
keycloak                           sylva-9vqcv                                                    0/1     Completed   0             20m
kube-system                        coredns-c94f6bfb-mgfts                                         1/1     Running     0             58m
kube-system                        k8sd-proxy-f6vxt                                               1/1     Running     0             41m
kube-system                        k8sd-proxy-j2wbm                                               1/1     Running     0             48m
kube-system                        k8sd-proxy-r5549                                               1/1     Running     0             49m
kube-system                        k8sd-proxy-xd25c                                               1/1     Running     0             57m
kube-system                        kube-vip-ds-kn4t4                                              1/1     Running     1 (22m ago)   58m
kube-system                        kube-vip-ds-q7w4s                                              1/1     Running     0             41m
kube-system                        kube-vip-ds-zqqkt                                              1/1     Running     0             49m
kube-system                        local-path-provisioner-7f8ff8867-zrd2c                         1/1     Running     0             58m
kube-system                        rke2-ingress-nginx-controller-cw6gp                            1/1     Running     0             34m
kube-system                        rke2-ingress-nginx-controller-dqb4m                            1/1     Running     0             34m
kube-system                        rke2-ingress-nginx-controller-hvs62                            1/1     Running     0             34m
kyverno                            kyverno-admission-controller-6bdd55d7fc-c9wqf                  1/1     Running     0             33m
kyverno                            kyverno-admission-controller-6bdd55d7fc-q4thj                  1/1     Running     0             32m
kyverno                            kyverno-admission-controller-6bdd55d7fc-t7svm                  1/1     Running     0             33m
kyverno                            kyverno-background-controller-f5468c579-2rqhc                  1/1     Running     0             33m
kyverno                            kyverno-background-controller-f5468c579-gjtks                  1/1     Running     0             33m

kyverno                            kyverno-background-controller-f5468c579-kcq2k                  1/1     Running     0             33m
kyverno                            kyverno-cleanup-controller-6cc758444d-hj9tt                    1/1     Running     0             39m
kyverno                            kyverno-cleanup-controller-6cc758444d-j79f7                    1/1     Running     0             39m
kyverno                            kyverno-cleanup-controller-6cc758444d-l5tx9                    1/1     Running     0             39m
kyverno                            kyverno-reports-controller-f8bc788f9-cr6kj                     1/1     Running     0             39m
kyverno                            kyverno-reports-controller-f8bc788f9-ksvtp                     1/1     Running     0             39m
kyverno                            kyverno-reports-controller-f8bc788f9-plmx6                     1/1     Running     0             39m
longhorn-system                    csi-attacher-655c8c4bc6-5qx5v                                  1/1     Running     0             55m
longhorn-system                    csi-attacher-655c8c4bc6-ndsqk                                  1/1     Running     0             55m
longhorn-system                    csi-attacher-655c8c4bc6-rvb9z                                  1/1     Running     0             55m
longhorn-system                    csi-provisioner-6cdfbcbb57-8mcmg                               1/1     Running     0             55m
longhorn-system                    csi-provisioner-6cdfbcbb57-gwj4g                               1/1     Running     0             55m
longhorn-system                    csi-provisioner-6cdfbcbb57-mjzfb                               1/1     Running     0             55m
longhorn-system                    csi-resizer-cb98b6bd-lfs44                                     1/1     Running     0             55m
longhorn-system                    csi-resizer-cb98b6bd-mftgd                                     1/1     Running     0             55m
longhorn-system                    csi-resizer-cb98b6bd-vsqgn                                     1/1     Running     0             55m
longhorn-system                    csi-snapshotter-7999cdc944-88h6b                               1/1     Running     0             55m
longhorn-system                    csi-snapshotter-7999cdc944-xhg97                               1/1     Running     0             55m
longhorn-system                    csi-snapshotter-7999cdc944-xvglx                               1/1     Running     0             55m
longhorn-system                    engine-image-ei-555a183d-7mwnn                                 1/1     Running     0             41m
longhorn-system                    engine-image-ei-555a183d-b4nf9                                 1/1     Running     0             56m
longhorn-system                    engine-image-ei-555a183d-jqrpn                                 1/1     Running     0             49m
longhorn-system                    engine-image-ei-555a183d-nwn46                                 1/1     Running     0             48m
longhorn-system                    instance-manager-066fd39c8864204a7bfff9504231623e              1/1     Running     0             48m
longhorn-system                    instance-manager-1852c3a471e1bc3dc48f7cd3f1543b8f              1/1     Running     0             41m
longhorn-system                    instance-manager-3eba09e6173de63d22e45b9ea8af8a9f              1/1     Running     0             56m
longhorn-system                    instance-manager-d71317a30ea47498cf717b52d8d14cbb              1/1     Running     0             47m
longhorn-system                    longhorn-csi-plugin-5hsft                                      3/3     Running     0             48m
longhorn-system                    longhorn-csi-plugin-7w554                                      3/3     Running     0             41m
longhorn-system                    longhorn-csi-plugin-7w8rq                                      3/3     Running     0             55m
longhorn-system                    longhorn-csi-plugin-scx5g                                      3/3     Running     0             49m
longhorn-system                    longhorn-driver-deployer-56dbcb645d-4nrsw                      1/1     Running     0             57m
longhorn-system                    longhorn-instance-manager-cleanup-29150470-6fd8d               0/1     Completed   0             13m
longhorn-system                    longhorn-instance-manager-cleanup-29150475-g8f57               0/1     Completed   0             8m39s
longhorn-system                    longhorn-instance-manager-cleanup-29150480-vgm5z               0/1     Completed   0             3m39s
longhorn-system                    longhorn-manager-74q9l                                         2/2     Running     0             41m
longhorn-system                    longhorn-manager-gp6wg                                         2/2     Running     0             49m
longhorn-system                    longhorn-manager-hjh7x                                         2/2     Running     1 (56m ago)   57m
longhorn-system                    longhorn-manager-xkbkn                                         2/2     Running     0             48m
longhorn-system                    longhorn-ui-5d9cddd6dc-2tt7x                                   1/1     Running     3 (56m ago)   57m
longhorn-system                    longhorn-ui-5d9cddd6dc-4hpgc                                   1/1     Running     3 (56m ago)   57m
metal3-system                      baremetal-operator-controller-manager-d67ddf58c-7dkqm          1/1     Running     0             34m
metal3-system                      baremetal-operator-controller-manager-d67ddf58c-9k57c          1/1     Running     0             34m
metal3-system                      metal3-ironic-567dfc54b9-rmwd9                                 3/3     Running     0             34m
minio-monitoring                   monitoring-pool-0-0                                            2/2     Running     0             26m
minio-monitoring                   monitoring-pool-0-1                                            2/2     Running     0             26m
minio-monitoring                   monitoring-pool-0-2                                            2/2     Running     0             26m
minio-monitoring                   monitoring-pool-0-3                                            2/2     Running     0             25m
minio-operator                     minio-operator-6794d5d6f9-2n5ng                                1/1     Running     0             32m
minio-operator                     minio-operator-6794d5d6f9-v4w7j                                1/1     Running     0             32m
os-images                          ubuntu-noble-plain-ck8s-1-31-6-0                               1/1     Running     0             33m
```

Deploy the workload cluster:

```bash
$: APPLY_WC_WATCH_TIMEOUT_MIN=2000 ./apply-workload-cluster.sh environment-values/workload-clusters/ck8s-capm3-virt/

🔎 Validate input files

📜 Install a sylva-units Helm release for workload cluster ck8s-capm3-virt
no sylva-units HelmRelease found, nothing to suspend
[INFO] Using 8d7aa74bf3e7c800368ad47de891143ce1d501f3
namespace/ck8s-capm3-virt created
configmap/capm3-virt-ha-values created
configmap/capm3-virt-values created
configmap/sylva-units-values created
secret/sylva-units-secrets created
helmrelease.helm.toolkit.fluxcd.io/sylva-units created
gitrepository.source.toolkit.fluxcd.io/sylva-units created

🎯 Trigger reconciliation of units
trigger reconciliation of sylva-units HelmRelease...
  helmrelease.helm.toolkit.fluxcd.io/sylva-units annotated
 ✓ GitRepository/sylva-units - Resource is ready
 ✓ HelmChart/ck8s-capm3-virt-sylva-units - Resource is ready
 ✓ HelmRelease/sylva-units - Resource is ready
 ✓ All Done: resource HelmRelease/ck8s-capm3-virt/sylva-units is ready!
waiting for root-dependency-1 to become ready...
 ✓ GitRepository/devnull - Resource is ready
 ✓ GitRepository/sylva-core - Resource is ready
 ✓ HelmChart/ck8s-capm3-virt-root-dependency-1 - Resource is ready
 ✓ HelmRelease/root-dependency-1 - Resource is ready
 ✓ Kustomization/root-dependency-1 - Resource is ready
 ✓ All Done: resource Kustomization/ck8s-capm3-virt/root-dependency-1 is ready!

⏳ Wait for units to be ready
 ✓ GitRepository/devnull - Resource is ready
 ✓ GitRepository/sylva-capi-cluster - Resource is ready
 ✓ GitRepository/sylva-core - Resource is ready
 ✓ GitRepository/sylva-prometheus-rules - Resource is ready
 ✓ HelmChart/ck8s-capm3-virt-cluster - Resource is ready
 ✓ HelmChart/ck8s-capm3-virt-cluster-bmh - Resource is ready
 ✓ HelmChart/ck8s-capm3-virt-root-dependency-1 - Resource is ready
 ✓ HelmChart/ck8s-capm3-virt-sylva-prometheus-rules - Resource is ready
 ✓ HelmRelease/root-dependency-1 - Resource is ready
 ✓ HelmRelease/sylva-prometheus-rules - Resource is ready
 ✓ HelmRepository/unit-calico - Resource is ready
 ✓ HelmRepository/unit-calico-crd - Resource is ready
 ✓ HelmRepository/unit-cert-manager - Resource is ready
 ✓ HelmRepository/unit-ingress-nginx - Resource is ready
 ✓ HelmRepository/unit-kyverno - Resource is ready
 ✓ HelmRepository/unit-longhorn - Resource is ready
 ✓ HelmRepository/unit-longhorn-crd - Resource is ready
 ✓ HelmRepository/unit-monitoring - Resource is ready
 ✓ HelmRepository/unit-monitoring-crd - Resource is ready


 ✓ Kustomization/root-dependency-1 - Resource is ready
 ✓ HelmChart/ck8s-capm3-virt-calico - Resource is ready
 ✓ HelmChart/ck8s-capm3-virt-calico-crd - Resource is ready
 ✓ HelmChart/ck8s-capm3-virt-cert-manager - Resource is ready
 ✓ HelmChart/ck8s-capm3-virt-ingress-nginx - Resource is ready
 ✓ HelmChart/ck8s-capm3-virt-kyverno - Resource is ready
 ✓ HelmChart/ck8s-capm3-virt-longhorn - Resource is ready
 ✓ HelmChart/ck8s-capm3-virt-longhorn-crd - Resource is ready
 ✓ HelmChart/ck8s-capm3-virt-monitoring - Resource is ready
 ✓ HelmChart/ck8s-capm3-virt-monitoring-crd - Resource is ready
 ✓ HelmRelease/calico - Resource is ready
 ✓ HelmRelease/calico-crd - Resource is ready
 ✓ HelmRelease/cert-manager - Resource is ready
 ✓ HelmRelease/cluster - Resource is ready
 ✓ HelmRelease/cluster-bmh - Resource is ready
 ✓ HelmRelease/ingress-nginx - Resource is ready
 ✓ HelmRelease/kyverno - Resource is ready
 ✓ HelmRelease/longhorn - Resource is ready
 ✓ HelmRelease/longhorn-crd - Resource is ready
 ✓ HelmRelease/monitoring - Resource is ready
 ✓ HelmRelease/monitoring-crd - Resource is ready
 ✓ Kustomization/mgmt-cluster-ready - Resource is ready
 ✓ Kustomization/os-images-info - Resource is ready
 ✓ Kustomization/thanos-credentials-secret - Resource is ready
 ✓ Kustomization/cluster-bmh - Resource is ready
 ✓ Kustomization/cluster-node-deletion-timeout-fix - Resource is ready
 ✓ Kustomization/cluster - Resource is ready
 ✓ Kustomization/cluster-reachable - Resource is ready
 ✓ Kustomization/cluster-ready - Resource is ready
 ✓ Kustomization/namespace-defs - Resource is ready
 ✓ Kustomization/calico-crd - Resource is ready
 ✓ Kustomization/cluster-machines-ready - Resource is ready
 ✓ Kustomization/calico - Resource is ready
 ✓ Kustomization/calico-ready - Resource is ready
 ✓ Kustomization/cert-manager - Resource is ready
 ✓ Kustomization/cluster-import-init - Resource is ready
 ✓ Kustomization/coredns - Resource is ready
 ✓ Kustomization/ingress-nginx - Resource is ready
 ✓ Kustomization/longhorn-crd - Resource is ready
 ✓ Kustomization/longhorn-instance-manager-cleanup - Resource is ready
 ✓ Kustomization/monitoring-crd - Resource is ready
 ✓ Kustomization/sylva-ca - Resource is ready
 ✓ Kustomization/cluster-import - Resource is ready
 ✓ Kustomization/cluster-import-check - Resource is ready
 ✓ Kustomization/kyverno - Resource is ready
 ✓ Kustomization/kyverno-policy-rancher-webhook-ha - Resource is ready
 ✓ Kustomization/longhorn - Resource is ready
 ✓ Kustomization/longhorn-engine-image-cleanup - Resource is ready
 ✓ Kustomization/monitoring - Resource is ready
 ✓ Kustomization/sylva-prometheus-rules - Resource is ready
 ✓ Kustomization/cluster-node-provider-id-blacklist - Resource is ready
 ✓ Kustomization/sylva-units-status - Resource is ready
 ✓ All Done: resource Kustomization/ck8s-capm3-virt/sylva-units-status is ready!
```

Verify the workload cluster nodes:

```bash
# from one of the workload cluster nodes
# kubectl exec -n sylva-system -it libvirt-metal-workload-cp-0-0 -- virsh console vbmh

$: sudo k8s kubectl get node -A

NAME                            STATUS   ROLES                  AGE    VERSION
ck8s-capm3-virt-workload-cp-0   Ready    control-plane,worker   119m   v1.31.6
ck8s-capm3-virt-workload-cp-1   Ready    control-plane,worker   103m   v1.31.6
ck8s-capm3-virt-workload-cp-2   Ready    control-plane,worker   110m   v1.31.6
ck8s-capm3-virt-workload-md-0   Ready    worker                 110m   v1.31.6
```

Verify the workload cluster pods:

```bash
# from one of the workload cluster nodes
# kubectl exec -n sylva-system -it libvirt-metal-workload-cp-0-0 -- virsh console vbmh

$: sudo k8s kubectl get pods -A

NAMESPACE                  NAME                                                     READY   STATUS      RESTARTS       AGE
calico-system              calico-kube-controllers-744469f77-42g7r                  1/1     Running     0              119m
calico-system              calico-node-58fz8                                        1/1     Running     0              110m
calico-system              calico-node-br987                                        1/1     Running     0              110m
calico-system              calico-node-sgjtv                                        1/1     Running     0              119m
calico-system              calico-node-t2hss                                        1/1     Running     0              103m
calico-system              calico-typha-bb48cf578-btztl                             1/1     Running     0              110m
calico-system              calico-typha-bb48cf578-dwdgv                             1/1     Running     0              119m
cattle-fleet-system        fleet-agent-0                                            2/2     Running     0              98m
cattle-monitoring-system   alertmanager-rancher-monitoring-alertmanager-0           2/2     Running     0              99m
cattle-monitoring-system   alertmanager-rancher-monitoring-alertmanager-1           2/2     Running     0              99m
    3/3     Running     0              98m
cattle-monitoring-system   rancher-monitoring-grafana-58f9ddd97b-vj9wb              3/3     Running     0              99m
cattle-monitoring-system   rancher-monitoring-kube-state-metrics-7c976cb77c-w5ngf   1/1     Running     0              99m
cattle-monitoring-system   rancher-monitoring-operator-7f66845b68-lh7fk             1/1     Running     0              99m
cattle-monitoring-system   rancher-monitoring-prometheus-adapter-5d559f65c8-6jgbc   1/1     Running     0              99m
cattle-monitoring-system   rancher-monitoring-prometheus-node-exporter-8dllh        1/1     Running     0              99m
cattle-monitoring-system   rancher-monitoring-prometheus-node-exporter-dhvlc        1/1     Running     0              99m
cattle-monitoring-system   rancher-monitoring-prometheus-node-exporter-dxh64        1/1     Running     0              99m
cattle-monitoring-system   rancher-monitoring-prometheus-node-exporter-h7b9f        1/1     Running     0              99m
cattle-system              cattle-cluster-agent-699f8c757b-s6jhk                    1/1     Running     0              99m
cattle-system              cattle-cluster-agent-699f8c757b-sjljk                    1/1     Running     0              100m
cattle-system              cluster-import-init-g759k                                0/1     Completed   0              103m
cattle-system              rancher-webhook-7bb4cc9c45-vn945                         1/1     Running     0              97m
cattle-system              rancher-webhook-7bb4cc9c45-z258p                         1/1     Running     0              97m
cert-manager               cert-manager-67bf4568c6-796hd                            1/1     Running     0              103m
cert-manager               cert-manager-67bf4568c6-w9zl2                            1/1     Running     0              103m
cert-manager               cert-manager-cainjector-689d8fd7f7-49fms                 1/1     Running     0              103m
cert-manager               cert-manager-cainjector-689d8fd7f7-pmqcc                 1/1     Running     0              103m
cert-manager               cert-manager-webhook-5f5cc99d7f-6wc9v                    1/1     Running     0              103m
cert-manager               cert-manager-webhook-5f5cc99d7f-c6m62                    1/1     Running     0              103m
cert-manager               cert-manager-webhook-5f5cc99d7f-t2brw                    1/1     Running     0              103m
kube-system                coredns-c94f6bfb-dwjzf                                   1/1     Running     0              120m
kube-system                k8sd-proxy-67vwh                                         1/1     Running     0              110m
    1/1     Running     0              110m
kube-system                k8sd-proxy-m2848                                         1/1     Running     0              118m
kube-system                k8sd-proxy-m68s7                                         1/1     Running     0              103m
kube-system                kube-vip-ds-525rb                                        1/1     Running     0              110m
kube-system                kube-vip-ds-b756j                                        1/1     Running     0              103m
kube-system                kube-vip-ds-qw4t5                                        1/1     Running     0              120m
kube-system                rke2-ingress-nginx-controller-dv8gg                      1/1     Running     0              102m
kube-system                rke2-ingress-nginx-controller-xd5p2                      1/1     Running     0              102m
kube-system                rke2-ingress-nginx-controller-xddpf                      1/1     Running     0              102m
kyverno                    kyverno-admission-controller-868cdcc9fd-5brg9            1/1     Running     0              102m
kyverno                    kyverno-admission-controller-868cdcc9fd-5tnrw            1/1     Running     0              102m
kyverno                    kyverno-admission-controller-868cdcc9fd-whw49            1/1     Running     0              102m
kyverno                    kyverno-background-controller-59fddcc8d-8mp4d            1/1     Running     0              102m
kyverno                    kyverno-background-controller-59fddcc8d-9ww9f            1/1     Running     0              102m
kyverno                    kyverno-background-controller-59fddcc8d-tgrcg            1/1     Running     0              102m
kyverno                    kyverno-cleanup-controller-6cc758444d-cjc6m              1/1     Running     0              102m
kyverno                    kyverno-cleanup-controller-6cc758444d-dvl5m              1/1     Running     0              102m
kyverno                    kyverno-cleanup-controller-6cc758444d-lgh85              1/1     Running     0              102m
kyverno                    kyverno-reports-controller-f8bc788f9-68xln               1/1     Running     0              102m
kyverno                    kyverno-reports-controller-f8bc788f9-rkd5f               1/1     Running     0              102m
kyverno                    kyverno-reports-controller-f8bc788f9-zjr7h               1/1     Running     0              102m
longhorn-system            csi-attacher-655c8c4bc6-gvncq                            1/1     Running     0              100m
longhorn-system            csi-attacher-655c8c4bc6-hmcv2                            1/1     Running     0              100m
longhorn-system            csi-attacher-655c8c4bc6-pzfsv                            1/1     Running     0              100m
longhorn-system            csi-provisioner-6cdfbcbb57-2z2k9                         1/1     Running     0              100m
longhorn-system            csi-provisioner-6cdfbcbb57-cbz9n                         1/1     Running     0              100m
longhorn-system            csi-provisioner-6cdfbcbb57-hcglt                         1/1     Running     0              100m
longhorn-system            csi-resizer-cb98b6bd-hz4r9                               1/1     Running     0              100m
longhorn-system            csi-resizer-cb98b6bd-v9xh7                               1/1     Running     0              100m
longhorn-system            csi-resizer-cb98b6bd-w4rsf                               1/1     Running     0              100m
longhorn-system            csi-snapshotter-7999cdc944-cf524                         1/1     Running     0              100m
longhorn-system            csi-snapshotter-7999cdc944-dsbmw                         1/1     Running     0              100m
longhorn-system            csi-snapshotter-7999cdc944-px8s9                         1/1     Running     0              100m
longhorn-system            engine-image-ei-555a183d-hhvz6                           1/1     Running     0              101m
longhorn-system            engine-image-ei-555a183d-kg9g8                           1/1     Running     0              101m
longhorn-system            engine-image-ei-555a183d-pzw6b                           1/1     Running     0              101m
longhorn-system            engine-image-ei-555a183d-tsq7x                           1/1     Running     0              101m
longhorn-system            instance-manager-660bb69a488e3468a3524b626c1f35a8        1/1     Running     0              101m
longhorn-system            instance-manager-67535772c4edb0504f1494c57945b93c        1/1     Running     0              101m
longhorn-system            instance-manager-b3eca32334cafd09c7174dc5de97601c        1/1     Running     0              101m
longhorn-system            instance-manager-da358a79379e2e063074336717eb2495        1/1     Running     0              101m
longhorn-system            longhorn-csi-plugin-2v6mc                                3/3     Running     0              100m
longhorn-system            longhorn-csi-plugin-c4zjb                                3/3     Running     0              100m
longhorn-system            longhorn-csi-plugin-tdvw2                                3/3     Running     0              100m
longhorn-system            longhorn-csi-plugin-tqlnf                                3/3     Running     0              100m
longhorn-system            longhorn-driver-deployer-56dbcb645d-5htx6                1/1     Running     1 (101m ago)   102m
longhorn-system            longhorn-instance-manager-cleanup-29150605-8tmz4         0/1     Completed   0              14m
longhorn-system            longhorn-instance-manager-cleanup-29150610-kghx2         0/1     Completed   0              9m27s
longhorn-system            longhorn-instance-manager-cleanup-29150615-frxhh         0/1     Completed   0              4m27s
longhorn-system            longhorn-manager-2vbsd                                   2/2     Running     0              102m
longhorn-system            longhorn-manager-bd6kt                                   2/2     Running     1 (101m ago)   102m
longhorn-system            longhorn-manager-c9gl4                                   2/2     Running     0              102m
longhorn-system            longhorn-manager-v9tgx                                   2/2     Running     0              102m
longhorn-system            longhorn-ui-5d9cddd6dc-mgwjh                             1/1     Running     0              102m
longhorn-system            longhorn-ui-5d9cddd6dc-rjqn7                             1/1     Running     0              102m
tigera-operator            tigera-operator-5cf6cc58b5-dkj4b                         1/1     Running     0              118m
```
