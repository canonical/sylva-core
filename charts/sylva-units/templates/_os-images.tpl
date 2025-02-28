{{- define "images_from_diskimagebuilder" }}
{{/* returns a dict of images following sylva_diskimagebuilder_images and os_images values */}}
{{- $images := dict }}
{{- $sylva_dib_images := index (tuple . .Values.sylva_diskimagebuilder_images | include "interpret-inner-gotpl" | fromJson) "result" }}
{{- $sylva_dib_version := tuple . .Values.sylva_diskimagebuilder_version | include "interpret-as-string" }}
{{- $os_images_oci_registries := index (tuple . .Values.os_images_oci_registries | include "interpret-inner-gotpl" | fromJson) "result" }}
{{- $os_images := index (tuple . .Values.os_images | include "interpret-inner-gotpl" | fromJson) "result"}}
  {{- range $os_image_name, $os_image_props := $sylva_dib_images }}
  {{- $os_image_props := mergeOverwrite (dict "os_images_oci_registry" "sylva") $os_image_props }}
  {{- $oci_registry_url := dig $os_image_props.os_images_oci_registry "url" "" $os_images_oci_registries }}
  {{- $oci_registry_tag := dig $os_image_props.os_images_oci_registry "tag" "" $os_images_oci_registries }}
  {{- $oci_registry_cosign_publickey := dig $os_image_props.os_images_oci_registry "cosign_publickey" "" $os_images_oci_registries }}

  {{- $use_image := false -}}

  {{/* else, we'll use it if .enabled is set or, if os_images isn't set if .default_enabled is set */}}
  {{- $use_image = or ($os_image_props.enabled) (and $os_image_props.default_enabled (not $os_images)) -}}

  {{- if $use_image -}}
    {{- $props := dict "uri"              (printf "%s/%s:%s" $oci_registry_url $os_image_name $oci_registry_tag)
                       "sylva_dib_image"  true
                       "cosign_publickey" $oci_registry_cosign_publickey
                       -}}
    {{- $_ := set $images $os_image_name $props }}
  {{- end -}}
{{- end }}
{{- $images | toJson }}
{{- end }}

{{- define "generate-os-images" -}}
os_images:
  {{- if .Values.os_images }}
{{ .Values.os_images | toYaml | indent 2}}
  {{- end }}
{{- $images_from_diskimagebuilder := include "images_from_diskimagebuilder" . | fromJson }}
  {{- if $images_from_diskimagebuilder }}
{{ $images_from_diskimagebuilder | toYaml | indent 2}}
  {{- end }}
  {{- if and (not .Values.os_images) (not $images_from_diskimagebuilder) }}
{{ dict | toYaml }}
  {{- end }}
{{- end }}
