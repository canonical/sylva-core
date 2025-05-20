#!/usr/bin/env python3

import yaml
from pathlib import Path
from typing import Dict

DOCS_DIR = Path("charts/sylva-units/docs")
SETTINGS_FILE = Path("charts/sylva-units/schemas/units-settings.yaml")


def load_settings(filepath: Path) -> Dict:
    with filepath.open("r") as f:
        return yaml.safe_load(f)


def render_setting(name: str, details: Dict, prefix: str = "") -> str:
    lines = [f"### `{prefix}{name}`"]
    if details.get("type"):
        lines.append(f"**Type**: `{details['type']}`  ")
    if details.get("default"):
        lines.append(f"**Default**: `{details['default']}`  ")
    if details.get("upstream_path"):
        lines.append(f"**Injected into**: `{details['upstream_path']}`  ")
    if details.get("example"):
        lines.append("**Example**:")
        lines.append("```yaml")
        lines.append(str(details["example"]))
        lines.append("```")
    if details.get("description"):
        lines.append(f"**Description**:\n{details['description']}")
    lines.append("")
    return "\n".join(lines)


def process_settings(unit_name: str, settings: Dict, prefix: str = "") -> str:
    output = []
    for setting, details in settings.items():
        if not isinstance(details, dict):
            continue

        full_name = f"{prefix}{setting}"

        if "properties" in details:
            # Document parent field
            output.append(f"## `{full_name}` (object)")
            if details.get("description"):
                output.append(f"{details['description']}\n")
            output.append("Contains the following sub-fields:\n")
            # Recurse into sub-properties
            subprops = details["properties"]
            output.append(process_settings(unit_name, subprops, prefix=f"{full_name}.").strip())
        else:
            output.append(render_setting(setting, details, prefix))

    return "\n".join(output)


def generate_markdown_for_unit(unit_name: str, settings: Dict) -> str:
    meta = settings.pop("_meta", {})
    deprecated = meta.get("deprecated", False)

    lines = [f"# `{unit_name}` Settings"]
    if deprecated:
        lines.append(f"> ⚠️ This unit is **deprecated** and may be removed in future versions.\n")

    lines.append(process_settings(unit_name, settings))
    return "\n".join(lines)


def write_docs(units: Dict):
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    for unit, settings in units.items():
        markdown = generate_markdown_for_unit(unit, settings.copy())
        output_path = DOCS_DIR / f"{unit}.md"
        with output_path.open("w") as f:
            f.write(markdown)
        print(f"✅ Generated: {output_path}")


if __name__ == "__main__":
    if not SETTINGS_FILE.exists():
        raise FileNotFoundError(f"units-settings.yaml not found at {SETTINGS_FILE}")

    settings_data = load_settings(SETTINGS_FILE)
    write_docs(settings_data)
    print("\n📘 Documentation successfully generated.")
