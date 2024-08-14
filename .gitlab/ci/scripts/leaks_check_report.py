#!/usr/bin/env python3

import os
import re
import urllib
import base64
import sys
import urllib3
import hvac
from kubernetes import client, config

urllib3.disable_warnings(category=urllib3.exceptions.InsecureRequestWarning)
# Script to build a single regex from all kubernetes and vault secret and use
# it to dectect leak on the pods logs

# white list of secrets to ignore
whitelist_secret = {
  "keycloak-initial-admin": ["username"],
  "keycloak-db-secret": ["username"],
  "keycloak-client-secret-vault-client": ["CLIENT_ID"],
  "keycloak-client-secret-rancher-client": ["CLIENT_ID"],
  "keycloak-client-secret-harbor-client": ["CLIENT_ID"],
  "keycloak-client-secret-grafana-client": ["CLIENT_ID"],
  "keycloak-client-secret-flux-webui-client": ["CLIENT_ID"],
  "credential-sylva-sylva-admin-keycloak": ["username"],
  "credential-external-keycloak": ["ADMIN_USERNAME"],
  "oidc-auth": ["redirectURL", "issuerURL", "clientID"],
  "cluster-user-auth": ["username"],
  "cluster-creator-kubeconfig": ["USER_NAME"],
  "local-kubeconfig": ["apiServerURL"],
  "fleet-agent": ["deploymentNamespace", "clusterNamespace", "clusterName"],
  "thanos-minio-root":  ["MINIO_ROOT_USER"],
  "loki-minio-user": ["CONSOLE_ACCESS_KEY"],
  "minio-monitoring-user": ["CONSOLE_ACCESS_KEY"],
  "chart-values-metallb": ["ca-file.pem"],
  # https://gitlab.com/sylva-projects/sylva-core/-/issues/1451
  # for password key
  "sso-account": ["login", "password"],
  "extra-ca-certs": ["extra-ca-certs.pem"],
  # https://gitlab.com/sylva-projects/sylva-core/-/issues/1335
  # for password key
  "thanos-basic-auth": ["username", "password"],
  # https://gitlab.com/sylva-projects/sylva-core/-/issues/1334
  # for admin-password key
  "rancher-monitoring-grafana": ["admin-user", "admin-password"]
}

whitelist_secret_without_suffix = {
  # https://gitlab.com/sylva-projects/sylva-core/-/issues/1479
  # for ADMIN_PASSWORD key
  "kustomization-unit-substitute-vault": ["ADMIN_PASSWORD"],
  # https://gitlab.com/sylva-projects/sylva-core/-/issues/1480
  # for SSO_PASSWORD key
  "kustomization-unit-substitute-keycloak-resources": ["SSO_PASSWORD"]
}

whitelist_key = [
    "systemNamespace",
    "deploymentNamespace",
    "clusterNamespace",
    "clusterName",
    "namespace",
    "format"
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


# check if secret is in white list and be safely ignore
def is_whitelist_secret(secret_name, key):
    if secret_name in whitelist_secret:
        if key in whitelist_secret[secret_name]:
            return True  # secret in white list skip
    if key in whitelist_key:
        return True  # key in white lsit skip
    # remove suffix of secret like my-secret-xxxxxxx
    secret_without_suffix = re.sub('-[A-Za-z0-9]{7}$', '', secret_name)
    if secret_without_suffix in whitelist_secret_without_suffix:
        if key in whitelist_secret_without_suffix[secret_without_suffix]:
            return True  # secret in white list skip
    return False


# build secret regex
def build_secret_regex(secrets_dict, secret_list, secret_id_list, encoded):
    for secret_name in secrets_dict:
        if secrets_dict[secret_name]:
            for key in secrets_dict[secret_name]:
                if is_whitelist_secret(secret_name, key):
                    continue  # secret in white list skip
                value_secret = secrets_dict[secret_name][key]
                if encoded:
                    value_secret = base64.b64decode(value_secret)
                    try:
                        value_secret = value_secret.decode('utf-8')
                    except:
                        continue
                if value_secret:
                    value_secret = value_secret.strip()
                    value_secret_re = value_secret
                    # escape special characteres
                    value_secret_re = ".{1,2}".join(value_secret_re.split(r"\."))
                    value_secret_re = re.sub("[']",  ".", value_secret_re)
                    value_secret_re = re.sub(r"[.|*+/()?\[\]$^]", ".", value_secret_re)
                    value_secret_re = ".{1,2}".join(value_secret_re.split(r"\n"))
                    value_secret_re = ".{1,2}".join(value_secret_re.split(r"\x"))
                    value_secret_re = ".{1,2}".join(value_secret_re.split(r"\\"))
                    value_secret_re = ".".join(value_secret_re.split("\\"))
                    secret_list.append(value_secret_re)
                    secret_id_list[value_secret_re] = {"secret": secret,
                                                       "key": key}


def validate_secret_regex(secrets_dict, secrets_regex, encoded):
    for secret_name in secrets_dict:
        if secrets_dict[secret_name]:
            for key in secrets_dict[secret_name]:
                if is_whitelist_secret(secret_name, key):
                    continue  # secret in white list skip
                value_secret = secrets_dict[secret_name][key]
                if encoded:
                    value_secret = base64.b64decode(value_secret)
                    try:
                        value_secret = value_secret.decode('utf-8')
                    except:
                        continue
                if value_secret:
                    log_leak = re.findall(secrets_regex, value_secret)
                    if not log_leak:
                        print(f"ERROR : secret {secret_name} does not match regex")
                        sys.exit(1)


def check_leaks(log_string, leaks_output, target_pod, secrets_regex, secret_id_list):
    log_string = f"{log_string}"
    log_string = log_string.rstrip('\r')
    for leak_found in re.finditer(secrets_regex, log_string):
        if leak_found.group() in secret_id_list:
            leaks_output.append({"pod": target_pod.metadata.name,
                                 "namespace": target_pod.metadata.namespace,
                                 "leak": secret_id_list[leak_found.group()],
                                 "log": log_string[leak_found.start()-20:leak_found.end()+20]})
        else:
            leaks_output.append({"pod": target_pod.metadata.name,
                                 "namespace": target_pod.metadata.namespace,
                                 "log": log_string[leak_found.start()-20:leak_found.end()+20]})

# get kubernetes secrets
secrets = v1.list_secret_for_all_namespaces(watch=False).items
kubernetes_secrets = {}
secret_lst = []
for secret in secrets:
    kubernetes_secrets[secret.metadata.name] = secret.data

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
    read_response = vault_client.secrets.kv.v2.read_secret(
          path=path,
    )
    vault_secrets[folder] = read_response['data']['data']

# get list of all pods
pods = v1.list_pod_for_all_namespaces(watch=False).items

leaks = []

secret_id_lst = {}
# build kubernetes secret regex
build_secret_regex(kubernetes_secrets, secret_lst, secret_id_lst, True)
# build vault secret regex
build_secret_regex(vault_secrets, secret_lst, secret_id_lst, False)

secrets_re = ""
secrets_re = r"(?=("+'|'.join(secret_lst)+r"))"

check_leaks
# validate the regex on all vault secret
validate_secret_regex(vault_secrets, secrets_re, False)

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

