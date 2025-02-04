#!/usr/bin/env python3
import base64
from keycloak import KeycloakAdmin
import requests
import urllib3
import logging
from kubernetes import client, config
from kubernetes.client import CoreV1Api


# supress ssl warning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(funcName)s: %(message)s')

# Configure Kubernetes client
config.load_incluster_config()
api_instance = client.CustomObjectsApi()
core_v1_api = CoreV1Api()
v1 = client.CoreV1Api()

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


KEYCLOAK_BASE_URL = "https://keycloak-service.keycloak.svc.cluster.local:8443"
CONFIGMAP_NAMESPACE = "sylva-system"
CONFIGMAP_NAME = "keycloak-uuid-resources"
KEYCLOAK_USERNAME = "admin"
KEYCLOAK_CLIENT_ID = "admin-cli"
KEYCLOAK_REALM_NAME = "sylva"
VERIFY_SSL = False


# Retrieve Keycloak admin initial password
def get_initial_password():
    logging.info("Getting Keycloak initial password...")
    secret = v1.read_namespaced_secret(name="keycloak-initial-admin", namespace=CONFIGMAP_NAMESPACE)
    password_encoded = secret.data['password']
    password = base64.b64decode(password_encoded).decode('utf-8')
    return password


KEYCLOAK_PASSWORD = get_initial_password()


# retrieve access token
def get_access_token():
    logging.info("Get Keycloak access token...")
    url = f"{KEYCLOAK_BASE_URL}/realms/master/protocol/openid-connect/token"
    data = {
        "username": KEYCLOAK_USERNAME,
        "password": KEYCLOAK_PASSWORD,
        "grant_type": "password",
        "client_id": KEYCLOAK_CLIENT_ID
    }
    response = requests.post(url, data=data, verify=VERIFY_SSL)
    token = response.json()
    if response.status_code != 200:
        logging.error("Failed to retrieve access token")
        raise

    if not token:
        logging.error("ACCESS_TOKEN is set to the empty string")
        raise

    return token


keycloak_access_tk = get_access_token()  # gitleaks:allow


# Initialize Keycloak Admin client
keycloak_admin = KeycloakAdmin(
    server_url=KEYCLOAK_BASE_URL,
    realm_name=KEYCLOAK_REALM_NAME,
    client_id=KEYCLOAK_CLIENT_ID,
    token=keycloak_access_tk,  # gitleaks:allow
    verify=VERIFY_SSL
)


def get_client_and_mappers_uuids():
    logging.info("Getting KeycloakClients uuids...")
    client_uuids = {}
    protocol_mappers_uuids = {}
    all_clients = keycloak_admin.get_clients()
    for kclient in all_clients:
        if kclient.get('secret'):
            client_uuids.update({f"CLIENT_{kclient['clientId'].replace('-', '_').upper()}": kclient['id']})
            for mapper in kclient['protocolMappers']:
                protocol_mappers_uuids.update(
                    {f"MAPPER_{mapper['name'].replace(' ', '_').upper()}_{kclient['clientId'].replace('-', '_').upper()}": mapper['id']}
                )
    return {**client_uuids, **protocol_mappers_uuids}


def get_groups_ids():
    logging.info("Getting KeycloakGroups uuids...")
    group_uuids = {}

    groups = keycloak_admin.get_groups()
    for group in groups:
        group_uuids.update({f"GROUPS_{group['name'].replace('-', '_').upper()}": group['id']})
    return group_uuids


def get_user_ids():
    logging.info("Getting KeycloakUsers uuids...")
    user_uuids = {}

    users = keycloak_admin.get_users({})
    for user in users:
        user_uuids.update({f"USER_{user['username'].replace('-', '_').upper()}": user['id']})
    return user_uuids


def get_realm_roles():
    logging.info("Getting KeycloakRealmRoles uuids...")
    realm_uuids = {}
    realm_roles = keycloak_admin.get_realm_roles()
    for role in realm_roles:
        realm_uuids.update({f"REALM_ROLE_{role['name'].replace('-', '_').upper()}": role['id']})
    return realm_uuids


def get_client_scopes():
    logging.info("Getting KeycloakClientScopes uuids...")
    client_scope_uuids = {}
    client_scopes = keycloak_admin.get_client_scopes()
    client_scope_uuids.update({f"CLIENT_SCOPE_{x['name'].replace('-', '_').upper()}": x['id'] for x in client_scopes if x['name'] == 'groups'})
    return client_scope_uuids


def create_k8s_configmap(uuid_data):
    config_map = client.V1ConfigMap(
        metadata=client.V1ObjectMeta(
            name=CONFIGMAP_NAME,
            namespace=CONFIGMAP_NAMESPACE),
        data=uuid_data
    )
    try:
        logging.info("Creating configmap...")
        v1.create_namespaced_config_map(namespace=CONFIGMAP_NAMESPACE, body=config_map)
        logging.info(f"ConfigMap {CONFIGMAP_NAME} created successfully.")
    except client.exceptions.ApiException as e:
        if e.status == 409:   # if configmap exists, update it.
            logging.info(f"Configmap {CONFIGMAP_NAME} already exists, will update it...")
            v1.replace_namespaced_config_map(name=CONFIGMAP_NAME, namespace=CONFIGMAP_NAMESPACE, body=config_map)
            logging.info("ConfigMap updated successfully.")
        else:
            logging.error(f"An error occurred: {e}")


realms = keycloak_admin.get_realms()


if len(realms) == 1 and realms[0]['realm'] == 'master':
    logging.info("This is a fresh install with only the master realm.")
else:
    logging.info("This Keycloak instance has additional realms, proceeding to get resource UUIDS")
    client_uuids = get_client_and_mappers_uuids()
    group_uuids = get_groups_ids()
    user_uuids = get_user_ids()
    realm_roles_uuids = get_realm_roles()
    client_scope_uuids = get_client_scopes()

    result_uuids = {**client_uuids, **group_uuids, **user_uuids, **realm_roles_uuids, **client_scope_uuids}
    create_k8s_configmap(result_uuids)
