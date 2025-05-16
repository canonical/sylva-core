{{/*

interpret-values-gotpl

This template allows the interpretation of go templates inside values. It should be called at the beginning of every template file that uses templated values, using the following syntax for eample:

{{- $envAll := set . "Values" (include "interpret-values-gotpl" . | fromJson) -}}

Here is an example of its usage:

# values:

foo: bar
sample: "{{ .Values.foo }}"

# template:

{{- $_ := set . "Values" (include "interpret-values-gotpl" . | fromJson) -}}
sample-value: {{ .Values.sample }}

# result:

sample-value: bar

If your template outputs is not a string, you should pass it to the "preserve-type" template if want to prevent the result from being transformed to a string (which often produces unwanted result, as illustrated below):

# values:

sample: '{{ dict "foo" "bar" }}'
preserved: '{{ dict "foo" "bar" | include "preserve-type" }}'

# template:

{{- $_ := set . "Values" (include "interpret-values-gotpl" . | fromJson) -}}
sample-value: {{ .Values.sample }}
preserved-value:
{{ .Values.preserved | toYaml | indent 2 }}

# result:

sample-value: map[foo:bar]
preserved-value:
  foo: bar

There is also a special "set-only-if" template that enable to conditionally add an item to a list or dict:
(note that it also preserves type of non-string outputs like "preserve-type" template described above)

# values:

sample_list:
- some-value
- '{{ tuple "skipped" false | include "set-only-if" }}'
- '{{ tuple "included" true | include "set-only-if" }}'
sample_dict:
  some: value
  skipped: '{{ tuple "this key will not be set" false | include "set-only-if" }}'
  sample_list: | # note that you can also split template as a multiline string
    {{- $value := .Values.sample_list -}}
    {{ tuple $value true | include "set-only-if" }}

# template:

{{- $_ := set . "Values" (include "interpret-values-gotpl" . | fromJson)  -}}
{{ .Values | toYaml }}

# result:

sample_list:
- some-value
- included
sample_dict:
  some: value
  sample_list:
  - some-value
  - included


Note well that there are a few limitations:

* there is no error management on templating:
    foo: 42
    x: "{{ .Values.fooo }}" -> x after processing by this template will give "" (nothing complains about 'fooo' not being defined)

* everything looking like "{{ }}" will be interpreted, even non-gotpl stuff
  that you might want to try to put in your manifest because a given unit
  would need that

* templates that use "preserve-type" must define the whole key or value field, it can't be compound inline with a string:
  (this wouldn't make sense anyway, as you can't concaternate a string with another type)


To recap what happens when `preserve-type` is used in values.yaml and the result rendered in the final manifest:

value: prefix-{{ 42 | include "preserve-type" }}            -> will produce prefix-{"encapsulated-result":42}
value: '{{ print "prefix-" 42 | include "preserve-type" }}' -> will produce {"encapsulated-result":"prefix-42"}
value: "prefix-{{ 42 }}"                                    -> will also produce "prefix-42"

*/}}

{{ define "interpret-values-gotpl" }}
{{- $envAll := . }}
{{/* As this named template is called multiple time (once from each template file),
     check if values have already been interpreted to avoid unnecessary re-interpretation */}}
{{- if not ($envAll.Values._interpreted | default false) -}}
  {{/* we need to preserve this, to allow deferring template computation of _unit_name_ in unit-def */}}
  {{ $saved_unit_templates := deepCopy $envAll.Values.unit_templates }}
  {{ $saved_unit_definition_defaults := deepCopy ($envAll.Values.unit_definition_defaults | default dict) }}
  {{ $_ := set $envAll.Values "unit_templates" dict }}
  {{/* .Values._internal.state is interpreted first */}}
  {{ $_ := set $envAll.Values._internal "state" (index (tuple $envAll $envAll.Values._internal.state | include "interpret-inner-gotpl" | fromJson) "result") }}
  {{/* the rest of .Values._internal is interpreted next */}}
  {{ $_ := set $envAll.Values "_internal" (index (tuple $envAll $envAll.Values._internal | include "interpret-inner-gotpl" | fromJson) "result") }}
  {{ $_ := set $envAll "Values" (index (tuple $envAll $envAll.Values | include "interpret-inner-gotpl" | fromJson) "result") }}
  {{/* restore preserved values */}}
  {{ $_ := set $envAll.Values "unit_templates" $saved_unit_templates }}
  {{ $_ := set $envAll.Values "unit_definition_defaults" $saved_unit_definition_defaults }}
  {{ $_ := set $envAll.Values "_interpreted" true }}
{{- end }}
{{/* return result */}}
{{ $envAll.Values | toJson }}
{{ end }}

