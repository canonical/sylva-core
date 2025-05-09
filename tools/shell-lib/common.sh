#!/bin/bash

set -eu
set -o pipefail

export BASE_DIR="$(dirname $(realpath $0))"
export USER_DIR="$(dirname $0)"

# source sylva.env first
if [[ -f "${USER_DIR}/sylva.env" ]]; then
  source "${USER_DIR}/sylva.env"
fi

export PATH=${USER_DIR}/bin:${PATH}
export KIND_CLUSTER_NAME=${KIND_CLUSTER_NAME:-sylva}

SYLVA_BASE_OCI_REGISTRY=${SYLVA_BASE_OCI_REGISTRY:-registry.gitlab.com/sylva-projects}
SYLVA_TOOLBOX_VERSION=${SYLVA_TOOLBOX_VERSION:-"v0.10.2"}
SYLVA_TOOLBOX_IMAGE=${SYLVA_TOOLBOX_IMAGE:-container-images/sylva-toolbox}
SYLVA_TOOLBOX_REGISTRY=${SYLVA_TOOLBOX_REGISTRY:-${SYLVA_BASE_OCI_REGISTRY}/sylva-elements}
export KIND_POD_SUBNET=${KIND_POD_SUBNET:-100.100.0.0/16}
export KIND_SVC_SUBNET=${KIND_SVC_SUBNET:-100.96.0.0/16}

UNIT_TIMEOUT_ARGS=""
[ -n "${UNIT_TIMEOUT_FACTOR:-}" ] && UNIT_TIMEOUT_ARGS+="--unit-timeout-factor $UNIT_TIMEOUT_FACTOR "
[ -n "${UNIT_TIMEOUT:-}" ] && UNIT_TIMEOUT_ARGS+="--unit-timeout $UNIT_TIMEOUT"

if [[ -n "${CI:-}" ]]; then
  SYLVACTL_SAVE=1
  CHECK_TEST_UNITS=1
fi

