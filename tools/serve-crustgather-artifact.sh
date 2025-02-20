#!/usr/bin/env bash

set -e

usage() {
    cat << EOF
Usage: $0 -p PROJECT_PATH -j JOB_ID [-u URI] -s SOCKET

Script to collect a Gitlab artifact with crust-gather content and serve it using your current kubeconfig.
Once started, you'll be able to explore cluster resources using kubectl from another shell.
You can also choose the target cluster (bootstrap/management/workload) by selecting the appropriate context:

kubectl --context workload get pods -A

-u, --uri           Full artifact URL for download. Will be parsed to owner/repo/artifact string. Required if -j is not specified.
-p, --project_path  Project ID. Defaults to 42451983
-j, --job_id        Job ID. Required.
-s, --socket        The socket address to bind the HTTP server to. Defaults to 127.0.0.1:9385
-b, --background    Start crust-gather in background and use a dedicated kubeconfig in a subshell to explore this artifact

\$GITLAB_TOKEN        For private projects, an access token with 'read_api' scope is to be provided through GITLAB_TOKEN variable.
EOF
    exit 1
}

while [[ $# -gt 0 ]]
do
    key="$1"
    case "${key}" in
        -u|--uri)
            URI="${2}"
            shift
            ;;
        -p|--project_id)
            PROJECT_ID="${2}"
            shift
            ;;
        -j|--job_id)
            JOB_ID="${2}"
            shift
            ;;
        -s|--socket)
            SOCKET="${2}"
            shift
            ;;
        -b|--background)
            BACKGROUND=1
            ;;
        *)
            # unknown option
            usage
            ;;
    esac
    shift
done

: ${PROJECT_ID:="42451983"}
: ${SOCKET:="127.0.0.1:$(( $RANDOM + 1024 ))"}

if [[ -z ${PROJECT_ID} ]] || [[ -z ${JOB_ID} ]] && [[ -z ${URI} ]]
then
    usage
    exit
fi

TOOLBOX_ENV=$(dirname ${BASH_SOURCE[0]})/../bin/env
if ! command -v crustgather &>/dev/null && [[ -f "$TOOLBOX_ENV" ]]; then
    source "$TOOLBOX_ENV"
fi

: ${URI:="https://gitlab.com/api/v4/projects/${PROJECT_ID}/jobs/${JOB_ID}/artifacts/crust-gather.tar.gz"}
echo "Downloading from $URI"

tmp=$(mktemp -d)
curl -H "PRIVATE-TOKEN: ${GITLAB_TOKEN}" -L "${URI}" --output "${tmp}/artifact.tar.gz"
tar -xzf "${tmp}/artifact.tar.gz" -C "${tmp}"

echo "Serving on ${SOCKET}..."

if [[ $BACKGROUND -eq 1 ]]; then
    export KUBECONFIG=$(mktemp)
    crustgather serve -a ${tmp} -s ${SOCKET} -v WARN &
    crustgather_pid=$!

    kubectl config use-context management && kubectl config set-context management --namespace sylva-system

    echo "Starting a new shell in crustgather context, hit ctlr+D to exit"
    JOB_PROMPT="crustgather-job-$JOB_ID ~> "
    if [[ $SHELL =~ .*bash$ && -f ~/.bashrc ]]; then
        $SHELL --rcfile <(cat ~/.bashrc; echo "PS1=\"$JOB_PROMPT\"")
    else
        $SHELL -c "export PS1=\"$JOB_PROMPT\"; exec $SHELL"
    fi

    while kill $crustgather_pid &>/dev/null; do
      sleep 1
    done
    rm $KUBECONFIG
else
    crustgather serve -a ${tmp} -s ${SOCKET} -v WARN
fi

rm -rf ${tmp}