{{/*

preserve-type

The goal of this template is just to encapsulate a value into json, using a well known key to retrieve it later in interpret-inner-gotpl

Given that templating function (aka "tpl") only returns strings, it is impossible to retrieve the original type of values. For example:

# values:
test: 42
# template:
{{ tpl "{{ .Values.test }}" . | kindOf }}
# result:
string

This simple template enables the encapsulation of the template result in a json that will preserve the original type:

# values:
test: 42
# template:
{{ tpl "{{ .Values.test | include \"preserve-type\" }}" . }}
# result:
"{\"encapsulated-result\":42}"

The result is still a string, but we'll be able to match its signature and deserialize properly its content in interpret-inner-gotpl
*/}}

{{ define "preserve-type" }}
  {{- dict "encapsulated-result" . | toJson -}}
{{ end }}

{{/*

set-only-if

This is another utility template that enables to conditionally set an item in a list or dict.

If condition evaluates to false, it will return a very specific value that can be matched in interpret-inner-gotpl to skip the item.

For convenience, it also encaspsulates the result like in 'preserve-type' template in order to properly handle non-string items.

*/}}

{{ define "set-only-if" }}
  {{- if index . 1 -}}
    {{- dict "encapsulated-result" (index . 0) | toJson -}}
  {{- else -}}
    skip-as-set-only-if-result-was-false
  {{- end -}}
{{ end }}


{{/*

set-if-defined

This is another utility template that enables to conditionally set an item in a list or dict.

If the value passed is null, it will return a very specific value that can be matched in interpret-inner-gotpl to skip the item.

For convenience, it also encaspsulates the result like in 'preserve-type' template in order to properly handle non-string items.

Example:

  foo:
    bar:  '{{ .cluster.bar | include "set-if-defined" }}

  will set foo.bar only if cluster.bar is not null

  This is equivalent to: FIXME

*/}}

{{ define "set-if-defined" }}
  {{- if not (eq . nil) -}}
    {{- dict "encapsulated-result" . | toJson -}}
  {{- else -}}
    skip-as-set-only-if-result-was-false
  {{- end -}}
{{ end }}


{{/*

interpret-inner-gotpl

This is used to interpret any '{{ .. }}' templating found in a datastructure, doing that on all strings found at the different levels.

This template returns the resulting datastructure marshalled as a JSON dict {"result": ...}

Usage:

    tuple $envAll $data | include "interpret-inner-gotpl"

Example:

    $data := dict "foo" (dict "bar" "{{ .Values.bar }}")
    index (tuple $envAll $data | include "interpret-inner-gotpl" | fromJson) "result"

Values:

    bar: something here

Result:

    {"foo": {"bar": "something here"}}


Note well that there are a few limitations:

* there is no error management on templating:

    foo: 42
    x: "{{ .Values.fooo }}"  -> x after processing by this template will give "" (nothing complains about 'fooo' not being defined)

* the templating that you use cannot currently return anything else than a string.

    foo: 42
    x: "{{ .Values.foo }}"  -> x after processing by this template will give "42" not 42

    bar:
     - 1
     - 2
     - 3
    y: "{{ .Values.bar }}"  -> y after processing by this template will give '[1 2 3]', which is not what you want (not a list of numbers)

    In order to workaround this issue, you should pass the value to "preserve-type" template defined above:

    y: '{{ .Values.bar | include "preserve-type }}' -> will produce the expected content

* when a template refers to values that are themselves templated (aka "nested templating")
  you need to use helpers in some case:

    a: "foobar"  # this is a plain, non templated value
    b: "{{ .Values.a }}"  # this is a templated value, without nesting
    c: "{{ .Values.b }}"  # this is a templated value, _with_ nesting, given that b is itself templated

    # WRONG nested templating (it gives the base64 of the '{{ .Values.a }}' string, not the base64 of "foobar")
    d-broken: '{{ .Values.b | b64enc }}'  # WRONG
    # working version (gives the base64 of "foobar"):
    d-working: '{{ tuple . .Values.b | include "interpret-as-string" | b64enc }}'    

    # WRONG nested templating (it gives the boolean 'not' of the '{{ .Values.a }}' string, which will always evaluate to false, because the string is not empty)
    e-broken: '{{ not .Values.b }}'  # WRONG
    # working version:
    e-working: '{{ not (tuple . .Values.b | include "interpret-for-test")) }}'

* everything looking like "{{ }}" will be interpreted, even non-gotpl stuff
  that you might want to try to put in your manifest because a given unit
  would need that

*/}}

