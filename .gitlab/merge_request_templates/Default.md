## What does this MR do and why?

%{first_multiline_commit}

### Related reference(s)

## Test coverage

<!-- Explain which tests have been added for covering the new behavior.
     As a last resort, indicate what kind of manual testing was done. -->

## CI configuration

CI pipelines perform an update for both management and workload clusters, this update will **NOT** perform a ClusterAPI rolling update (deletion and creation of new K8s nodes) by default.

For some cases, it may be relevant to perform more complex tests.

Theses features can be activated in an MR by adding one of these labels to the MR and will apply to the next pipelines.

* adding the label ~ci-feature::test-rolling-update pipelines will perform a node rolling update in the `-update` jobs (without version upgrades)
* adding the label ~ci-feature::test-upgrade-from-1.2.1 pipelines will perform an upgrade from Sylva 1.2.1 to your dev branch (including a k8s version upgrade resulting in a node rolling update)
