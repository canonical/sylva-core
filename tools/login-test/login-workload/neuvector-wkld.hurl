POST https://{{neuvector_url}}/auth
{"isRancherSSOUrl":false,
"username":"admin",
"password":"{{password_neuvector}}"}
HTTP 200
[Captures]
token_neuvector: jsonpath "$.token.token"
