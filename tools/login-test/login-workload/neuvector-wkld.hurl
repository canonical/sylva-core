POST https://{{neuvector_url}}/auth
{"isRancherSSOUrl":false,
"username":"admin",
"password":"{{password_neuvector}}"}
HTTP 200
[Captures]
token_neuvector: jsonpath "$.token.token"

GET https://{{neuvector_url}}/fed/member
Content-Type: application/json
Token: {{token_neuvector}}
HTTP 200
[Asserts]
jsonpath "$.fed_role" == "joint"
