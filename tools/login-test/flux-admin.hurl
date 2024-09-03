GET https://{{vault_url}}/v1/secret/data/{{cluster_name}}/flux-webui
X-Vault-Token: {{token}}
HTTP 200
[Captures]
password_flux: jsonpath "$.data.data.password"

POST https://{{flux_url}}/oauth2/sign_in
{"username": "admin",
"password": "{{password_flux}}"}
HTTP 200
