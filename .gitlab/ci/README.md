This directory contains GitLab-ci templates, scripts used to generate jobs and linter config files.

`scripts`: scripts used in CI
`configuration`: configuration files used in CI

Some `*_ADDITIONAL_VALUES` variables are available for specifying a file or a list of files (separate by space char) which defines some additional [**sylva-units**](../../charts/sylva-units) values that are merged on top of what we have in the environment-values directory used for a CI job (be it all in a local `values.yaml` or partly coming from a kustomization remote resource). In case of a list of file they are merged in order.

For context, since the job filesystem is cleaned between jobs (that's a GitLab CI principle), the contents of `$values_file` is not passed from one job to the next job in the same pipeline (for example the `update-workload-cluster` won't have the additional values passed by *yq merge* to `deploy-workload-cluster`).

That's why the following were implemented:

- `MGMT_ADDITIONAL_VALUES`: common base for the whole management cluster pipeline (deployment and update stages) values
- `MGMT_INITIAL_ADDITIONAL_VALUES`: values only for management cluster DEPLOYMENT job
- `MGMT_UPDATE_ADDITIONAL_VALUES`: values only for the management cluster UPDATE job

- `WC_ADDITIONAL_VALUES`: common base for the whole workload cluster pipeline (deployment and update stages) values
- `WC_INITIAL_ADDITIONAL_VALUES`: values only for workload cluster DEPLOYMENT job
- `WC_UPDATE_ADDITIONAL_VALUES`: values only for workload cluster UPDATE job

During `deployment-test` stage we run one of:

- `test-sso+workload-kubeconfig` that does<br/>

   1) runs the [Selenium script](../../tools/login-test/test-sso.py), which <br/>
     1.1) tests SSO login (to the UIs for which an endpoint is exported in CI job script, the `capo-misc-units-deploy` ones like Harbor and Neuvector are not) <br/>
     1.2) and also downloads the Rancher Kubeconfig for the sample workload cluster, if job is **not** using a variable `ONLY_DEPLOY_MGMT: "TRUE"`, i.e. the job does deploy the sample workload cluster <br/>
   2) and then does some more with this kubeconfig, creating a test pod <br/>

- `test-sso`, that only does 1.1) from above, when we only deploy the management cluster (like in `capo-fip` or `capo-misc-units` CI variants)
- `test-no-sso`, get Rancher Kubeconfig without SSO and create test pod into workload cluster.

- `test-login`, job is designed to verify access to each component deployed in Sylva on both management and workload clusters.
    1) Pre-requisities on CI test
        The managment cluster and workload should be created before launching the CI test-login
        We need to set extends to `.test-tags` corresponding  to tests jobs done though Docker executor based on runner for capo, capm3 ONLY.

    2) Pre-requisities on env
        the variable HURL_JUNIT_REPORT should be set, and corresponding to future HURL report

    3) it runs the Hurl tests for accessing to
          - grafana.sylva
          - Rancher.sylva
          - flux.sylva
          - harbor.sylva
          - keycloak.sylva
          - minio-monitoring-tenant.sylva
          - minio-monitoring-tenant-console.sylva
          - minio-operator-console.sylva
          - thanos-query.sylva
          - thanos.sylva
          - thanos-receive.sylva
          - thanos-storegateway.sylva
          - vault.sylva
