# Sets of Helm values overrides

Each of the subdirectories contains a set of files used as Helm values override.

For each of these sub-directories the "sylva-units:helm-template-yamllint"
CI job (defined in `.gitlab/ci`)  will give all YAML files as inputs to
"helm template" (which will validate against the Helm schema) and also check the
result with `yamllint`.

## Negative test cases

A `test-spec.yaml` file can be put in any such directory. Setting `require-failure: true`
in this file allows you to specify that a test case is a intended to fail.
