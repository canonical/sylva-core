#!/usr/bin/env python3
# The aim of this script is to detect leaks of sensitive information from Kubernetes
# and Vault Secrets in the pods logs.
#
# The script is building a single regex from all kubernetes and vault secrets.
#
# The "whitelisted secrets" (`whitelist_secret` and `whitelist_secret_without_prefix_and_suffix` lists below)
# are the Secret to be ignored (more specifically combination of Secret and key inside the Secret).
#
# The whitelisted secrets are either:
# - information that is not sensitive, such as the username in a Secret containing a user/password pair
#   having them in the logs is not an issue
# - sensitive information for which a leak has been detected and an
#   issue already created to track and fix it.
#
# To detect leaks, the script tries to find all matches of the secret in the logs
# of every pods currently running on the platform against which the script is being run.

import os
import re
import base64
import warnings
import sys
import urllib3
import hvac
from kubernetes import client, config

urllib3.disable_warnings(category=urllib3.exceptions.InsecureRequestWarning)


# white list of secrets to ignore
whitelist_secret = {
    # https://gitlab.com/sylva-projects/sylva-core/-/issues/1480
    # for password key
    "credential-sylva-sylva-admin-keycloak": ["password"],
    # https://gitlab.com/sylva-projects/sylva-core/-/issues/1451
    # for password key
    "sso-account": ["login", "password"],
    # https://gitlab.com/sylva-projects/sylva-core/-/issues/1335
    # for password key
    "thanos-basic-auth": ["password"],
    # https://gitlab.com/sylva-projects/sylva-core/-/issues/1334
    # for admin-password key
    "rancher-monitoring-grafana": ["admin-password"],
    # https://gitlab.com/sylva-projects/sylva-core/-/issues/1332
    # for REGISTRY_CREDENTIAL_PASSWORD key
    "harbor-jobservice": ["REGISTRY_CREDENTIAL_PASSWORD"],
    # https://gitlab.com/sylva-projects/sylva-core/-/issues/1332
    # for secretKey and REGISTRY_CREDENTIAL_PASSWORD keys
    "harbor-core": ["secretKey", "REGISTRY_CREDENTIAL_PASSWORD"],
    # https://gitlab.com/sylva-projects/sylva-core/-/issues/1609
    "ironic-inspector-basic-auth": ["htpasswd"],
    # https://gitlab.com/sylva-projects/sylva-core/-/issues/1609
    "ironic-basic-auth": ["htpasswd"],
    # https://gitlab.com/sylva-projects/sylva-core/-/issues/1609
    "ironic-mariadb": ["password"],
    # https://gitlab.com/sylva-projects/sylva-core/-/issues/1652
    "csi-cephfs-secret": ["adminKey"],
    # these are the clientId of the gitea oidc client
    # which aren't security sensitve
    "gitea-keycloak-oidc-auth": ["key"],
    # this is the gitea script to setup environment
    # which is not sensitive as it contains no sensitive data
    "gitea": ["config_environment.sh"],
    # https://gitlab.com/sylva-projects/sylva-core/-/issues/1665
    "gitea-postgres-replication": ["password"],
    "cnpg-keycloak-app": ["user", "port", "host", "dbname"],
}

