GET https://{{vault_url}}/v1/secret/data/{{cluster_name}}/neuvector-passwd
X-Vault-Token: {{token}}
HTTP 200
[Captures]
password_neuvector: jsonpath "$.data.data.password"

POST https://{{neuvector_url}}/auth
{"isRancherSSOUrl":false,
"username":"admin",
"password":"{{password_neuvector}}"}
HTTP 200

