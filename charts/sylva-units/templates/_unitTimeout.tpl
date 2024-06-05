{{- define "cluster-unit-timeout" -}}
{{- $infra := .Values.cluster.capi_providers.infra_provider -}}
{{- $controlPlaneReplicas := .Values.cluster.control_plane_replicas | int -}}

{{- /* Initialize the maximum number of replicas in the machine deployments */ -}}
{{- $maxMachineReplicas := 0 -}}

{{- range $md_name, $deployment := .Values.cluster.machine_deployments -}}
  {{- $maxMachineReplicas = max $maxMachineReplicas ($deployment.replicas | int) -}}
{{- end -}}

{{- $unitTimeout := mul (max $controlPlaneReplicas $maxMachineReplicas) (ternary 30 15 (eq $infra "capm3")) -}}

{{- $unitTimeout -}}
{{- end -}}
