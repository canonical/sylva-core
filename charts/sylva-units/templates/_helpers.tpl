{{/*
Expand the name of the chart.
*/}}
{{- define "sylva-units.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "sylva-units.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "sylva-units.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}


{{/*
Selector labels
*/}}
{{- define "sylva-units.selectorLabels" -}}
app.kubernetes.io/name: {{ include "sylva-units.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "sylva-units.labels" -}}
helm.sh/chart: {{ include "sylva-units.chart" . }}
{{ include "sylva-units.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}


{{/*

This is used by units.yaml to patch the HelmRelease
resource produced when the kustomization from kustomize-units/helmrelease-generic
which is used to create a Flux Kustomization that generates a HelmRelease.

*/}}
{{ define "helmrelease-kustomization-patch-template" }}
  {{- $unit_name := index . 0 -}}
  {{- $helmrelease_spec := index . 1 -}}
  {{- $annotations := index . 2 -}}
  {{- $labels := index . 3 -}}
  {{- $has_secret := index . 4 -}}
  {{- $secretHash := index . 5 -}}
patches:
  - target:
      kind: HelmRelease
    patch: |
      - op: replace
        path: /metadata
        value:
          namespace: sylva-system
          name: {{ $unit_name }}
          annotations: {{ $annotations | toYaml | nindent 12 }}
          labels: {{ $labels | toYaml | nindent 12 }}
      - op: replace
        path: /spec
        value: {{ mergeOverwrite (dict "valuesFrom" list) $helmrelease_spec | toYaml | nindent 10 | include "unshield-raw" }}
  {{ if $has_secret }}
  - target:
      kind: Secret
    patch: |
      - op: replace
        path: /metadata
        value:
          namespace: sylva-system
          name: helm-unit-values-{{ $unit_name }}-{{ $secretHash }}
          labels: {{ $labels | toYaml | nindent 12 }}
  - target:
      kind: HelmRelease
    patch: |
      - op: add
        path: /spec/valuesFrom/0
        value:
          kind: Secret
          name: helm-unit-values-{{ $unit_name }}-{{ $secretHash }}
          valuesKey: values
  {{ else }}
  - target:
      kind: Secret
    patch: |
      kind: Secret
      metadata:
        name: _unused_
      $patch: delete
  {{ end }}
{{ end }}

{{/*

unit-labels

Returns a JSON dict with the labels of a unit.

Parameters:
- $envAll
- unit definition dictionary

Usage:

  {{ include "unit-labels" $unit_def }}

*/}}
{{- define "unit-labels" -}}
  {{- $envAll := index . 0 -}}
  {{- $unit_def := index . 1 -}}

  {{- $labels := $unit_def.labels | default dict -}}

  {{/* remove labels with 'null' values */}}
  {{- range $k,$v := $labels -}}
    {{- if $v | eq nil -}}
      {{- $_ := unset $labels $k -}}
    {{- end -}}
  {{- end -}}

  {{/* add global Helm chart labels */}}
  {{- $_ := mergeOverwrite $labels (include "sylva-units.labels" $envAll | fromYaml) -}}

  {{/* add unit name label */}}
  {{- $_ := set $labels "sylva-units.unit" $unit_def._unit_name_ -}}

  {{/* return result */}}
  {{- $labels | toJson -}}
{{- end -}}

{{/*

Test if a unit is enabled or not

Usage:

{{ if tuple $envAll "unit-name" | include "unit-enabled" }}

*/}}
{{- define "unit-enabled" -}}
  {{- $envAll := index . 0 -}}
  {{- $unit_name := index . 1 -}}

  {{/* interpret unit name to cover the case where it would be a template */}}
  {{- $unit_name = tuple $envAll $unit_name | include "interpret-as-string" -}}

  {{- $unit_def := index $envAll.Values.units $unit_name -}}

  {{- if not $unit_def -}}
    {{- fail (printf "'unit-enabled' called to test if a non-existing unit is enabled (%s)" $unit_name) -}}
  {{- end -}}

  {{- $unit_enabled := $envAll.Values.units_enabled_default -}}

  {{- if hasKey $envAll.Values "units_override_enabled" -}}
    {{- $interpreted_units_override_enabled := index (tuple $envAll $envAll.Values.units_override_enabled | include "interpret-inner-gotpl" | fromJson) "result" -}}
    {{- $unit_enabled = has $unit_name $interpreted_units_override_enabled -}}
  {{- else if hasKey $unit_def "enabled" -}}
    {{- $unit_enabled = index (tuple $envAll $unit_def.enabled (printf "unit:%s" $unit_name) | include "interpret-as-bool" | fromJson) "encapsulated-result" -}}
  {{- end -}}

  {{/* a unit which has "one_shot: true" will be disabled if we have recorded,
       via sylva-units-status ConfigMap, that it was part of an install/upgrade
       of the Helm release that proceeded until completion (reconcilication of
       sylva-units-status Kustomization which depends on all Kustomizations
       having reconciled, and which updates the sylva-units-status ConfigMap)
  */}}
  {{- if and ($unit_def.one_shot | default false) (include "one-shot-unit-is-done" (tuple $envAll $unit_name)) -}}
    {{- $unit_enabled = false -}}
  {{- end -}}

  {{- range $condition := $unit_def.enabled_conditions | default list -}}
    {{- $unit_enabled = and $unit_enabled (index (tuple $envAll $condition (printf "unit:%s" $unit_name) | include "interpret-as-bool" | fromJson) "encapsulated-result") -}}
    {{- if not $unit_enabled -}}
      {{- break -}}
    {{- end -}}
  {{- end -}}

  {{- if $unit_enabled -}}
true
  {{- else -}} {{- /* we "emulate" a 'false' value by returning an empty string which the caller will evaluate as False */ -}}
  {{- end -}}
{{- end -}}


{{/*

"one-shot-unit-is-done"

Test, applicable to a unit with "one_shot: true", which indicates if this unit
was already applied, ie. reconciled successfully in an application (install or upgrade)
of sylva-units Helm release that ran to completion until the reconciliation
of sylva-units-status Kustomization.

This is determined based on the content of the "one-shot-units"
key of the sylva-units-status ConfigMap.

Usage:

  include "one-shot-unit-is-done" "my-unit"

Returned value: "true" or "" (false)

*/}}
{{- define "one-shot-unit-is-done" -}}
  {{- $envAll := index . 0 -}}
  {{- $unit_name := index . 1 -}}
  {{- if include "one-shot-units" $envAll | fromJson | dig $unit_name "" | eq "done" -}}
true
  {{- else -}}{{- end -}}{{/* empty return value to mean false */}}
{{- end -}}

{{/*

"one-shot-units"

Returns a JSON-encoded dict with all the one-shot units tracked in
the "one-shot-units" entry of sylva-units-status ConfigMap.

(see in sylva-units-values.yaml how the "one-shot-units" entry of
sylva-units-status ConfigMap is maintained)

*/}}
{{- define "one-shot-units" -}}
  {{- $envAll := index . -}}
  {{/* this function does a 'lookup', but for unit test the 'lookup' call is replaced by a mock */}}
  {{- if hasKey .Values._internal "_test_mockup_sylva_units_status_ConfigMap"  -}}
    {{- .Values._internal | dig   "_test_mockup_sylva_units_status_ConfigMap" "data" "one-shot-units" "{}" | fromYaml | toJson -}}
  {{- else -}}
    {{- lookup "v1" "ConfigMap" $envAll.Release.Namespace "sylva-units-status" | dig "data" "one-shot-units" "{}" | fromYaml | toJson -}}
  {{- end -}}
{{- end -}}


{{/*

"unit-def"

This named template takes a unit name and
provides the full definition of the unit *taking into account:
- what comes from unit_definition_defaults
- what is inherited from unit_templates* via the declarations of *unit.xxx.unit_templates*

Usage:

  {{ $unit_def := include "unit-def" (tuple $envAll "my-unit") | fromJson }}

See usage in units.yaml and sources.yaml

*/}}
{{ define "unit-def" }}
  {{- $envAll := index . 0 -}}
  {{- $unit_name := index . 1 -}}

  {{- if not (hasKey $envAll.Values.units $unit_name) -}}
    {{- fail (printf "unit-def called on non-existing unit: %s" $unit_name) -}}
  {{- end -}}
  {{- $unit_def := deepCopy $envAll.Values.unit_definition_defaults -}}
  {{- $_ := tuple $unit_def (index $envAll.Values.units $unit_name) | include "merge-append" -}}

  {{/* inherit settings from any template specified in unit.<this unit>.unit_templates and unit_definition_defaults.unit_templates*/}}
  {{- $merged_unit_templates := dict -}}
  {{ range $template_name := $unit_def.unit_templates | default list -}}
    {{- if not (hasKey $envAll.Values.unit_templates $template_name) -}}
      {{ fail (printf "unit %s has '%s' in '<unit>.unit_templates' but no such template is declared in '.Values.unit_templates'" $unit_name $template_name) -}}
    {{- end -}}
    {{/* merge the unit template with the others*/}}
    {{- $_ = tuple $merged_unit_templates (index $envAll.Values.unit_templates $template_name) | include "merge-append" -}}
  {{- end -}}

  {{/* merge unit definition with unit templates
       we merge from defaults again in order to have lists merged in "intuitive" order that is:
        - values from unit_definition_defaults
        - values from unit_templates
        - values from unit definitions
  */}}
  {{ $unit_def := deepCopy $envAll.Values.unit_definition_defaults -}}
  {{- $_ = tuple $unit_def $merged_unit_templates (index $envAll.Values.units $unit_name) | include "merge-append" -}}

  {{/* interpret _unit_name_ in unit template */}}
  {{- $_ := set $envAll.Values "_unit_name_" $unit_name -}}
  {{- $_ := set $envAll.Values "_kustomization_name_" (include "kustomization-name" (tuple $envAll $unit_name $unit_def)) -}}
  {{- $unit_def := index (tuple $envAll $unit_def | include "interpret-inner-gotpl" | fromJson) "result" -}}

  {{/* clear _unit_name_ from Values, we don't need it anymore */}}
  {{- $_ := set $envAll.Values "_unit_name_" "N/A" -}}

  {{/* include the unit name in the unit_def result */}}
  {{- $_ := set $unit_def "_unit_name_" $unit_name }}

  {{/* return the result */}}
  {{- $unit_def | toJson -}}
{{ end }}


{{/*

all-unit-dependencies

this named template compute all the direct and indirect dependencies of a given unit

it fails if any circular dependency is found

usage:

  $deps := index (include "all-unit-dependencies" (tuple . "cluster" (list "cluster-machines-ready") dict)
                                                   | fromJson) "result"

(it has two additionnal parameters:
  $ignore_units, which is used to optimize recursive calls or exclude a unit from being considered during computation
  $all_dependencies_cache, which is used to optimize recursive calls, especially for circular dependency checks)

*/}}

{{- define "all-unit-dependencies" -}}
{{- $envAll := index . 0 -}}
{{- $unit_name := index . 1 -}}
{{- $ignore_units := index . 2 -}}{{/* list */}}
{{- $all_dependencies_cache := index . 3 -}}{{/* dict */}}
{{- include "_all-unit-dependencies" (tuple $envAll $unit_name $ignore_units $all_dependencies_cache list) }}
{{- end }}

{{/*

internal implementation of all-unit-dependencies that keeps a trace of the dependencies in
dependents_list and fails if a circular dependency is detected

*/}}

{{- define "_all-unit-dependencies" -}}
{{- $envAll := index . 0 -}}
{{- $unit_name := index . 1 -}}
{{- $ignore_units := index . 2 -}}{{/* list */}}
{{- $all_dependencies_cache := index . 3 -}}{{/* dict */}}
{{- $dependents_list := index . 4 -}}{{/* list of dependents used to print circular dependencies */}}

{{- if not $unit_name -}}
  {{- fail "unit name nil/empty" -}}
{{- end -}}

{{- $result := list -}}

{{- $debug := printf "(start %s " $unit_name }}

{{- if has $unit_name $dependents_list -}}
  {{- $dependents_list = append $dependents_list $unit_name -}}
  {{- fail (printf "unit %s is involved in a circular dependency:\n%s" $unit_name (join " -> " $dependents_list)) }}
{{- end }}
{{- $dependents_list = append $dependents_list $unit_name -}}

{{- if hasKey $all_dependencies_cache $unit_name -}}
  {{- $result = without (index $all_dependencies_cache $unit_name) $ignore_units -}}
{{- else -}}
  {{- $unit_def := include "unit-def" (tuple $envAll $unit_name) | fromJson -}}

  {{- if hasKey $unit_def "depends_on" -}}
    {{/*
    we need to handle the case where depends_on is a template, and/or
    where keys or values are templates
    */}}
    {{- $depends_on := index (tuple $envAll $unit_def.depends_on | include "interpret-inner-gotpl" | fromJson) "result" -}}

    {{- $debug = printf "%s alldepends_ons:%s" $debug ($unit_def.depends_on|keys|join ",") -}}

    {{- range $dep_name, $is_dependency := $depends_on -}}
      {{- $debug = printf "%s dep:%s" $debug $dep_name -}}

      {{- if $ignore_units | has $dep_name -}}
        {{- $debug = printf "%s:ignored-unit" $debug -}}
        {{- continue }}
      {{- end -}}

      {{/* only take a dependency into account if it is active (depend_on[x] == true) */}}
      {{- if not (tuple $envAll $is_dependency | include "interpret-for-test") -}}
        {{- $debug = printf "%s:inactive-dep" $debug -}}
        {{- continue }}
      {{- end -}}

      {{- $result = append $result $dep_name -}}

      {{/* examine the dependency, recursing if needed */}}
      {{- $recurse := include "_all-unit-dependencies" (tuple $envAll $dep_name $ignore_units $all_dependencies_cache $dependents_list) | fromJson -}}
      {{- $debug = printf "%s:r:%s" $debug $recurse.debug -}}

      {{/* incorporate recursion result in result */}}
      {{- $result = concat $result $recurse.result -}}
    {{- end -}}
  {{- end -}}
  {{/* save result in cache */}}
  {{- $_ := set $all_dependencies_cache $unit_name $result -}}
{{- end -}}

{{- $debug := printf "%s)" $debug -}}

{{/* return the result */}}
{{- dict "result" $result
         "debug" $debug
    | toJson -}}
{{- end -}}


{{/*

internalPersistentRandomPasswd

This named template produces a random password that does not change when the sylva-units Helm release
is updated. This is ensured by storing the password in the "sylva-units-values" Secret and looking
up in this Secret if the password was already generated, before generating a fresh random one.

usage (in values):

  _internal:
     my_password: '{{ include "persistentRandomPasswd" "my_password" }}

NOTE WELL:
* this can be done only under '_internal'
* the named template parameter MUST MATCH the key used under _internal

*/}}
{{- define "internalPersistentRandomPasswd" -}}
{{- $envAll := index . 0 -}}
{{- $key := index . 1 -}}
{{- lookup "v1" "Secret" $envAll.Release.Namespace "sylva-units-values" | dig "data" "values" "" | b64dec | fromYaml | dig "_internal" $key (randAlphaNum 64) -}}
{{- end -}}



{{/*

kustomization-name

This named templates return the name of the Kustomization to use for a given unit.

The name is 'kustomization_name' if this attribute is defined in the unit definition
(either in unit.$unit_name.kustomization_name or inherited via unit_templates), or,
by default the unit name.

Usage:

  {{- $unit_name := include "kustomization-name" (tuple $envAll "unit-foo") }}

Or, as an optimization *if* *full* $unit_def, as computed by "unit-def",
is already known by caller:

  {{- $unit_name := include "kustomization-name" (tuple $envAll "unit-foo" $unit_def) }}

*/}}
{{- define "kustomization-name" -}}
{{- $envAll := index . 0 -}}
{{- $unit_name := index . 1 -}}

{{- $unit_def := dict -}}
{{- if gt (len .) 2 -}}
  {{- $unit_def = index . 2 -}}
{{- else -}}
  {{- $unit_def = include "unit-def" (tuple $envAll $unit_name) | fromJson -}}
{{- end -}}
{{/* return the result */}}
{{- $unit_def.kustomization_name | default $unit_name -}}
{{- end -}}



{{/*
merge-append template: like mergeOverwrite, but append lists instead of overwriting them.

Usage:

    tuple $dst $src | include "merge-append"

Values:

    dest:
      one: thing
      two:
       - a
       - b

    source1:
      one: stuff
      two:
       - a
       - c

    source2:
      one: other
      two:
       - d

Template:

{{- tuple .Values.dest .Values.source1 .Values.source2 | include "merge-append" }}
{{ .Values.dest | toYaml }}

Result:

    one: other
    two:
    - a
    - b
    - a
    - c
    - d

*/}}
{{- define "merge-append" }}
    {{- $dst := first . }}
    {{- range $src := rest . }}
        {{- $dst := tuple $dst $src | include "_merge-append" }}
    {{- end }}
{{- end }}

{{- define "_merge-append" }}
    {{- $dst := index . 0 }}
    {{- $src := index . 1 }}
    {{- if not (kindIs "map" $src) }}
        {{- fail (printf "'merge-append' called with a source object which is not a map (<%s> is %s)" ($src | toString) (kindOf $src)) }}
    {{- end }}
    {{- if not (kindIs "map" $dst) }}
        {{- fail (printf "'merge-append' called with a source object which is not a map (<%s> is %s)" ($dst | toString) (kindOf $dst)) }}
    {{- end }}
    {{- $result := $dst }}
    {{- range $key,$value := $src }}
        {{- if (hasKey $dst $key) }}
            {{- if (eq (kindOf $value) (kindOf (get $dst $key))) }}
                {{- if (eq (kindOf $value) "slice") }}
                    {{- /* append src list to dst one */}}
                    {{- $_ := set $result $key (concat (get $dst $key) $value) }}
                {{- else if (eq (kindOf $value) "map") }}
                    {{- /* recurse in that case */}}
                    {{- $_ := tuple (get $dst $key) $value | include "merge-append" }}
                {{- else }}
                    {{- /* we can't merge other kind of values like string or integers, overwrite dst value with src one */}}
                    {{- /* NOTE: maybe we should have a merge-append and merge-overwrite-append to choose whether we should keep value from dst or not */}}
                    {{- $_ := set $result $key $value }}
                {{- end }}
            {{- else }}
                {{- /* we can't merge two different kind of values, overwrite dst value with src one */}}
                {{- /* NOTE: maybe we should have a must-merge-append variant that would fail in that case? of fail inconditionally? */}}
                {{-  if (eq (kindOf $value) "map") }}
                  {{- /* deepCopy maps, otherwise they would be passed by reference and source could be updated by subsequent merges */}}
                  {{- $_ := set $result $key (deepCopy $value) }}
                {{- else }}
                  {{- $_ := set $result $key $value}}
                {{- end }}
            {{- end }}
        {{- else }}
            {{- /* key not in dst, merge it from src */}}
            {{-  if (eq (kindOf $value) "map") }}
              {{- /* deepCopy maps, otherwise they would be passed by reference and source could be updated by subsequent merges */}}
              {{- $_ := set $result $key (deepCopy $value) }}
            {{- else }}
              {{- $_ := set $result $key $value}}
            {{- end }}
        {{- end }}
    {{- end }}
    {{- $dst := $result }}
{{- end }}
