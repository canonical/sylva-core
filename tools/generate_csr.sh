#!/bin/bash

if [[ $# -ne 1 || $1 == "--help" ]]; then
  echo "Usage: ./generate_csr.sh <domain name>"
  echo
  echo "This script generates keys and csr (Certificate Signing Requests) for all the exposed services of a sylva management cluster"
  echo "The domain name should be the same as the 'cluster_domain' in the deployment values ('sylva' by default)"
  echo "The output is a set of files '<service>.<domain name>.key' and '<service>.<domain name>.csr'"
  echo
  echo "The following environment variables can be set to configure the subject of the certificates:"
  echo "EMAIL (email@domain by default)"
  echo "ORGANISATION (SYLVA by default)"
  echo "ORGANISATIONAL_UNIT (DEV by default)"
  echo "COUNTRY (FR by default)"
  exit
fi

DOMAIN=$1
# EMAIL=email@domain        # CHANGE_ME
# ORGANISATION=SYLVA        # CHANGE_ME
# ORGANISATIONAL_UNIT=DEV   # CHANGE_ME
# COUNTRY=FR                # CHANGE_ME

SERVICES="rancher keycloak vault flux neuvector harbor gitea kubevirt-manager"

for BASE_NAME in $SERVICES; do
  echo =========
  echo $BASE_NAME

  CN=${BASE_NAME}.${DOMAIN}
  echo CN=$CN
  echo generate key
  openssl genrsa -out $CN.key 4096

  cat > $CN.conf << EOF
[ req ]
prompt = no
distinguished_name = dn
req_extensions = req_ext

[ dn ]
CN = ${CN}
emailAddress = ${EMAIL:-email@domain}
O = ${ORGANISATION:-SYLVA}                 # CHANGE_ME
OU = ${ORGANISATIONAL_UNIT:-DEV}                  # CHANGE_ME
C = ${COUNTRY:-FR}                    # CHANGE_ME

[ req_ext ]
subjectAltName =  DNS:${CN}
EOF
  echo create CSR
  openssl req -new -config $CN.conf -key $CN.key -out $CN.csr
  rm $CN.conf

done
