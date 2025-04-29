{{- define "cluster-unit-timeout" -}}
{{- $infra := .Values.cluster.capi_providers.infra_provider -}}
{{- $controlPlaneReplicas := .Values.cluster.control_plane_replicas | int -}}
{{- $isUpgrade := .Values._internal.state.is_upgrade | default false -}}

{{- /* Initialize the maximum number of replicas in the machine deployments */ -}}
{{- $maxMachineReplicas := 0 -}}

{{- range $md_name, $deployment := .Values.cluster.machine_deployments -}}
  {{- $maxMachineReplicas = max $maxMachineReplicas ($deployment.replicas | int) -}}
{{- end -}}

{{- $baseTimeout := mul (max $controlPlaneReplicas $maxMachineReplicas) (ternary 30 15 (eq $infra "capm3")) -}}

{{- $unitTimeout := ternary (mul $baseTimeout 3) $baseTimeout (and $isUpgrade (eq $infra "capm3")) -}}

{{- $unitTimeout -}}
{{- end -}}
