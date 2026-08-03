#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")


def version_key(version: str) -> tuple[int, int, int]:
    major, minor, patch = version.split(".")
    return int(major), int(minor), int(patch)


def list_sigma_versions(base_dir: Path) -> list[str]:
    versions = [
        path.name
        for path in base_dir.iterdir()
        if path.is_dir() and VERSION_PATTERN.match(path.name)
    ]
    return sorted(versions, key=version_key)


def main() -> int:
    parser = argparse.ArgumentParser(description="List committed sigma-cli version directories.")
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Directory containing sigma-cli version subdirectories.",
    )
    parser.add_argument("--json", action="store_true", help="Print versions as a JSON array.")
    parser.add_argument(
        "--has-versions",
        action="store_true",
        help="Exit successfully when at least one version directory exists.",
    )
    args = parser.parse_args()

    versions = list_sigma_versions(args.base_dir)

    if args.has_versions:
        return 0 if versions else 1

    if args.json:
        print(json.dumps(versions))
    else:
        for version in versions:
            print(version)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
