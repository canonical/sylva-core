GET https://{{vault_url}}/v1/secret/data/{{cluster_name}}/keycloak-passwd
X-Vault-Token: {{token}}
HTTP 200
[Captures]
password_keycloak: jsonpath "$.data.data.password"

POST https://{{keycloak_url}}/realms/master/protocol/openid-connect/token
Content-Type: application/x-www-form-urlencoded
[FormParams]
username: admin
password: {{password_keycloak}}
grant_type: password
client_id: admin-cli
HTTP 200

