from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.poi_catalog import PoiCatalogError, csv_to_catalog, write_catalog_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert poiCatalog CSV to validated JSON.")
    parser.add_argument("csv_path", nargs="?", default=str(ROOT / "data" / "poiCatalog.sample.csv"))
    parser.add_argument("json_path", nargs="?", default=str(ROOT / "data" / "poiCatalog.sample.json"))
    args = parser.parse_args()

    try:
        catalog, result = csv_to_catalog(Path(args.csv_path))
    except (OSError, ValueError, PoiCatalogError) as error:
        print(f"poiCatalog conversion failed: {error}")
        return 1

    if result.errors:
        print("poiCatalog conversion failed; JSON was not generated:")
        for error in result.errors:
            print(f"- {error}")
        return 1

    if result.warnings:
        print("poiCatalog conversion warnings:")
        for warning in result.warnings:
            print(f"- {warning}")
    write_catalog_json(catalog, Path(args.json_path))
    print(f"poiCatalog JSON generated: {args.json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
