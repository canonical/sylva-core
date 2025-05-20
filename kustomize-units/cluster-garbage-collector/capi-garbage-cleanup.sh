#!/bin/bash

set -ue
set -o pipefail

# the '.*' below is here to ensure a match in `kubectl api-resources | grep ...`
# we use fully-qualified kinds to avoid unfortunate collisions with Rancher CRDs
TEMPLATE_TYPES_CR="
KubeadmConfigTemplate.*bootstrap.cluster.x-k8s.io
RKE2ConfigTemplate.*bootstrap.cluster.x-k8s.io
OpenshiftAssistedConfigTemplate.*bootstrap.cluster.x-k8s.io
DockerMachineTemplate.*infrastructure.cluster.x-k8s.io
VSphereMachineTemplate.*infrastructure.cluster.x-k8s.io
OpenStackMachineTemplate.*infrastructure.cluster.x-k8s.io
Metal3MachineTemplate.*infrastructure.cluster.x-k8s.io
"
# shellcheck disable=SC2068
for TEMPLATE_CR in ${TEMPLATE_TYPES_CR[@]}; do

    if kubectl api-resources | grep -i $TEMPLATE_CR > /dev/null ; then

        # Transform the .* used for matching kubectl api-resource, into a plain '.'
        # (see VSphereMachineTemplates.*cluster.x-k8s.io above)
        TEMPLATE_RESOURCE=${TEMPLATE_CR/\*/}

        # in some places we need to use the short kind name
        TEMPLATE_RESOURCE_SHORT=${TEMPLATE_CR/.*/}

        # Only for (Docker|VSphere|OpenStack|Metal3)MachineTemplates resources
        if [[ $TEMPLATE_RESOURCE =~ .*MachineTemplate ]]; then

            # Extract cloned template resource type from template type (eg. OpenStackMachine out of OpenStackMachineTemplate)
            CLONED_TEMPLATE_RESOURCE="${TEMPLATE_RESOURCE/Template}"
            CLONED_TEMPLATE_RESOURCE_SHORT=${CLONED_TEMPLATE_RESOURCE/.*/}

            echo -e "\n Inspecting all $TEMPLATE_RESOURCE_SHORT resource instances/names for
- usage as (RKE2ControlPlane.spec|KubeadmControlPlane.spec.machineTemplate|OpenshiftAssistedControlPlane.spec.machineTemplate).infrastructureRef.name
- usage as (MachineDeployment|MachineSet).spec.template.spec.infrastructureRef.name
- presence of $CLONED_TEMPLATE_RESOURCE_SHORT resources having the annotation cluster.x-k8s.io/cloned-from-name=<$TEMPLATE_RESOURCE_SHORT resource instance>"

        # Only for (Kubeadm|RKE2|AgentBootstrap)ConfigTemplate resources
        elif [[ $TEMPLATE_RESOURCE =~ .*ConfigTemplate ]]; then

            echo -e "\n Inspecting all $TEMPLATE_RESOURCE_SHORT resource instances/names for