whitelist_secret_without_prefix_and_suffix = {
    # https://gitlab.com/sylva-projects/sylva-core/-/issues/1479
    # for ADMIN_PASSWORD key
    "kustomization-unit-substitute-vault": ["ADMIN_PASSWORD"],
    # https://gitlab.com/sylva-projects/sylva-core/-/issues/1480
    # for SSO_PASSWORD key
    "kustomization-unit-substitute-keycloak-resources": ["SSO_PASSWORD"],
    # https://gitlab.com/sylva-projects/sylva-core/-/issues/1609
    "rke2-capm3-virt-management-md": ["password"],
    # https://gitlab.com/sylva-projects/sylva-core/-/issues/1609
    "rke2-capm3-virt-management-cp": ["password"],
    # https://gitlab.com/sylva-projects/sylva-core/-/issues/1609
    "kubeadm-capm3-virt-management-md": ["password"],
    # https://gitlab.com/sylva-projects/sylva-core/-/issues/1609
    "kubeadm-capm3-virt-management-cp": ["password"],
    # https://gitlab.com/sylva-projects/sylva-core/-/issues/1609
    "rke2-capm3-virt-workload": ["password"],
    # https://gitlab.com/sylva-projects/sylva-core/-/issues/1609
    "kubeadm-capm3-virt-workload": ["password"],
    # https://gitlab.com/sylva-projects/sylva-core/-/issues/1610
    "rke2-capm3-virt-token": ["value"],
    "bootstrap-token": [
        # usage-bootstrap-signing and usage-bootstrap-authentication
        # are boolean which indicates that the token should be used
        # or not to sign the cluster-info ConfigMap or ahtnenticate.
        # not sensitive
        "usage-bootstrap-signing",
        "usage-bootstrap-authentication",
        # token_id is sensitive data and tracked on following issue:
        # https://gitlab.com/sylva-projects/sylva-core/-/issues/1709
        "token-id",
    ],
    # this is some rancher webhook setup, not sensitive
    "helm-operation": ["values-rancher-webhook-104.0.2-up0.5.2.yaml"],
}

whitelist_key = [
    "systemNamespace",
    "deploymentNamespace",
    "clusterNamespace",
    "clusterName",
    "namespace",
    "format",
    "ca.crt",
    "tls.crt",
    "extra-ca-certs.pem",
    "ca-file.pem",
    "username",
    # these are ID of the keycloak clients, which aren't security sensitve
    "CLIENT_ID",
    # these are ID of the OIDC-auth, which aren't security sensitve
    "clientID",
    # these are the csi-cephfs admin ID, which aren't security sensitve
    "adminID",
    # these are ADMIN keyclock username, which aren't security sensitve (the ADMIN_PASSWORD is sentitive)
    "ADMIN_USERNAME",
    "USER_NAME",
    "admin-user",  # these are  grafana admin user, which aren't security sensitve
    # these are minio S3 access keys, which aren't security sensitve
    #  (the "secret access keys", found in CONSOLE_SECRET_KEY are sensitive)
    "CONSOLE_ACCESS_KEY",
    # these are  redirect URL use for OIDC Auth, which aren't security sensitve
    "redirectURL",
    # these are  issuer URL use for OIDC Auth, which aren't security sensitve
    "issuerURL",
    "apiServerURL",
    "MINIO_ROOT_USER",
    # these are loki username, which aren't security sensitve
    "LOKI_USERNAME",
]

ci_project_dir = os.getenv("CI_PROJECT_DIR", ".")

REPORT_FILE = f"{ci_project_dir}/leak-report.log"

# load kubeconfig
config.load_kube_config()
# kubernetes_client
v1 = client.CoreV1Api()
vault_token = os.getenv("VAULT_API_TOKEN")
vault_url = os.getenv("VAULT_URL")
vault_url = f"https://{vault_url}"


def is_valid_secret(value_secret):
    """
    is_valid_secret checks if value_secret should be skipped
    the function will return true if value secret is equal
    to an empty dictionnary JSON representation ("{}")
    :value_secret
    """
    return value_secret and not (value_secret == "{}")


# check if secret is in white list and be safely ignore
def is_whitelist_secret(secret_name, key):
    """
    is_whitelist_secret checks if the data found in the specified Secret in this `key` are in the whitelist
    :secret_name
    :key
    """
    if secret_name in whitelist_secret:
        if key in whitelist_secret[secret_name]:
            return True  # secret in white list skip
    if key in whitelist_key:
        return True  # key in white lsit skip
    # check for secret with contextual prefix and/or suffix
    #  like yyyyyy-my-secret-xxxxxxx
    for secret in whitelist_secret_without_prefix_and_suffix:
        if secret in secret_name:
            if key in whitelist_secret_without_prefix_and_suffix[secret]:
                return True
    return False


