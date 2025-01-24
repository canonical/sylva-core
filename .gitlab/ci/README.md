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

- `wkld-sso-kubeconfig` that downloads the Rancher Kubeconfig for the sample workload cluster, if job is using a variable `DEPLOY_WORKLOAD_CLUSTER: "TRUE"`, i.e. the job does deploy the sample workload cluster <br/>
      and then creates a pod using this this kubeconfig <br/>

- `mgmt-sso`, that tests SSO login (to the UIs for which an endpoint is exported in CI job script) <br/>
- `wkld-no-sso-kubeconfig`, get Rancher Kubeconfig without SSO and create test pod into workload cluster.