{{- define "interpret-inner-gotpl" -}}
    {{- $envAll := index . 0 -}}
    {{- $data := index . 1 -}}
    {{- $result := dict -}}
    {{- tuple $envAll $data $result | include "_interpret-inner-gotpl" -}}
    {{- $result | toJson -}}
{{- end -}}

{{- define "_interpret-inner-gotpl" -}}
    {{- $envAll := index . 0 -}}
    {{- $data := index . 1 -}}
    {{- $output := index . 2 -}}
    {{- $kind := kindOf $data -}}
    {{- $result := 0 -}}
    {{- $tmp_res := dict -}}
    {{- if (eq $kind "string") -}}
        {{- if regexMatch "(.|\n)*{{(.|\n)+}}(.|\n)*" $data -}}
            {{/* This is where we actually trigger GoTPL interpretation */}}
            {{- $tpl_res := tpl $data $envAll -}}
            {{- if (regexMatch "^( |\n)*{\"encapsulated-result\":" $tpl_res) -}}
                {{- $result = index (fromJson $tpl_res) "encapsulated-result" -}}
            {{- else -}}
                {{- $result = $tpl_res -}}
            {{- end -}}
            {{/* recurse to also interpret any nested GoTPL */}}
            {{- $_ := tuple $envAll $result $tmp_res | include "_interpret-inner-gotpl" -}}
            {{- $result = index $tmp_res "result" -}}
        {{- else -}}
            {{- $result = $data -}}
        {{- end -}}
    {{- else if (eq $kind "slice") -}}
        {{/* this is a list, recurse on each item */}}
        {{- $result = list -}}
        {{- range $data -}}
            {{- $_ := tuple $envAll . $tmp_res | include "_interpret-inner-gotpl" -}}
            {{- $tpl_item := index $tmp_res "result" -}}
            {{- if (eq (kindOf $tpl_item) "string") -}}
                {{- if (regexMatch "^( |\n)*{\"encapsulated-result\":" $tpl_item) -}}
                    {{- $result = append $result (index (fromJson $tpl_item) "encapsulated-result") -}}
                {{- else if (ne $tpl_item "skip-as-set-only-if-result-was-false") -}}
                    {{- $result = append $result $tpl_item -}}
                {{- end -}}
            {{- else -}}
                {{- $result = append $result $tpl_item -}}
            {{- end -}}
        {{- end -}}
    {{- else if (eq $kind "map") -}}
        {{/* this is a dictionary, recurse on each key-value pair */}}
        {{- $result = dict -}}
        {{- range $key,$value := $data -}}
            {{- $_ := tuple $envAll $key $tmp_res | include "_interpret-inner-gotpl" -}}
            {{- $tpl_key := index $tmp_res "result" -}}
            {{- $_ := tuple $envAll $value $tmp_res | include "_interpret-inner-gotpl" -}}
            {{- $tpl_value := index $tmp_res "result" -}}
            {{- if (eq (kindOf $tpl_value) "string") -}}
                {{- if (regexMatch "^( |\n)*{\"encapsulated-result\":" $tpl_value) -}}
                    {{- $_ := set $result $tpl_key (index (fromJson $tpl_value) "encapsulated-result") -}}
                {{- else if (ne $tpl_value "skip-as-set-only-if-result-was-false") -}}
                    {{- $_ := set $result $tpl_key $tpl_value -}}
                {{- end -}}
            {{- else -}}
                {{- $_ := set $result $tpl_key $tpl_value -}}
            {{- end -}}
        {{- end -}}
    {{- else -}}  {{/* bool, int, float64 */}}
        {{- $result = $data -}}
    {{- end -}}

{{- $_ := set $output "result" $result -}}
{{- end -}}


{{/*

interpret

Usage:

  tuple . "path.of.value.to.interpret"  | include "interpret"

It is meant to be used in Helm values, as a way to fix the nested templating issue described in "interpret-inner-gotpl" doc above.

This function triggers the interpretation of the value at provided path; it can be used to forcefully interpret a given value prior to using it.

Example:

    a: "foobar"  # this is a plain, non templated value
    b: "{{ .Values.a }}"  # this is a templated value, without nesting

    # WRONG nested templating (it gives the base64 of the '{{ .Values.a }}' string, not the base64 of "foobar")
    d-broken: '{{ .Values.b | b64enc }}'  # WRONG
    # working version (gives the base64 of "foobar"):
    d-working: '{{ tuple . ".b" | include "interpret"}}{{ .Values.b | b64enc }}'  

*/}}
{{- define "interpret" -}}
  {{- $envAll := index . 0 -}}
  {{- $path := index . 1 -}}
  {{- if gt (len .) 2 -}}
    {{- fail (printf "'interpret' accepts only 2 parameters, was given %d (arguments after first one: %s)" (len .) (slice . 1|toJson)) -}}
  {{- end -}}
  {{- $keys := splitList "." $path -}}
  {{- tuple $envAll $envAll.Values ($keys | first) ($keys | rest) "" | include "_interpret" -}}
{{- end -}}

