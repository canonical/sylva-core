{{/*
Ensure that no_proxy covers everything that we need by adding the values defined in no_proxy_base.
(Default values will be add only if the user set at least one of no_proxy or no_proxy_additional field)
*/}}
{{- define "sylva-units.no_proxy" -}}
  {{- $envAll := index . 0 -}}

  {{- if (or  ($envAll.Values.proxies.http_proxy) ($envAll.Values.proxies.https_proxy)) -}}
    {{/* this function accepts an optional second parameter to override entries from no_proxy_additional) */}}
    {{- $overrides := dict -}}
    {{- if gt (len .) 1 -}}
        {{- $overrides = index . 1 -}}
    {{- end -}}

    {{/* we start building the list of no_proxy items, accumulating them in $no_proxy_list... */}}
    {{- $no_proxy_list := concat $envAll.Values.cluster.cluster_pods_cidrs $envAll.Values.cluster.cluster_services_cidrs -}}
    {{- if $envAll.Values.cluster.capm3 -}}
      {{- range $envAll.Values.cluster.capm3.networks -}}
        {{- $no_proxy_list = append $no_proxy_list .subnet -}}
      {{- end -}}
      {{- range $envAll.Values.cluster.baremetal_hosts -}}
        {{- $bmc_mgmt := urlParse (tuple $envAll .bmh_spec.bmc.address | include "interpret-as-string") -}}
        {{- $no_proxy_list = append $no_proxy_list ($bmc_mgmt.host | splitList ":" | first) -}}
      {{- end -}}
    {{- end -}}

    {{- $no_proxy_list = concat $no_proxy_list (splitList "," $envAll.Values.proxies.no_proxy) -}}

    {{/* we merge 'no_proxy_additional_rendered' with 'overrides'
         note well that we do this after *interpreting* any go templating
    */}}
    {{- $no_proxy_additional_rendered := dict -}}
    {{- range $no_proxy_item,$val := $envAll.Values.no_proxy_additional -}}
      {{- $_ := set $no_proxy_additional_rendered (tuple $envAll $no_proxy_item | include "interpret-as-string") $val -}}
    {{- end -}}
    {{- range $no_proxy_item,$val := $overrides -}}
      {{- $_ := set $no_proxy_additional_rendered (tuple $envAll $no_proxy_item | include "interpret-as-string") $val -}}
    {{- end -}}

    {{/* we add to the list the no_proxy items that are enabled
         and remove the disabled ones
    */}}
    {{- range $no_proxy_item, $val := $no_proxy_additional_rendered -}}
      {{- if $val -}}
        {{- $no_proxy_list = append $no_proxy_list $no_proxy_item -}}
      {{- else -}}
        {{- $no_proxy_list = without $no_proxy_list $no_proxy_item -}}
      {{- end -}}
    {{- end -}}

    {{/* render final list */}}
    {{- without $no_proxy_list "" | uniq | join "," -}}
  {{- end -}}
{{- end -}}

{{/*
Return an error if the upgrade values (positional arg $tentative_values)
of any of the ones marked as immutable (positional arg $immutable_values)
are not equal to previous revision (positional arg $old_values) set
*/}}
{{- define "check-immutable-values" -}}
{{- $immutable_values := index . 0 -}}
{{- $old_values := index . 1 -}}
{{- $tentative_values := index . 2 -}}
{{- $path := index . 3 | default list -}}
{{- if not (kindIs "map" $immutable_values) -}}
  {{- fail (printf "check-immutable-values: type of input parameter for immutable values at '._internal.immutable_values.%s', but %s" (join "." $path) (kindOf $immutable_values)) -}}
{{- end -}}
{{- range $key, $value := $immutable_values -}}
  {{- $path := append $path $key -}}
  {{- if kindIs "map" $value -}}
    {{- if hasKey $value "_immutable" -}}
      {{- if not (kindIs "bool" (index $value "_immutable")) -}}
        {{- fail (printf "wrong type for '._internal.immutable_values.%s': %v" (join "." $path) (index $value "_immutable")) -}}
      {{- end -}}
      {{- if (eq (index $value "_immutable") true) -}}
        {{- if not (deepEqual (dig $key "_dig_default_unused" $old_values) (dig $key "_dig_default_unused" $tentative_values)) -}}
          {{- fail (printf "Attempting to change value for '.%s', which is immutable (from '%s' to '%s'). \n %s"
                                                (join "." $path)
                                                (dig $key "<unset>" $old_values | toJson)
                                                (dig $key "<unset>" $tentative_values | toJson)
                                                (index $value "_immutable_comment" | default "Unsupported.")
                    ) -}}
        {{- end -}}
      {{- end -}}
    {{- end -}}
    {{/* if there are additional keys in $value on top of `_immutable` & `_immutable_comment` we recursively check them
         by passing the $value without `_immutable` & `_immutable_comment` keys as the new set of $immutable_values */}}
    {{- if (gt ((without (keys $value) "_immutable" "_immutable_comment") | len) 0) -}}
      {{- $_ := unset $value "_immutable" -}}
      {{- $_ := unset $value "_immutable_comment" -}}
      {{- tuple $value (dig $key dict $old_values) (dig $key dict $tentative_values) $path | include "check-immutable-values" -}}
    {{- end -}}
  {{- else -}}
    {{- fail (printf "Input '._internal.immutable_values.%s' type is not a map, but %s" (join "." $path) (kindOf $value)) -}}
  {{- end -}}
{{- end -}}
{{- end -}}

{{- define "get-helm-version" -}}
  {{- $envAll := index . 0 -}}
  {{- $unit_name := index . 1 -}}
  {{- $unit_def := index . 2 -}}
  {{- $helm_chart_versions_selection := "" -}}
  {{- range $ver, $enabled := (index (tuple $envAll $unit_def | include "interpret-inner-gotpl" | fromJson) "result" | dig "helm_chart_versions" "")  -}}
    {{- if $enabled -}}
      {{- if $helm_chart_versions_selection -}}
        {{- fail (printf "unit '%s' has 'true' set on more than one version inside 'helm_chart_versions':\n%s" $unit_name ($unit_def.helm_chart_versions | toYaml)) -}}
      {{- else -}}
        {{- $helm_chart_versions_selection = $ver -}}
      {{- end -}}
    {{- end -}}
  {{- end -}}
  {{ $helm_chart_versions_selection }}
{{- end -}}