- usage as (MachineDeployment|MachineSet).spec.template.spec.bootstrap.configRef.name"

        fi

        # Get all namespaces in which template resources of a particular type are seen (in which Sylva clusters are deployed)
        for TARGET_NAMESPACE in $(kubectl get $TEMPLATE_RESOURCE --all-namespaces -o=custom-columns=NAME:.metadata.name,NAMESPACE:.metadata.namespace --no-headers | awk '{print $2}' | sort | uniq); do

            # Get all template resources older than 5 minutes (eg. name of all OpenStackMachineTemplates from a ns with .metadata.creationTimestamp > 300s)
            # and only continue if list is not empty
            TEMPLATE_RESOURCE_INSTANCE_LIST=$(kubectl -n "$TARGET_NAMESPACE" get "$TEMPLATE_RESOURCE" -o json | jq -r --argjson timestamp 300 '.items[] | select (.metadata.creationTimestamp | sub("\\..*";"Z") | sub("\\s";"T") | fromdate < now - $timestamp).metadata.name')

            if [ -z "$TEMPLATE_RESOURCE_INSTANCE_LIST" ]; then
                echo -e "\n\t All $TEMPLATE_RESOURCE_SHORT inside namespace $TARGET_NAMESPACE are newer than 5 minutes \n"
                kubectl -n "$TARGET_NAMESPACE" get "$TEMPLATE_RESOURCE" -o=custom-columns=KIND:.kind,NAME:.metadata.name,NAMESPACE:.metadata.namespace,AGE:.metadata.creationTimestamp
                continue
            fi
            echo -e "\n   Garbage collecting CAPI template resources for namespace $TARGET_NAMESPACE"
            # Iterate over template resource instances (eg. each OpenStackMachineTemplate)
            for TEMPLATE_RESOURCE_INSTANCE in $TEMPLATE_RESOURCE_INSTANCE_LIST; do

                : > /tmp/template_resources_consumers.txt
                could_be_removed="true"

                # Only for (Docker|VSphere|OpenStack|Metal3)MachineTemplates resources
                if [[ $TEMPLATE_RESOURCE =~ .*MachineTemplate ]]; then

                    # Check there's no KubeadmControlPlane.spec.machineTemplate.infrastructureRef.name
                    #                 or  RKE2ControlPlane.spec.machineTemplate.infrastructureRef.name
                    #  or (old location)  RKE2ControlPlane.spec.infrastructureRef.name 
                    #    or  OpenshiftAssistedControlPlane.spec.machineTemplate.infrastructureRef.name
                    # usage for the template resource instance
                    if kubectl api-resources | grep -i KubeadmControlPlane > /dev/null ; then
                        kubectl -n "$TARGET_NAMESPACE" get KubeadmControlPlane -o=custom-columns=KIND:.kindNAME:.metadata.name,INFRASTRUCTURE_REF_NAME:.spec.machineTemplate.infrastructureRef.name,INFRASTRUCTURE_REF_KIND:.spec.machineTemplate.infrastructureRef.kind --no-headers >> /tmp/template_resources_consumers.txt
                    fi
                    if kubectl api-resources | grep -i RKE2ControlPlane > /dev/null; then
                        kubectl -n "$TARGET_NAMESPACE" get RKE2ControlPlane -o=custom-columns=KIND:.kind,NAME:.metadata.name,INFRASTRUCTURE_REF_NAME:.spec.infrastructureRef.name,INFRASTRUCTURE_REF_KIND:.spec.infrastructureRef.kind --no-headers >> /tmp/template_resources_consumers.txt
                        kubectl -n "$TARGET_NAMESPACE" get RKE2ControlPlane -o=custom-columns=KIND:.kind,NAME:.metadata.name,INFRASTRUCTURE_REF_NAME:.spec.machineTemplate.infrastructureRef.name,INFRASTRUCTURE_REF_KIND:.spec.infrastructureRef.kind --no-headers >> /tmp/template_resources_consumers.txt
                    fi
                    if kubectl api-resources | grep -i OpenshiftAssistedControlPlane > /dev/null; then
                        kubectl -n "$TARGET_NAMESPACE" get OpenshiftAssistedControlPlane -o=custom-columns=KIND:.kind,NAME:.metadata.name,INFRASTRUCTURE_REF_NAME:.spec.machineTemplate.infrastructureRef.name,INFRASTRUCTURE_REF_KIND:.spec.machineTemplate.infrastructureRef.kind --no-headers >> /tmp/template_resources_consumers.txt
                    fi

                    # Check there's no MachineSet.spec.template.spec.infrastructureRef.name usage for the template resource instance
                    kubectl -n "$TARGET_NAMESPACE" get MachineSet -o=custom-columns=KIND:.kind,NAME:.metadata.name,INFRASTRUCTURE_REF_NAME:.spec.template.spec.infrastructureRef.name,INFRASTRUCTURE_REF_KIND:.spec.template.spec.infrastructureRef.kind --no-headers >> /tmp/template_resources_consumers.txt

                    # Check there's no MachineDeployment.spec.template.spec.infrastructureRef.name usage for the template resource instance
                    kubectl -n "$TARGET_NAMESPACE" get MachineSet -o=custom-columns=KIND:.kind,NAME:.metadata.name,INFRASTRUCTURE_REF_NAME:.spec.template.spec.infrastructureRef.name,INFRASTRUCTURE_REF_KIND:.spec.template.spec.infrastructureRef.kind --no-headers >> /tmp/template_resources_consumers.txt

                    while read INFRASTRUCTURE_CONSUMER_KIND INFRASTRUCTURE_CONSUMER_INSTANCE INFRASTRUCTURE_REF_NAME INFRASTRUCTURE_REF_KIND; do
                    if [[ $INFRASTRUCTURE_REF_NAME == $TEMPLATE_RESOURCE_INSTANCE && $INFRASTRUCTURE_REF_KIND == $TEMPLATE_RESOURCE_SHORT ]]; then
                        echo -e "\n\t Found $TEMPLATE_RESOURCE_SHORT/$TEMPLATE_RESOURCE_INSTANCE being referenced by $INFRASTRUCTURE_CONSUMER_KIND/$INFRASTRUCTURE_CONSUMER_INSTANCE."
                        could_be_removed="false"
                    fi
                    done < /tmp/template_resources_consumers.txt

                    # Check if there are currently any cloned template resources still linked to the template resource instance
                    EXISTING_CLONED_RESOURCES=$(kubectl -n "$TARGET_NAMESPACE" get $CLONED_TEMPLATE_RESOURCE -o jsonpath="{ $.items[?(@.metadata.annotations.cluster\.x-k8s\.io\/cloned-from-name == '$TEMPLATE_RESOURCE_INSTANCE')].metadata.name}" | wc -w)

                    # Don't consider template resource instance for deletion if cloned resources still exist for it
                    if [[ $EXISTING_CLONED_RESOURCES -gt 0 ]]; then
                        echo -e "\n\t The following $CLONED_TEMPLATE_RESOURCE_SHORT resources are annotated with cluster.x-k8s.io/cloned-from-name=$TEMPLATE_RESOURCE_INSTANCE:"
                        kubectl -n "$TARGET_NAMESPACE" get $CLONED_TEMPLATE_RESOURCE -o jsonpath="{ $.items[?(@.metadata.annotations.cluster\.x-k8s\.io\/cloned-from-name == '$TEMPLATE_RESOURCE_INSTANCE')].metadata.name}" | sed 's/^/\'$'\t/'
                        echo -e "\n\t Thus $TEMPLATE_RESOURCE_SHORT/$TEMPLATE_RESOURCE_INSTANCE is not considered for garbage collection."
                        could_be_removed="false"
                    fi
                fi

                # Only for (Kubeadm|RKE2|AgentBootstrap)ConfigTemplate resources
                if [[ $TEMPLATE_RESOURCE =~ .*ConfigTemplate ]]; then

                    # Check there's no MachineSet.spec.template.spec.bootstrap.configRef.name usage for the template resource instance
                    kubectl -n "$TARGET_NAMESPACE" get MachineSet -o=custom-columns=KIND:.kind,NAME:.metadata.name,BOOTSTRAP_CONFIG_REF_NAME:.spec.template.spec.bootstrap.configRef.name,BOOTSTRAP_CONFIG_REF_KIND:.spec.template.spec.bootstrap.configRef.kind --no-headers >> /tmp/template_resources_consumers.txt

                    # Check there's no MachineDeployment.spec.template.spec.bootstrap.configRef.name usage for the template resource instance
                    kubectl -n "$TARGET_NAMESPACE" get MachineDeployment -o=custom-columns=KIND:.kind,NAME:.metadata.name,BOOTSTRAP_CONFIG_REF_NAME:.spec.template.spec.bootstrap.configRef.name,BOOTSTRAP_CONFIG_REF_KIND:.spec.template.spec.bootstrap.configRef.kind --no-headers >> /tmp/template_resources_consumers.txt

                    while read BOOTSTRAP_CONSUMER_KIND BOOTSTRAP_CONSUMER_INSTANCE BOOTSTRAP_CONFIG_REF_NAME BOOTSTRAP_CONFIG_REF_KIND; do
                        if [[ $BOOTSTRAP_CONFIG_REF_NAME == $TEMPLATE_RESOURCE_INSTANCE && $BOOTSTRAP_CONFIG_REF_KIND == $TEMPLATE_RESOURCE_SHORT ]]; then
                            echo -e "\n\t Found $TEMPLATE_RESOURCE_SHORT/$TEMPLATE_RESOURCE_INSTANCE being referenced by $BOOTSTRAP_CONSUMER_KIND/$BOOTSTRAP_CONSUMER_INSTANCE."
                            could_be_removed="false"
                        fi
                    done < /tmp/template_resources_consumers.txt
                fi

                if [[ "$could_be_removed" == "true" ]]; then
                    echo -e "\n\t Preparing deletion of $TEMPLATE_RESOURCE_SHORT/$TEMPLATE_RESOURCE_INSTANCE"
                        TEMPLATE_RESOURCE_API_VERSION=$(kubectl -n "$TARGET_NAMESPACE" get "$TEMPLATE_RESOURCE/$TEMPLATE_RESOURCE_INSTANCE" -o json | jq .apiVersion)

                        echo -e "\n\t Deleting $TEMPLATE_RESOURCE_SHORT/$TEMPLATE_RESOURCE_INSTANCE"
                        kubectl -n "$TARGET_NAMESPACE" delete "$TEMPLATE_RESOURCE/$TEMPLATE_RESOURCE_INSTANCE" | sed 's/^/\'$'\t/'

                        echo -e "\n\t Creating an event for this deletion"
                        kubectl apply -f - <<EOF
apiVersion: v1
kind: Event
metadata:
  name: capi-garbage-cleanup.delete.$(printf "%0000x%0000x" $RANDOM $RANDOM)
  namespace: sylva-system
type: Normal
reportingComponent: capi-garbage-cleanup
message: capi-garbage-cleanup deleted $TEMPLATE_RESOURCE/$TEMPLATE_RESOURCE_INSTANCE in $TARGET_NAMESPACE namespace
reason: capi-garbage-cleanup determined that this object isn't referred to anymore
firstTimestamp: $(date -Iseconds -u | sed 's/+00:00/Z/')
involvedObject:
  apiVersion: $TEMPLATE_RESOURCE_API_VERSION
  kind: $TEMPLATE_RESOURCE_SHORT
  name: $TEMPLATE_RESOURCE_INSTANCE
  namespace: $TARGET_NAMESPACE
action: delete
source:
  component: capi-garbage-cleanup
  host: $HOSTNAME
EOF
                fi
            done
        done
    fi
done