# unitary validate a secret with its regex
def validate_secret_regex(value_secret, secret_regex, secret_name, key):
    """
    validate_secret_regex validates a secret on its regex

    if the secret doesn't match the regex, this function forces a script exit

    :value_secret the value of the secret from which the secret_regx has been built
    :secret_regex the secret_regex built from the value_secret
    :secret_name the name of the secret
    :key the key of the secret use to generate the regex
    """
    log_leak = re.findall(secret_regex, value_secret)
    if not log_leak:
        print(f"""ERROR: the regex computed by this tool for {secret_name} key {key}
               should have matched the secret, but did not""")
        print(secret_regex)
        print(value_secret)
        sys.exit(1)


# build secret regex
def build_secret_regex(secrets_dict, secret_list, secret_id_list):
    """
    build_secret_regex builds a regex that will match all secrets from secrets_dict.
    the result is produced by enriching secret_list and secret_id_list
    :secrets_dict dictionnary, containing all secrets from kubernetes or vault
                  keys are names of secret
                  values are dicts with the Secret content (keys are Secret keys,
                  e.g. "password", values are the stored information)
    :secret_list list of regex, one for each secret value to match
    :secret_id_list dictionary, "reverse" map to get secret name and key from the secret value
                    (keys are the secret values, values are dicts with `secret` (secret name)
                    and `key` (key inside secret)
    """
    for secret_name in secrets_dict:
        if secrets_dict[secret_name]:
            for key in secrets_dict[secret_name]:
                if is_whitelist_secret(secret_name, key):
                    continue  # secret in white list skip
                value_secret = secrets_dict[secret_name][key]
                if is_valid_secret(value_secret):
                    # removes any leading, and trailing whitespaces from the secret value
                    value_secret = value_secret.strip()
                    value_secret_re = value_secret
                    # escape special characteres
                    # replace any non alphanumeric character by a "."
                    value_secret_re = re.sub(r"['.|*+/()?\[\]$^]", ".", value_secret_re)
                    # escape "\x" used to denotate hexa bytes by a "."
                    value_secret_re = re.sub(r"\\x", ".{1,2}", value_secret_re)
                    # escape remaining "\" charactere by a "."
                    value_secret_re = re.sub(r"\\", ".{1,2}", value_secret_re)
                    validate_secret_regex(value_secret, value_secret_re, secret_name, key)
                    secret_list.append(value_secret_re)
                    secret_id_list[value_secret] = {"secret": secret_name,
                                                    "key": key}


# validate secrets regex by matching every secret on it
def validate_secret_list_regex(secrets_dict, secrets_regex):
    """
    validate_secret_list_regex validates the secret regex by testing it on every secret

    if one of the secret doesn't match the regex, this function forces a script exit

    :secrets_dict dictionary containing secrets from kubernetes or vault (same format as for build_secret_regex)
    :secrets_regex the secret_regex built from all secrets
    """
    for secret_name in secrets_dict:
        if secrets_dict[secret_name]:
            for key in secrets_dict[secret_name]:
                if is_whitelist_secret(secret_name, key):
                    continue  # secret in white list skip
                value_secret = secrets_dict[secret_name][key]
                if is_valid_secret(value_secret):
                    validate_secret_regex(value_secret, secrets_regex, secret_name, key)


# check  leak_checked is not present in the leaks_output
def is_new_leak(leak_checked, leaks_output):
    """
    is_new_leak validates the leak detected has not already be added in leaks_output to avoid duplicate
    in the report
    return True if it is a new leak False otherwise

    :leak_checked the leakce check if it is a new one or not
    :leaks_output The list of leak already tracked for report
    """
    for leak in leaks_output:
        if leak_checked == leak:
            return False
    return True