function check_args() {
  if ! [[ ${#BASH_ARGV[@]} -eq 1 && (-f ${BASH_ARGV[0]}/kustomization.yaml || -L ${BASH_ARGV[0]}/kustomization.yaml) ]]; then 
    echo "Usage: $BASH_ARGV0 [env_name]"
    echo "This script expects to find a kustomization in [env_name] directory to generate management-cluster configuration and secrets"
    exit 1
  else
    export ENV_PATH=$(readlink -f ${BASH_ARGV[0]})
  fi
}

function sylva_init {
  if ! python3 -c 'import yaml' &>/dev/null; then
      echo "PyYAML python package is required to run this script, install it on your system and start over."
      exit 1
  fi

  if ! python3 -c 'import yamllint' &>/dev/null; then
      echo "yamllint python package is required to run this script, install it on your system and start over."
      exit 1
  fi
}

function apply_scripts_init {
  sylva_init
  ensure_sylva_toolbox
  ensure_sylvactl
  trap exit_trap EXIT
  trap 'echo "Interrupted!"; exit 1' SIGINT
}


function _kustomize {
  kustomize build --load-restrictor LoadRestrictionsNone $1
}
export -f _kustomize

function set_wc_namespace() {
  local WORKLOAD_CLUSTER_NAMESPACE=$(basename ${ENV_PATH})
  sed "s/WORKLOAD_CLUSTER_NAMESPACE/${WORKLOAD_CLUSTER_NAMESPACE}/g"
}

function check_apply_kustomizations() {
  CALLER_SCRIPT_NAME=$(basename ${BASH_SOURCE[1]})
  if [[ $CALLER_SCRIPT_NAME == *"apply.sh"* ]]; then
    if [[ "$ENV_PATH" == *workload-clusters* ]]; then
      echo "Error: you shouldn't be running apply.sh against a workload cluster directory ($ENV_PATH)."
      exit 1
    fi
    result=$(_kustomize $ENV_PATH | yq eval-all -e 'select(.kind == "HelmRelease").spec.chart.spec.valuesFiles | any_c(. | test("(^|/)management.values.yaml$")) and select(.kind == "Namespace").metadata.name == "sylva-system"' 2>/dev/null ||:)
    if [[ $result != *"true"* ]]; then
      echo "The directory passed does not contain a management cluster kustomization."
      exit 1
    fi
  fi

  if [[ $CALLER_SCRIPT_NAME == *"apply-workload-cluster.sh"* ]]; then
    wc_dir_name=$(basename "$ENV_PATH")
    if [[ "$wc_dir_name" == "sylva-system" ]]; then
      echo "Error: Please provide a valid workload cluster directory name, other than \"sylva-system\"."
      exit 1
    fi
    result=$(_kustomize ${ENV_PATH} | set_wc_namespace | yq eval-all -e 'select(.kind == "HelmRelease").spec.chart.spec.valuesFiles | any_c(. | test("(^|/)workload-cluster.values.yaml$")) and select(.kind == "Namespace").metadata.name != "sylva-system"' 2>/dev/null ||:)
    if [[ $result != *"true"* ]]; then
      echo "The directory passed does not contains a workload cluster kustomization."
      exit 1
    fi
  fi
}

function echo_b() {
  end_section

  current_section_number=$(( ${current_section_number:-0} + 1))
  echo -e "\e[1m\e[0Ksection_start:`date +%s`:section_${current_section_number}[collapsed=true]\r\e[0K$*\e[0m"
}

function end_section() {
  # this is also called from EXIT trap to ensure that we always close the last section

  if (( ${current_section_number:-0} > 0 )) ; then
    echo -e "\e[0Ksection_end:`date +%s`:section_${current_section_number}\r\e[0K"
  fi
}

function set_current_namespace {
  kubectl config set-context --current --namespace=$1
}

function check_pivot_has_ran() {
  if kubectl wait --for condition=complete --timeout=0s job pivot -n sylva-system > /dev/null 2>&1; then
      if [ ! -f "management-cluster-kubeconfig" ]; then
          kubectl get secret management-cluster-kubeconfig-copy -o jsonpath='{.data.value}' 2>/dev/null | base64 -d > management-cluster-kubeconfig
      fi
      echo_b "\U000274C The pivot job has already ran and moved resources to the management cluster. Please use apply.sh instead of bootstrap.sh"
      exit 1
  fi
  if kubectl get customresourcedefinitions.apiextensions.k8s.io kustomizations.kustomize.toolkit.fluxcd.io &>/dev/null; then
    if [ -n "$(kubectl get kustomizations.kustomize.toolkit.fluxcd.io cluster -o jsonpath='{.metadata.annotations.pivot/started}' 2>/dev/null)" ]; then
      { echo_b "\U000274C The pivot job is in progress. Please wait for it to finish."; exit 1;} || echo
    fi
  fi
}

function validate_input_values {
  echo_b "\U0001F50E Validate input files"
  yamllint -c ${BASE_DIR}/tools/shell-lib/yamllint-validate.conf.yaml $ENV_PATH/*.y*ml
}

function retrieve_kubeconfig {
    orig_umask=$(umask)
    umask og-rw
    until kubectl get secret $(kubectl get cluster.cluster.x-k8s.io -o jsonpath='{ $.items[*].metadata.name}' 2>/dev/null)-kubeconfig -o jsonpath='{.data.value}' 2>/dev/null | base64 -d > management-cluster-kubeconfig; do
        sleep 2
    done
    # Check if there is an alternative public endpoint declared in values, in which case we modify kubeconfig to use it
    if kubectl get secret sylva-units-values -o template='{{ .data.values }}' | base64 -d | yq -e .cluster_public_endpoint &> /dev/null; then
        CLUSTER_PUBLIC_ENDPOINT=$(kubectl get secret sylva-units-values -o template='{{ .data.values }}' | base64 -d | yq -e .cluster_public_endpoint)
        yq -i ".clusters[0].cluster.server=\"${CLUSTER_PUBLIC_ENDPOINT}\"" management-cluster-kubeconfig
    fi
    kubectl --kubeconfig=management-cluster-kubeconfig config set-context --current --namespace=sylva-system
    umask $orig_umask
}

function check_management_kubeconfig() {
    if ! kubectl get -n sylva-system kustomization management-flag &>/dev/null; then
        echo_b "\U000026A0 Provided kubeconfig ($KUBECONFIG) does not seem to target management cluster, aborting."
        exit 1
    fi
}

function ensure_flux {
    if ! kubectl get namespace flux-system &>/dev/null; then
        echo_b "\U0001F503 Install flux"
        flux install --components "source-controller,kustomize-controller,helm-controller" --namespace=flux-system --export > ${BASE_DIR}/kustomize-units/flux-system/offline/manifests.yaml
        if _kustomize ${ENV_PATH} | python3 ${BASE_DIR}/tools/extractHelmReleaseValues.py --values-path .spec.valuesFrom | yq -e '.oci_registry_extra_ca_certs' &>/dev/null; then
            if ! yq -e '.components[] | select(. == "../components/extra-ca")' ${BASE_DIR}/kustomize-units/flux-system/offline/kustomization.yaml &> /dev/null; then
                yq -i '.components += ["../components/extra-ca"]' ${BASE_DIR}/kustomize-units/flux-system/offline/kustomization.yaml
            fi
            B64_CERTS=$(_kustomize ${ENV_PATH} | python3 ${BASE_DIR}/tools/extractHelmReleaseValues.py --values-path .spec.valuesFrom | yq '.oci_registry_extra_ca_certs | @base64')
            yq -i ".data[\"extra-ca-certs.pem\"]=\"$B64_CERTS\"" ${BASE_DIR}/kustomize-units/flux-system/components/extra-ca/certs.yaml
        fi
        _kustomize ${BASE_DIR}/kustomize-units/flux-system/offline | envsubst | kubectl apply -f -
        if [ -d "$BASE_DIR/.git" ] && command -v git &>/dev/null ; then
          (pushd $BASE_DIR && git checkout HEAD -- ./kustomize-units/flux-system/;) &>/dev/null
        fi
        echo_b "\U000023F3 Wait for Flux to be ready..."
        kubectl wait --for condition=Available --timeout 600s -n flux-system --all deployment
    fi
}

function ensure_sylva_toolbox {
    if ! command -v docker >/dev/null; then
        echo "Docker is a prerequisite for the installation of sylva-toolbox"
        exit 1
    fi
    if [[ ! -f  ${USER_DIR}/bin/sylva-toolbox-version || $(awk -F : '$1=="sylva-toolbox" {print $2}' ${USER_DIR}/bin/sylva-toolbox-version) != $SYLVA_TOOLBOX_VERSION ]]; then
        echo_b "\U0001F4E5 Installing sylva-toolbox binaries"
        mkdir -p ${USER_DIR}/bin
        docker run --rm ${SYLVA_TOOLBOX_REGISTRY}/${SYLVA_TOOLBOX_IMAGE}:${SYLVA_TOOLBOX_VERSION} | tar xz -C ${USER_DIR}/bin
    fi
}

function ensure_sylvactl {
    if [[ -n ${SYLVACTL_VERSION:-} ]] && [[ ${SYLVACTL_VERSION} != $(${USER_DIR}/bin/sylvactl version 2>&1) ]]; then
        SYLVACTL_RELEASE_NAME="sylvactl"
        UNSTABLE_REGEXP='^0\.0\.0-git-.*|^main$'
        [[ $SYLVACTL_VERSION =~ $UNSTABLE_REGEXP ]] && SYLVACTL_RELEASE_NAME="sylvactl-unstable" || true
        echo_b "\U0001F4E5 Downloading ${SYLVACTL_RELEASE_NAME} version: ${SYLVACTL_VERSION}"
        mkdir -p ${USER_DIR}/bin
        curl -q --progress-bar -f https://gitlab.com/api/v4/projects/43501695/packages/generic/$SYLVACTL_RELEASE_NAME/$SYLVACTL_VERSION/sylvactl -o ${USER_DIR}/bin/sylvactl
        chmod +x ${USER_DIR}/bin/sylvactl
    fi
}

function cleanup_bootstrap_cluster() {
  : ${CLEANUP_BOOTSTRAP_CLUSTER:='yes'}
  CALLER_SCRIPT_NAME=$(basename $0)
  kind_clusters=`kind get clusters -q`

  # if caller script is bootstrap.sh or apply.sh, current bootstrap-cluster contains sylva bootstrap-cluster and pivot was successful - then delete it
  if [[ $CALLER_SCRIPT_NAME =~ "bootstrap.sh"|"apply.sh" && ${kind_clusters} =~ $KIND_CLUSTER_NAME ]]; then
    libvirt_metal_ks=`KUBECONFIG= kubectl get ks -l sylva-units.unit=libvirt-metal -o yaml | yq '.items|length'`
    if [[ $CLEANUP_BOOTSTRAP_CLUSTER == 'yes' && $libvirt_metal_ks == "0" ]]; then
      echo_b "\U0001F5D1 Delete bootstrap cluster"
      if KUBECONFIG= kubectl wait job --for=jsonpath={.status.succeeded}=1 pivot; then
        kind delete cluster -n $KIND_CLUSTER_NAME
      else
        echo "Cannot delete bootstrap cluster as 'pivot' Kustomization is not ready."
        echo "To delete the bootstrap cluster, you can re-run apply.sh anytime after fixing this."
        exit 1
      fi
      end_section
    fi
  fi
}

function exit_trap() {
    EXIT_CODE=$?

    # Call debug script if needed
    if [[ $EXIT_CODE -ne 0 && ${DEBUG_ON_EXIT:-"0"} -eq 1 ]] || [[ -n "${CI:-}" ]]; then
        echo_b "gathering debugging logs in debug-on-exit.log file"
        ${BASE_DIR}/tools/shell-lib/debug-on-exit.sh 2>&1 | tee debug-on-exit.log
        end_section
    fi

    # call cleanup only when script exists successfully
    if [[ $EXIT_CODE -eq 0 ]]; then
      cleanup_bootstrap_cluster
    fi

    # Kill all child processes (kubectl watches) on exit
    pids="$(jobs -rp)"
    [ -n "$pids" ] && kill $pids || true
    exit $EXIT_CODE
}

function reconcile_sylva_units() {
  local namespace=${1:-sylva-system}
  local _options=${2:-}

  echo "trigger reconciliation of sylva-units HelmRelease..."
  RECONCILE_REQUEST_DATE=$(date -uIs | sed -e 's/+00:00//')

  # we need to ensure that:
  # - we force an update of sylva-units HelmRelease **if it was in error state**
  # - we don't return until the HelmRelease has reconciled (and that the last revision of the source was reconciled first)
  #   (this last point is important in particular because we most often follow with a "sylvactl watch"
  #    which can't give a relevant result if it starts before all Kustomizations are the new ones)
  #
  FORCE_RECONCILE_ANNOTATION=""
  if (kubectl get -n $namespace HelmRelease sylva-units -o yaml | yq -e '.status.conditions[] | select(.type=="Ready") | (.reason == "InstallFailed" or .reason == "UpgradeFailed")' >& /dev/null); then
    echo "  using forced reconciliation"
    FORCE_RECONCILE_ANNOTATION="reconcile.fluxcd.io/forceAt=$RECONCILE_REQUEST_DATE"
  fi
  kubectl annotate -n $namespace --overwrite HelmRelease sylva-units \
      reconcile.fluxcd.io/requestedAt=$RECONCILE_REQUEST_DATE \
      $FORCE_RECONCILE_ANNOTATION \
    | sed -e 's/^/  /'

  resume_suspended="--resume-suspended"
  if [[ $_options == *"skip-resume-suspended"* ]]; then
    echo "not using --resume-suspended"
    resume_suspended=""
  fi

  sylvactl watch -n $namespace HelmRelease/$namespace/sylva-units --timeout ${SYLVA_UNITS_RECONCILE_TIMEOUT:-180s} --skip-inventory \
    ${SYLVACTL_RECORD:+--record reconcile-su-$namespace-record.yaml} \
    --reconcile $resume_suspended \
    --exit-condition reason=UpgradeFailed \
    --exit-condition reason=InstallFailed

  helm_release_version=$(kubectl get -n $namespace HelmRelease sylva-units -o yaml | yq -r '.status.history[0].version')
  if ! [[ $_options == *"skip-root-dependency-wait"* ]] && kubectl get -n $namespace Kustomization root-dependency-$helm_release_version &>/dev/null; then
    echo "waiting for root-dependency-$helm_release_version to become ready..."
    sylvactl watch -n $namespace Kustomization/$namespace/root-dependency-$helm_release_version --timeout ${SYLVA_UNITS_RECONCILE_TIMEOUT:-180s} --skip-inventory --reconcile
  fi
}

function define_source() {

  if (command -v git && pushd $BASE_DIR && git rev-parse --is-inside-work-tree;) &> /dev/null; then
    pushd $BASE_DIR &> /dev/null
    export SYLVA_CORE_COMMIT=${SYLVA_CORE_COMMIT:-$(git rev-parse HEAD)}
    export SYLVA_CORE_REPO=${SYLVA_CORE_REPO:-$(git remote get-url origin | sed 's|^git@\([^:]\+\):|https://\1/|' | sed 's|gitlab-ci-token.*@||')}
    popd &> /dev/null
  else
    [ -z "${SYLVA_CORE_COMMIT:-}" ] && (echo >&2 "[INFO] Unable to determine current commit. Make sure to use OCI artifacts for deployment";)
    export SYLVA_CORE_REPO=${SYLVA_CORE_REPO:-"https://gitlab.com/sylva-projects/sylva-core"}
  fi
  [ -n "${SYLVA_CORE_COMMIT:-}" ] && echo >&2 "[INFO] Using ${SYLVA_CORE_COMMIT:-}";

  sed "s/CURRENT_COMMIT/${SYLVA_CORE_COMMIT:-"xxxxxx"}/" "$@" | \
  sed "s,SYLVA_CORE_REPO,${SYLVA_CORE_REPO},g" "$@" | \
  sed "s,SYLVA_BASE_OCI_REGISTRY,${SYLVA_BASE_OCI_REGISTRY},g" "$@"
}

function suspend_sylva_units {
  local ns=${1:-sylva-system}

  if [[ $(kubectl -n $ns get helmreleases.helm.toolkit.fluxcd.io sylva-units 2>&1 || true) == *"not found" ]]; then
    echo "no sylva-units HelmRelease found, nothing to suspend"
  else
    echo -e "\U000023F8 Suspend sylva-units HelmRelease/HelmChart"
    kubectl -n $ns patch helmreleases.helm.toolkit.fluxcd.io sylva-units       --type=merge --patch='{"spec":{"suspend":true}}'
    kubectl -n $ns patch helmcharts.source.toolkit.fluxcd.io ${ns}-sylva-units --type=merge --patch='{"spec":{"suspend":true}}'
  fi
}

function inject_bootstrap_values() {
  # this function transforms the output of '_kustomize ${ENV_PATH}'
  # to add bootstrap.values.yaml into the valuesFiles field of the HelmRelease
  #
  # this field is not exactly the same depending on whether we use a GitRepository as sources
  # or a HelmRepository (which is what we use for a deployment from OCI artifacts)

  # additionally, in the case of an OCI-based deployment, we need to insert "bootstrap.values.yaml"
  # before the "use-oci-artifacts.values.yaml" which has to be the last element to have
  # precedence over what is defined in "bootstrap.values.yaml"

  # shellcheck disable=SC2016
  yq eval-all '
    (select(.kind == "HelmRepository" and .spec.type == "oci") | length > 0 | to_yaml | trim) as $oci
    | select(.kind == "HelmRelease").spec.chart.spec.valuesFiles = ([
      {"true":"","false":"charts/sylva-units/"}[$oci] + "values.yaml",
      {"true":"","false":"charts/sylva-units/"}[$oci] + "management.values.yaml",
      {"true":"","false":"charts/sylva-units/"}[$oci] + "bootstrap.values.yaml"
    ] + {"true":["use-oci-artifacts.values.yaml"],"false":[]}[$oci])
    | select(.kind == "HelmRelease").spec.chart.spec.valuesFiles = (select(.kind == "HelmRelease").spec.chart.spec.valuesFiles | unique)
  '
  # explanations on the code above:
  # - ... as $oci on the first line produces a boolean (or nearly, see below)
  # - we use the {true: A, false: B}[x] construct to emulate the behavior of 'if x then A else B' (jq has such an if/else statement, but yq does not)
  # - the keys of this true/false map are actually strings, because yq does not support booleans as indexes
  # - this is why $oci is made into a string ('| to_yaml | trim' emulates '|tostring' which is not provided by yq)
}

function validate_sylva_units() {
  # Create & install sylva-units preview Helm release
  # If a Kustomization with the label:  previewNamespace=sylva-units-preview
  # exists, we define a targetNamespace to target sylva-units-preview
  PREVIEW_DIR=${BASE_DIR}/sylva-units-preview
  mkdir -p ${PREVIEW_DIR}
  cat <<-EOF > ${PREVIEW_DIR}/kustomization.yaml
        apiVersion: kustomize.config.k8s.io/v1beta1
        kind: Kustomization
        resources:
        - $(realpath --relative-to=${PREVIEW_DIR} ${ENV_PATH})
        components:
        - $(realpath --relative-to=${PREVIEW_DIR} ${BASE_DIR}/environment-values/preview)
        patches:
          - target:
              kind: Kustomization
              labelSelector: previewNamespace=sylva-units-preview
            patch: |
              - op: add
                path: /spec/targetNamespace
                value: sylva-units-preview
EOF

  if [[ ${KUBECONFIG:-} =~ management-cluster-kubeconfig$ ]] || [[ ${1:-} == "force-management" ]]; then
    bootstrap=no
  else
    bootstrap=yes
  fi

  # for bootstrap cluster, we need to inject bootstrap values
  # (for mgmt cluster, we do not so we "pipe through" with "cat")
  _kustomize ${PREVIEW_DIR} \
    | define_source \
    | (if [[ $bootstrap == "yes" ]]; then inject_bootstrap_values ; else cat ; fi) \
    | kubectl apply -f -
  rm -Rf ${PREVIEW_DIR}

  # this is just to force-refresh in a dev environment with  refreshed parameters
  reconcile_sylva_units sylva-units-preview skip-root-dependency-wait,skip-resume-suspended

}

function cleanup_preview() {
  kubectl get -n sylva-units-preview helmrelease/sylva-units gitrepository/sylva-core helmrepository/sylva-core ocirepository/sylva-core -o name \
       2> >(grep -v 'not found' >&2) || true \
    | xargs --no-run-if-empty kubectl delete -n sylva-units-preview
  kubectl delete namespace sylva-units-preview
}


function ci_remaining_minutes_and_at_most() {
  at_most=$1
  if [ -z ${CI_JOB_TIMEOUT:-} ]; then
    # we're not in a CI job
    echo ${at_most}m
  else
    # the value we return is the number of seconds of runtime left for this job
    # ... minus a safety margin to let debug-on-exit run
    # ... and we never return more than at_most seconds
    ci_job_started_at_epoch=$(date +%s --date=$CI_JOB_STARTED_AT)
    current_time_epoch=$(date +%s)
    debug_on_exit_max_duration_seconds=450

    # here we compute how much seconds are left before the CI job times out
    # (minus debug_on_exit_max_duration_seconds)
    ci_remaining_time=$((ci_job_started_at_epoch+CI_JOB_TIMEOUT-current_time_epoch-debug_on_exit_max_duration_seconds))
    ci_remaining_time=$((ci_remaining_time > 0 ? ci_remaining_time : 0))
    ci_remaining_min=$((ci_remaining_time/60))

    result=$((ci_remaining_min > at_most ? at_most : ci_remaining_min))m
    echo $result

    cat >&2 <<EOC
debug automatic computation of sylvactl --timeout (ci_remaining_minutes_and_at_most):
- at_most=$at_most
- CI_JOB_TIMEOUT=$CI_JOB_TIMEOUT
- ci_job_started_at_epoch=$ci_job_started_at_epoch
- current_time_epoch=$current_time_epoch
- debug_on_exit_max_duration_seconds=$debug_on_exit_max_duration_seconds
- ci_remaining_min=$ci_remaining_min
- result of timeout computation: $result
EOC
  fi
}

function display_service_ingresses() {
   kustomizations=$(kubectl --kubeconfig ./management-cluster-kubeconfig get kustomization -A -o yaml | yq '.items[] | select(.metadata.annotations."sylvactl/readyMessage" != null) | .metadata.name')
   for ks in $kustomizations; do
       message=$(kubectl --kubeconfig ./management-cluster-kubeconfig get kustomization $ks -o yaml | yq '.metadata.annotations."sylvactl/readyMessage"' )
       if [[ $message == *UI* ]]; then
           echo "* $ks - $message"
       fi
   done
}

function display_final_messages() {
  CALLER_SCRIPT_NAME=$(basename ${BASH_SOURCE[1]})
  if [[ $CALLER_SCRIPT_NAME != *"apply-workload-cluster.sh"* ]]; then
    echo_b "\U00002714 Sylva is ready, everything deployed in management cluster"
    echo "   Management cluster nodes:"
    kubectl --kubeconfig management-cluster-kubeconfig get nodes
  fi

  if [[ $CALLER_SCRIPT_NAME == *"bootstrap.sh"* ]]; then
    echo_b "\U0001F331 You can access following UIs"
    display_service_ingresses
  fi
  echo_b "\U0001F389 All done"
}
