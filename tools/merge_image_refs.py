import argparse
import json
from typing import Dict, List


def update_images_ref(images_ref: Dict, new_data: Dict) -> Dict:
    """
    Update the images_ref dictionary with new data.

    :param images_ref: Existing images_ref dictionary.
    :param new_data: New data to merge into images_ref.
    :return: Updated images_ref dictionary.
    """
    for key, value in new_data.items():
        if key in images_ref:
            if isinstance(images_ref[key], list) and isinstance(value, list):
                # Merge lists and remove duplicates
                images_ref[key] = list(set(images_ref[key] + value))
            elif isinstance(images_ref[key], dict) and isinstance(value, dict):
                # Recursively merge dictionaries
                images_ref[key] = update_images_ref(images_ref[key], value)
            else:
                # If types do not match, merge into a list to preserve both values
                if not isinstance(images_ref[key], list):
                    images_ref[key] = [images_ref[key]]
                if not isinstance(value, list):
                    value = [value]
                images_ref[key] = list(set(images_ref[key] + value))
        else:
            images_ref[key] = value
    return images_ref


def clean_dependencies(dependencies: Dict, keys_to_remove: List[str]) -> Dict:
    """
    Clean the dependencies by removing specified keys.

    :param dependencies: The dependencies dictionary.
    :param keys_to_remove: List of key prefixes to identify objects to remove.
    :return: The cleaned dependencies dictionary.
    """
    if isinstance(dependencies, dict):
        keys_to_remove_list = []
        for key, value in dependencies.items():
            if any(key.startswith(prefix) for prefix in keys_to_remove):
                keys_to_remove_list.append(key)
            else:
                clean_dependencies(value, keys_to_remove)
        for key in keys_to_remove_list:
            del dependencies[key]
    return dependencies


def normalize_keys(dependencies: Dict) -> Dict:
    """
    Normalize the keys by removing the second part (namespace) of the key.

    :param dependencies: The dependencies dictionary.
    :return: The normalized dependencies dictionary.
    """
    if isinstance(dependencies, dict):
        normalized_dependencies = {}
        for key, value in dependencies.items():
            parts = key.split('/')
            if len(parts) == 3:
                normalized_key = '/'.join([parts[0]] + parts[2:])  # Remove the namespace part
            else:
                normalized_key = key
            normalized_dependencies[normalized_key] = normalize_keys(value)
        return normalized_dependencies
    return dependencies


def load_and_prepare_json(file_path: str, keys_to_remove: List[str]) -> Dict:
    """
    Load JSON data from a file and clean it by removing specified keys.

    :param file_path: Path to the JSON file.
    :param keys_to_remove: List of key prefixes to identify objects to remove.
    :return: Cleaned JSON data.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
            if 'pod_images_dependencies' in data:
                cleaned_dependencies = {}
                for image, dependencies in data['pod_images_dependencies'].items():
                    cleaned_dependencies[image] = clean_dependencies(dependencies, keys_to_remove)
                    cleaned_dependencies[image] = normalize_keys(cleaned_dependencies[image])
                data['pod_images_dependencies'] = cleaned_dependencies
            return data
    except Exception as e:
        print(f"Error reading input file {file_path}: {e}")
        return {}


def merge_images_ref_files(input_files: List[str], output_file: str, keys_to_remove: List[str] = None):
    """
    Merge multiple images_ref files into one.

    :param input_files: List of input file paths.
    :param output_file: Path to the output file.
    :param keys_to_remove: List of key prefixes to identify objects to remove.
    """
    merged_images_ref = {}

    for input_file in input_files:
        data = load_and_prepare_json(input_file, keys_to_remove)
        merged_images_ref = update_images_ref(merged_images_ref, data)

    try:
        with open(output_file, "w", encoding="utf-8") as out_file:
            json.dump(merged_images_ref, out_file, indent=4)
            print(f"Merged result saved to {output_file}")
    except Exception as e:
        print(f"Error writing output file {output_file}: {e}")


def main():
    """
    Main function to parse arguments and merge images_ref files.
    """
    parser = argparse.ArgumentParser(description='Merge multiple images_ref files into one.')
    parser.add_argument('-i', '--input',
                        required=True,
                        nargs='+',
                        help='Paths to input images_ref files.')
    parser.add_argument('-o', '--output',
                        required=True,
                        help='Path to the output file.')
    parser.add_argument('-r', '--remove-keys',
                        required=False,
                        nargs='+',
                        default=["Pod/", "ReplicaSet/"],
                        help='Prefixes of keys to remove. Example: "Pod/", "ReplicaSet/" ')
    args = parser.parse_args()

    merge_images_ref_files(args.input, args.output, args.remove_keys)


if __name__ == "__main__":
    main()
