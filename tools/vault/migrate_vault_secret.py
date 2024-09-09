import os
import hvac


# read a secret in the Vault
def read_secret(vault, path):
    read_response = vault.secrets.kv.v2.read_secret(path)
    secret = read_response['data']['data']
    return secret


# Create a secret in the Vault
def write_secret(vault, secret_path, secret):
    vault.secrets.kv.create_or_update_secret(
        path=secret_path,
        secret=secret
    )


def delete_metadata_secret(vautl, secret_path):
    vautl.secrets.kv.v2.delete_metadata_and_all_versions(
        path=secret_path
    )


def migrate_secret(vault, old_secret_path, new_secret_path):
    # try:
    secret = read_secret(vault_client, old_secret_path)
    write_secret(vault, new_secret_path, secret)
    # migrated_secret = read_secret(vault_client, new_secret_path)
    # if migrated_secret == secret:
    # delete_metadata_secret(vault,old_secret_path)
    # else:
    # print(f"Some error occurred in migrate secret from {old_secret_path} to {new_secret_path}")
    # except Exception as e:
    #    print("Some error occurred in migrating secret", e)


def list_secrets(client, path=None):
    list_response = client.secrets.kv.v2.list_secrets(
        path=path
    )

    return list_response


def list_all_secrets(client, global_path_list, path=None, recursive=False):
    if path is None:
        try:
            response = list_secrets(client)
        except hvac.exceptions.VaultError:
            return
    else:
        response = list_secrets(client,  path=path)

    keys = response['data']['keys']

    for key in keys:
        if key[-1] == "/":
            if recursive:
                if path is not None:
                    _path = path + key
                else:
                    _path = key
                list_all_secrets(client, global_path_list,  path=_path, recursive=recursive)
            else:
                continue
        else:
            _temp = path + key

            if _temp is None:
                pass
            else:
                global_path_list.append(_temp)

    return global_path_list


vault_token = os.getenv("VAULT_API_TOKEN")
vault_url = os.getenv("VAULT_URL")
vault_url = f"https://{vault_url}/"
new_path = os.getenv("NEW_PATH")
# we rename secret to force flux to recreate the secret
# path is immutable field and as the error message from
# vault config operator didn't include immutable word
# it can't be managed by flux force property
# https://github.com/fluxcd/pkg/blob/30c101fc7c9fac4d84937ff4890a3da46a9db2dd/ssa/errors/immutable.go#L27-L28
new_secret_suffix = "-passwd"

if new_path is None:
    raise ValueError('missing required NEW_PATH env variable')

# vault_client
vault_client = hvac.Client(url=vault_url, verify=False, token=vault_token)

global_path_list = []

secrets_list = list_all_secrets(vault_client, global_path_list, '/')

for secret_path in secrets_list:
    secret = read_secret(vault_client, secret_path)
    new_secret_path = new_path + secret_path + new_secret_suffix
    migrate_secret(vault_client, secret_path, new_secret_path)
