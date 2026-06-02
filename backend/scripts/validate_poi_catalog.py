from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.poi_catalog import validate_poi_catalog


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate poiCatalog JSON data.")
    parser.add_argument("path", nargs="?", default=str(ROOT / "data" / "poiCatalog.sample.json"))
    args = parser.parse_args()

    path = Path(args.path)
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        print(f"poiCatalog validation failed: {error}")
        return 1

    errors = validate_poi_catalog(data)
    if errors:
        print("poiCatalog validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"poiCatalog validation passed: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
