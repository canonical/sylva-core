{{- define "images_from_diskimagebuilder" }}
{{/* returns a dict of images based on sylva_diskimagebuilder_images values */}}
{{- $images := dict }}
{{- tuple . "sylva_diskimagebuilder_images" | include "interpret" -}}
{{- tuple . "os_images_oci_registries" | include "interpret" -}}
{{- range $os_image_name, $os_image_props := .Values.sylva_diskimagebuilder_images -}}

  {{- if not (hasKey $.Values.os_images_oci_registries $os_image_props.os_images_oci_registry) -}}
    {{- fail (printf "sylva_diskimagebuilder_images.%s.os_images_oci_registry ('%s') is not defined in os_images_oci_registries" $os_image_name $os_image_props.os_images_oci_registry) -}}
  {{- end -}}

  {{/* skip image if its registry is disabled in os_images_oci_registries entry*/}}
  {{- if not ($.Values.os_images_oci_registries | dig $os_image_props.os_images_oci_registry "enabled" true) -}}
    {{- continue -}}
  {{- end -}}

  {{- $oci_registry_url := $.Values.os_images_oci_registries | dig $os_image_props.os_images_oci_registry "url" "" -}}
  {{- $oci_registry_tag := $.Values.os_images_oci_registries | dig $os_image_props.os_images_oci_registry "tag" "" -}}
  {{- $oci_registry_cosign_publickey := $.Values.os_images_oci_registries | dig $os_image_props.os_images_oci_registry "cosign_publickey" "" -}}

  {{- $props := dict "uri"              (printf "%s/%s:%s" $oci_registry_url $os_image_name $oci_registry_tag)
                     "sylva_dib_image"  true
                     "cosign_publickey" $oci_registry_cosign_publickey
                     -}}
  {{- $_ := set $images $os_image_name $props }}
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
{{ dict | toYaml | indent 2}}
  {{- end }}
{{- end }}