{{/* Internal recursive implementation of interpret */}}

{{- define "_interpret" -}}
  {{- $envAll := index . 0 -}}
  {{- $data := index . 1 -}}
  {{- $key := index . 2 -}}
  {{- $remainingKeys := index . 3 -}}
  {{- $path := index . 4 -}}
  {{- $path := printf "%s.%s" $path $key -}}
  {{- if hasKey $data $key | not -}}
    {{- fail (printf "'interpret' called on key '%s' not found in .Values.%s" $key $path) -}}
  {{- end -}}
  {{- if $remainingKeys | len | eq 0 -}}
    {{- $interpreted := index (tuple $envAll (get $data $key) | include "interpret-inner-gotpl" | fromJson) "result" -}}
    {{- $_ := set $data $key $interpreted -}}
  {{- else -}}
    {{- tuple $envAll (get $data $key) ($remainingKeys | first) ($remainingKeys | rest) $path | include "_interpret" -}}
  {{- end -}}
{{- end -}}


{{/*

interpret-as-string

Usage:

  tuple $envAll $data | include "interpret-as-string"

It is meant to be used in Helm values.

It will fail if the result of the interpretation is not a string.

See the documentation of "interpret-inner-gotpl" which has examples
explaining the rationale behind this function.

*/}}
{{- define "interpret-as-string" -}}
    {{- $envAll := index . 0 -}}
    {{- $data := index . 1 -}}

    {{- if not (kindIs "string" $data) -}}
        {{- fail (printf "'interpret-as-string' called on something which is not a string (<%s> is %s)" ($data | toString) (typeOf $data)) -}}
    {{- end -}}

    {{- $interpreted := index (tuple $envAll $data | include "interpret-inner-gotpl" | fromJson) "result" -}}

    {{- if kindIs "string" $interpreted -}}
        {{- $interpreted -}}
    {{- else -}}
        {{- fail (printf "'interpret-as-string' called on something which did not evaluate as a string (<%s> evaluates to <%s>, a %s)" ($data | toString) ($interpreted|toString) (typeOf $interpreted)) -}}
    {{- end -}}
{{- end -}}


{{/*

as-bool / as-bool-internal

  *** as-bool ***

The 'as-bool' named template transforms a boolean (or a pseudo-boolean string "true"/"false"/"")
into a {"encapsulated-result":true} or {"encapsulated-result":false}.

This is used to return something that our template code understands as a typed boolean,
compensating for the inability of Helm templating ('include "foo" ...') to return typed
values.

This "as-bool" template is used:
- in the templating code (in interpret-as-bool below)
- in 'values.yaml' to enfore the production of a real boolean in manifests

Example (in values.yaml):

  enableBar: '{{ not (tuple . .Values.units.foo.enabled | include "interpret-for-test") | include "as-bool" }}'

This ensures that enableBar will be produced as a boolean (rather than a sting like "true" or "false")


  *** as-bool-internal ***

'as-bool-internal' accept a tuple as parameter, the first item being the value to use,
the second one being optional and containing a string used to provide a helpful debug
message

this 'as-bool-internal' template is used only from 'interpret-as-bool' and 'as-bool'

*/}}
{{- define "as-bool-internal" -}}
  {{- $data := index . 0 -}}
  {{- $debug_context := "" -}}
  {{- if gt (len .) 1 -}}
    {{- $debug_context = printf " [%s]" (index . 1) -}}
  {{- end -}}

  {{- if kindIs "bool" $data -}}
    {{- dict "encapsulated-result" $data | toJson -}}
  {{- else if kindIs "string" $data -}}
    {{- if $data | eq "true" -}}
      {{- dict "encapsulated-result" true | toJson -}}
    {{- else if or ($data | eq "false") ($data | eq "") -}}
      {{- dict "encapsulated-result" false | toJson -}}
    {{- else -}}
      {{- fail (printf "can't cast '%s' as a bool%s" $data $debug_context) -}}
    {{- end -}}
  {{- else -}}
    {{- fail (printf "can't cast <%s> (type %s) as a bool%s" $data (kindOf $data) $debug_context) -}}
  {{- end -}}
{{- end -}}