# check  secret regex by matching every secret on it
def check_leaks(log_string, leaks_output, target_pod, secrets_regex, secret_id_list):
    """
    check_leaks tries to find matches of secret_regex in the given log_string

    for each match found (i.e. each leak), the leaks_output list is enriched
    with information about the leak (using target_pod information and secret_id_list)

    :log_string string containing the full logs of a pod
    :leaks_output list of all leaks detected (the function appends to this list)
    :target_pod (dict) Pod object, from which logs are being checked
    :secrets_regex the secret_regex built from all secrets
    :secret_id_list dictionary, "reverse" map to get secret name and key from the secret value
                    (keys are the secret values, values are dicts with `secret` (secret name)
                    and `key` (key inside secret)
    """
    log_string = f"{log_string}"
    log_string = log_string.rstrip('\r')
    for leak_found in re.findall(secrets_regex, log_string):
        leak_found = leak_found.strip()
        if leak_found in secret_id_list:
            leak = {"pod": target_pod.metadata.name,
                    "namespace": target_pod.metadata.namespace,
                    "leak": secret_id_list[leak_found],
                    "secret": leak_found}
        else:
            leak = {"pod": target_pod.metadata.name,
                    "namespace": target_pod.metadata.namespace,
                    "leak_found": leak_found}
        if is_new_leak(leak, leaks_output):
            leaks_output.append(leak)


# get kubernetes secrets
secrets = v1.list_secret_for_all_namespaces(watch=False).items
kubernetes_secrets = {}

for secret in secrets:
    kubernetes_secrets[secret.metadata.name] = {}
    if is_valid_secret(secret.data):
        for key in secret.data:
            decoded_secret = base64.b64decode(secret.data[key])
            # check if secret value is not a gzipped file (byte array beggining by 0x1F8B)
            if not (len(decoded_secret) >= 2 and decoded_secret[0] == 31 and decoded_secret[1] == 139):
                kubernetes_secrets[secret.metadata.name][key] = decoded_secret.decode("utf-8")
            else:
                warnings.warn(f"""WARNING: secret {secret.metadata.name} key {key}
                               was skipped, as it has been identified as gzip file content""")

# vault_client
vault_client = hvac.Client(url=vault_url, verify=False, token=vault_token)

# get vault secrets
list_response = vault_client.secrets.kv.v2.list_secrets(
    path='/'
)
vault_secrets = {}

list_folders = list_response['data']['keys']
for folder in list_folders:
    path = f"/{folder}"
    read_response = vault_client.secrets.kv.v2.read_secret(path=path,)
    vault_secrets[folder] = read_response['data']['data']

# get list of all pods
pods = v1.list_pod_for_all_namespaces(watch=False).items

leaks = []

secret_lst = []
secret_id_lst = {}
# build kubernetes secret regex
build_secret_regex(kubernetes_secrets, secret_lst, secret_id_lst)
# build vault secret regex
build_secret_regex(vault_secrets, secret_lst, secret_id_lst)

secrets_re = ""
# build secrets regex from list of individual secret regex
secrets_re = r"("+'|'.join(secret_lst) + r")" # noqa E226

# validate the regex on all kubernetes secret
validate_secret_list_regex(kubernetes_secrets, secrets_re)
# validate the regex on all vault secret
validate_secret_list_regex(vault_secrets, secrets_re)

# check for leak on pods logs
for pod in pods:
    for container in pod.spec.containers:
        try:
            # get logs of current container logs
            log = v1.read_namespaced_pod_log(name=pod.metadata.name,
                                             namespace=pod.metadata.namespace,
                                             container=container.name)
            check_leaks(log, leaks, pod, secrets_re, secret_id_lst)
            # check logs of previous terminated container logs
            previous_log = v1.read_namespaced_pod_log(name=pod.metadata.name,
                                                      namespace=pod.metadata.namespace,
                                                      container=container.name,
                                                      previous=True)
            check_leaks(previous_log, leaks, pod, secrets_re, secret_id_lst)
        except client.exceptions.ApiException as err:
            # ignore 400 and 404 error due to previous terminated container
            # in pod  not found as terminated container logs cannot be read"
            regex = "(.*previous terminated container.*in pod.*not found)"
            if err.status == 404 or (err.status == 400 and err.body and re.match(regex, err.body)):
                pass
            else:
                raise

if len(leaks) > 0:
    print("Some leaks were found, please take a look the job artifacts")
    with open(REPORT_FILE, "w", encoding="utf-8") as report_fd:
        for leak in leaks:
            print(leak, file=report_fd)
    sys.exit(1)
else:
    print("[OK] No leak found")
