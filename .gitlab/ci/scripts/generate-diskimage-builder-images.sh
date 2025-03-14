#!/bin/bash
# This script take as input parameter a tag of diskimage-builder repo
# It will try to download the associated release notes and parse it to generate sylva_diskimagebuilder_images
# Then it will update sylva-units values file with it
# 
# Used by renovate bot

release=$1
diskimage_build_project_id=43786055
input_file=$(mktemp)
output_file=$(mktemp)
sylva_units_values_file="../../../charts/sylva-units/values.yaml"

curl -s https://gitlab.com/api/v4/projects/$diskimage_build_project_id/releases/$release  | yq .description > $input_file

echo "sylva_diskimagebuilder_images:" > "$output_file"

grep -oP 'oci://registry\.gitlab\.com/sylva-projects/sylva-elements/diskimage-builder/\K[^:]*' "$input_file"| sort -r  | while read -r line; do
    image_name=$(echo "$line" | sed 's/:.*//')
    echo "  $image_name:" >> "$output_file"
    echo "    os_images_oci_registry: sylva" >> "$output_file"
done

cat "$output_file"

yq -i eval-all '. as $item ireduce ({}; . * $item )' $output_file $sylva_units_values_file