{{- define "as-bool" -}}
  {{- $data := index . -}}
  {{- tuple $data | include "as-bool-internal" -}}
{{- end -}}



{{/*

interpret-as-bool

Usage:

  tuple $envAll $data | include "interpret-as-bool"

This will:
* recursively interpret $data, insuring that it looks like a boolean
  (taking into account Helm and gotpl quirks, like the fact that "and foo ''"
  returns '' not false)
* return this boolean marshalled into a {"encapsulated-result": result} dict

It will fail if the result of the interpretation does not look like a boolean.

*/}}
{{- define "interpret-as-bool" -}}
    {{- $envAll := index . 0 -}}
    {{- $data := index . 1 -}}

    {{- $debug_context := "" -}}
    {{- if gt (len .) 2 -}}
        {{- $debug_context = printf ", %s" (index . 2) -}}
    {{- end -}}

    {{- if kindIs "bool" $data -}}
        {{- $data | include "as-bool" -}}
    {{- else -}}
        {{- if not (kindIs "string" $data) -}}
            {{- fail (printf "'interpret-as-bool' called on something which is not boolean nor a string (<%s> is a %s)%s" ($data | toString) (typeOf $data) $debug_context) -}}
        {{- end -}}

        {{- if or ($data | eq "true") ($data | eq "false") ($data | eq "") -}}
            {{- $data | include "as-bool" -}}
        {{- else -}}
            {{- $interpreted := index (tuple $envAll $data | include "interpret-inner-gotpl" | fromJson) "result" -}}
            {{- tuple $interpreted (printf "result of interpretation of '%s'%s" $data $debug_context) | include "as-bool-internal" -}}
        {{- end -}}
    {{- end -}}
{{- end -}}


{{/*

interpret-for-test

Usage:

  tuple $envAll $data | include "interpret-for-test"

It is meant to be used in Helm values.

It evaluates $data as a boolean (recursively), and returns either "true" (string) or "" (empty string).
The use for this template is specific to tests.

*/}}
{{- define "interpret-for-test" -}}
    {{- $envAll := index . 0 -}}
    {{- $data := index . 1 -}}

    {{- $debug_context := "interpret-for-test" -}}
    {{- if gt (len .) 2 -}}
        {{- $debug_context = printf "interpret-for-test, %s" (index . 2) -}}
    {{- end -}}

    {{- $value := index (tuple $envAll $data $debug_context | include "interpret-as-bool" | fromJson) "encapsulated-result" -}}

    {{- if $value -}}
true
    {{- else -}} {{- /* we "emulate" a 'false' value by returning an empty string which the caller will evaluate as False */ -}}
    {{- end -}}
{{- end -}}

{{/*

interpret-ternary

Usage:

  tuple $envAll $data $value_if_data_interprets_as_true $value_if_data_interprets_as_false | include "interpret-ternary"

It is meant to be used in Helm values.

It evaluates $data as a boolean (recursively), and returns either $value_if_data_interprets_as_true or $value_if_data_interprets_as_false,
depending on whether $data is true or false after interpretation.

*/}}
{{- define "interpret-ternary" -}}
    {{- $envAll := index . 0 -}}
    {{- $data := index . 1 -}}
    {{- $true_value := index . 2 -}}
    {{- $false_value := index . 3 -}}

    {{- $debug_context := "interpret-ternary" -}}
    {{- if gt (len .) 4 -}}
        {{- $debug_context = printf "interpret-ternary, %s" (index . 4) -}}
    {{- end -}}

    {{- $interpreted_data := index (tuple $envAll $data $debug_context | include "interpret-as-bool" | fromJson) "encapsulated-result" -}}

    {{- if $interpreted_data -}}
      {{- $true_value -}}
    {{- else -}}
      {{- $false_value -}}
    {{- end -}}
{{- end -}}



{{/*

interpret-and-hash

Usage:

  tuple $envAll $data  | include "interpret-and-hash"

This function inteprets $data and then computes the sha256sum of the JSON rendering of the result.

This was initially meant to be a helper for computing JOB_CHECKSUM.

*/}}
{{- define "interpret-and-hash" -}}
  {{- $envAll := index . 0 -}}
  {{- $data := index . 1 -}}
  {{- $interpreted := index (tuple $envAll $data | include "interpret-inner-gotpl" | fromJson) "result" -}}
  {{/* produce result: */}}
  {{- $interpreted | toJson | sha256sum -}}
{{- end -}}
