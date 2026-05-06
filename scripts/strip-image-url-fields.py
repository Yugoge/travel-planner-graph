#!/usr/bin/env python3
# Description: Recursively strip "image_url" keys from JSON files (PATH B image migration).
# Usage: source venv/bin/activate && python scripts/strip-image-url-fields.py <file_or_dir> [...]
# Exit codes: 0=success, 1=invalid arg, 2=file error

import json
import sys
from pathlib import Path

# Route persistence through the canonical save layer so post-strip writes hit
# the iter-2 ownership rejector + universal image_url deny. After stripping
# image_url fields the universal deny is a no-op (payload is image_url-free);
# ownership still applies (target file must be in the inferred agent's
# owned_files allowlist).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.json_io import save_agent_json  # noqa: E402


def strip_image_url(node):
    """Recursively remove all 'image_url' keys from any dict in node. Returns count."""
    removed = 0
    if isinstance(node, dict):
        if "image_url" in node:
            del node["image_url"]
            removed += 1
        for value in node.values():
            removed += strip_image_url(value)
    elif isinstance(node, list):
        for item in node:
            removed += strip_image_url(item)
    return removed


def process_file(path: Path) -> int:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"[error] {path}: {e}", file=sys.stderr)
        return -1

    count = strip_image_url(data)
    if count > 0:
        # Iter 2 (spec-20260505-221501 / W2): route through json_io's
        # save_agent_json so the ownership rejector + universal image_url
        # deny + stock-image deny all fire. agent_name inferred from
        # filename stem (e.g., meals.json -> meals).
        agent_name = path.stem
        inner_data = data.get("data", data) if isinstance(data, dict) else data
        save_agent_json(
            path,
            agent_name=agent_name,
            data=inner_data,
            validate=False,
            create_backup=False,
            allow_high_severity=True,
        )
        print(f"[ok] {path}: removed {count} image_url field(s)")
    else:
        print(f"[skip] {path}: no image_url fields")
    return count


def main():
    if len(sys.argv) < 2:
        print("Usage: strip-image-url-fields.py <file_or_dir> [...]", file=sys.stderr)
        return 1

    targets = []
    for arg in sys.argv[1:]:
        p = Path(arg)
        if p.is_dir():
            targets.extend(sorted(p.glob("*.json")))
        elif p.is_file():
            targets.append(p)
        else:
            print(f"[error] not found: {arg}", file=sys.stderr)
            return 2

    total_removed = 0
    file_errors = 0
    for target in targets:
        result = process_file(target)
        if result < 0:
            file_errors += 1
        else:
            total_removed += result

    print(f"\nSummary: {total_removed} image_url field(s) removed across {len(targets)} file(s); {file_errors} error(s).")
    return 0 if file_errors == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
