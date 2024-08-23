#!/bin/bash

# Helper script used to clean management and workload clusters OpenStack resources and bootstrap cluster if user pass yes. USE WITH CARE, AT YOU OWN RISK

# takes 2 input:
#    1st openstack profile(as with openstack-cleanup.sh script)
#    2nd yes/no (for bootstrap cluster cleanup)

# Check if the correct number of arguments is provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <arg1> <yes|no>"
    exit 1
fi

# Assign input arguments to variables
ARG1=$1
CONFIRMATION=$2

# Check if the second argument is either "yes" or "no"
if [[ "$CONFIRMATION" != "yes" && "$CONFIRMATION" != "no" ]]; then
    echo "Error: The second argument must be either 'yes' or 'no'."
    exit 1
fi

# Call the openstack-cleanup.sh script with the first argument
./tools/openstack-cleanup.sh "$ARG1"

# If the second argument is "yes", delete the kind cluster named "sylva"
if [ "$CONFIRMATION" == "yes" ]; then
    echo "Deleting kind cluster named 'sylva'..."
    kind delete cluster --name sylva
    echo "Bootstrap cluster 'sylva' deleted."
    echo "Full cleanup completed."
else
    echo "Skipping cluster deletion."
    echo "Only OpenStack cleanup done!!."
fi
