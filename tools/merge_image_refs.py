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
            if isinstance(images_ref[key], list):
                images_ref[key] = list(set(images_ref[key] + value))
            elif isinstance(images_ref[key], dict):
                for sub_key, sub_value in value.items():
                    if sub_key in images_ref[key]:
                        images_ref[key][sub_key] = list(set(images_ref[key][sub_key] + sub_value))
                    else:
                        images_ref[key][sub_key] = sub_value
        else:
            images_ref[key] = value
    return images_ref


def merge_images_ref_files(input_files: List[str], output_file: str):
    """
    Merge multiple images_ref files into one.

    :param input_files: List of input file paths.
    :param output_file: Path to the output file.
    """
    merged_images_ref = {}

    for input_file in input_files:
        try:
            with open(input_file, "r", encoding="utf-8") as in_file:
                data = json.load(in_file)
                merged_images_ref = update_images_ref(merged_images_ref, data)
        except Exception as e:
            print(f"Error reading input file {input_file}: {e}")

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
    args = parser.parse_args()

    merge_images_ref_files(args.input, args.output)


if __name__ == "__main__":
    main()
