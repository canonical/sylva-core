{{/*

cluster-healthchecks

This named template generates the content of healthChecks field for a Flux CD Kustomization, with
reference to CAPI resources for the current CAPI cluster defined in the 'cluster' unit, with the
'sylva-capi-cluster' chart.

The background is that:
* the HelmRelease resource instantiating sylva-capi-cluster has no health check (FluxCD HelmReleases don't have that)
* we hence want to do the checks in the Kustomization that creates that HelmRelease
* the list of resource cannot be static, because it depends on:
  - which control plane provider is used
  - which infra provider is used
  - what are the machine deployments defined

Depending on the context, this template can be used to generate the references to the MachineDeployments or not.

This is because in the kubeadm case we can't wait for the MachineDeployemts in "cluster" unit, or this prevents
deploying the CNI, and the CNI itself is needed before the MachineDeployment nodes can be considered ready by CAPI.

*/}}

{{ define "cluster-healthchecks" }}

{{- $ns := .ns -}}  {{/* this corresponds to .Release.Namespace */}}
{{- $cluster := .cluster -}}  {{/* this corresponds to .Values.cluster */}}
{{- $includeMDs := . | dig "includeMDs" true -}}

{{/* the healtchecks is a list, we wrap it into a dict to overcome the
     fact that fromYaml can't return anything else than a dict
*/}}
{{ $result := list }}

{{/*

Wait for Cluster resource:

*/}}
{{- $result = append $result (dict
    "apiVersion" (include "getApiVersion" "Cluster")
    "kind" "Cluster"
    "name" $cluster.name
    "namespace" $ns
) -}}

{{/*

In CAPV the vsphere-cpi is responsible of executing the control plane nodes rollout so
Cluster is removed from the healthChecks in order for the vsphere-cpi to depend on the cluster unit

*/}}
{{- if $cluster.capi_providers.infra_provider | eq "capv" -}}
  {{- $result = initial $result -}}
{{- end }}

{{/*

Wait for infra provider Cluster

*/}}

{{- $cluster_kind := "" -}}
{{- $cluster_apiVersion := "" -}}
{{- if $cluster.capi_providers.infra_provider | eq "capo" -}}
  {{- $cluster_kind = "OpenStackCluster" -}}
{{- else if $cluster.capi_providers.infra_provider | eq "capv" -}}
  {{- $cluster_kind = "VSphereCluster" -}}
{{- else if $cluster.capi_providers.infra_provider | eq "capm3" -}}
  {{- $cluster_kind = "Metal3Cluster" -}}
{{- else if $cluster.capi_providers.infra_provider | eq "capd" -}}
  {{- $cluster_kind = "DockerCluster" -}}
{{- else -}}
  {{- fail (printf "sylva-units cluster-healthchecks named template would need to be extended to support CAPI infra provider %s" $cluster.capi_providers.infra_provider) -}}
{{- end }}
{{- $cluster_apiVersion = include "getApiVersion" $cluster_kind -}}
{{- $result = append $result (dict
    "apiVersion" $cluster_apiVersion
    "kind" $cluster_kind
    "name" $cluster.name
    "namespace" $ns
) -}}

{{/* Workaround for https://gitlab.com/sylva-projects/sylva-core/-/issues/959; we drop the last element (Metal3Cluster) */}}
{{- if $cluster.capi_providers.infra_provider | eq "capm3" -}}
  {{- $result = initial $result -}}
{{- end }}
{{/*

We determine which control plane object to look at depending
on the CAPI bootstrap provider being used.

*/}}

{{- $cp_kind := "" -}}
{{- $cp_apiVersion := "" -}}
{{- if $cluster.capi_providers.bootstrap_provider | eq "cabpk" -}}
  {{- $cp_kind = "KubeadmControlPlane" -}}
{{- else if $cluster.capi_providers.bootstrap_provider | eq "cabpr" -}}
  {{- $cp_kind = "RKE2ControlPlane" -}}
{{- else if $cluster.capi_providers.bootstrap_provider | eq "cabpoa" -}}
  {{/* "OpenshiftAssistedControlPlane" for OKD CAPI provider */}}
  {{- $cp_kind = "OpenshiftAssistedControlPlane" -}}
{{- else if $cluster.capi_providers.bootstrap_provider | eq "cabpck" -}}
  {{- $cp_kind = "CK8sControlPlane" -}}
{{- else -}}
  {{- fail (printf "sylva-units cluster-healthchecks named template would need to be extended to support CAPI bootstrap provider %s" $cluster.capi_providers.bootstrap_provider) -}}
{{- end }}
{{- $cp_apiVersion = include "getApiVersion" $cp_kind -}}
{{ $result = append $result (dict
    "apiVersion" $cp_apiVersion
    "kind" $cp_kind
    "name" (printf "%s-control-plane" $cluster.name)
    "namespace" $ns
) -}}

{{/*

In CAPV the vsphere-cpi is responsible of executing the control plane nodes rollout so
the CR representing the Control Plane is removed from the healthChecks in order for the vsphere-cpi to depend on the cluster unit

*/}}
{{- if $cluster.capi_providers.infra_provider | eq "capv" -}}
  {{- $result = initial $result -}}
{{- end }}

{{/*

If $includeMDs was specified, we include all the MachineDeployments in the healthChecks.

*/}}

{{ if $includeMDs -}}
    {{- range $md_name,$_ := $cluster.machine_deployments }}
        {{- $result = append $result (dict
    "apiVersion" (include "getApiVersion" "MachineDeployment")
    "kind" "MachineDeployment"
    "name" (printf "%s-%s" $cluster.name $md_name)
    "namespace" $ns
        ) -}}
    {{ end -}}
{{- end -}}

{{/*

All the above is subject to a race condition: if Flux checks the status too early
it concludes, because CAPI resources aren't fully kstatus compliant, that the resource is ready

Waiting for the cluster kubeconfig Secret is a workaround

*/}}

{{/*

In the case of Canonical Bootstrap Provider (cabpck), we wait only for the kubeconfig,
as the CK8sControlPlane becomes ready only and only after the calico unit gets installed.

In the case of RKE2, Calico is installed by the cloud-init userdata.
In the case of Kubeadm, the KuebadmControlPlane becomes ready in an optimistic fashion. See: https://github.com/kubernetes-sigs/cluster-api/issues/11766

*/}}

{{- $onlyCheckKubeConfig := . | dig "onlyCheckKubeConfig" false -}}
{{- if $onlyCheckKubeConfig -}}
  {{- $result = list -}}
{{- end }}

{{- $result = append $result (dict
    "apiVersion" "v1"
    "kind" "Secret"
    "name" (printf "%s-kubeconfig" $cluster.name)
    "namespace" $ns
) -}}
{{ dict "result" $result | toYaml }}
{{ end -}}
