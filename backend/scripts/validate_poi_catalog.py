from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.poi_catalog import csv_to_catalog, validate_poi_catalog_with_warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate poiCatalog CSV or JSON data.")
    parser.add_argument("path", nargs="?", default=str(ROOT / "data" / "poiCatalog.sample.json"))
    args = parser.parse_args()

    path = Path(args.path)
    try:
        if path.suffix.lower() == ".csv":
            _, result = csv_to_catalog(path)
        else:
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)
            result = validate_poi_catalog_with_warnings(data)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"poiCatalog validation failed: {error}")
        return 1

    if result.errors:
        print("poiCatalog validation failed:")
        for error in result.errors:
            print(f"- {error}")
        return 1

    if result.warnings:
        print("poiCatalog validation warnings:")
        for warning in result.warnings:
            print(f"- {warning}")
    print(f"poiCatalog validation passed: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
