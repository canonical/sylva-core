#!/bin/bash

set -e
set -o pipefail

PEM_FILE=cabundle.pem

truststore() {
	echo "-- Add Sylva CA and external certificates to CA bundle file"
        kubectl get -n keycloak secret sylva-ca.crt -o yaml | yq '.data."ca.crt"' | base64 -d >> /tmp/$PEM_FILE

	echo "-- Generate truststore file"

        # number of certs in the PEM file
        CERTS=$(grep 'END CERTIFICATE' /tmp/$PEM_FILE| wc -l)

        # For every cert in the PEM file, extract it and import into the JKS keystore
        # awk command: step 1, if line is in the desired cert, print the line
        #              step 2, increment counter when last line of cert is found
       for N in $(seq 0 $(($CERTS - 1))); do
         ALIAS="${PEM_FILE%.*}-$N"
         cat /tmp/$PEM_FILE | \
         awk "n==$N { print }; /END CERTIFICATE/ { n++ }" | \
         keytool -noprompt -import -trustcacerts -alias $ALIAS -keystore /tmp/keycloak-truststore.jks -storepass changeit
       done

       echo "-- Create truststore ConfigMap"

       kubectl create configmap keycloak-truststore --from-file=/tmp/keycloak-truststore.jks -n keycloak

}

echo "-- Check if truststore ConfigMap already exist"

if kubectl -n keycloak get cm/keycloak-truststore 
then
   echo "-- ConfigMap keycloak-truststore exist"
   echo "-- Check if new certificates has been added"
   md=$(kubectl get -n keycloak secret sylva-ca.crt -o yaml | yq '.data."ca.crt"' | base64 -d | md5sum |cut -f1 -d " ")
   actual_md=$(kubectl -n keycloak get cm/keycloak-truststore -o yaml | yq '.metadata.labels.cert')
   if [ $md == $actual_md ]
   then
     echo "-- No new certificate"
   else
     kubectl -n keycloak delete cm/keycloak-truststore
     truststore
     kubectl -n keycloak label cm/keycloak-truststore cert=$md
   fi 
else
   md=$(kubectl get -n keycloak secret sylva-ca.crt -o yaml | yq '.data."ca.crt"' | base64 -d | md5sum |cut -f1 -d " ")
   truststore
   kubectl -n keycloak label cm/keycloak-truststore cert=$md
fi

echo "-- All done"
