#!/usr/bin/env python3
"""
Find the most likely clone in a swigh exhaustive TSV by ranking on count,
SW_score, and identity (all descending).
"""

import argparse
import csv
from pathlib import Path
from typing import Dict, Tuple


def ranking_key(row: Dict[str, str]) -> Tuple[int, float, float]:
    """Return a sort key: highest count, then SW_score, then identity."""
    return (
        int(row["Count"]),
        float(row["SW_score"]),
        float(row["Identity"]),
    )


def find_top_clone(path: Path) -> Dict[str, str]:
    with path.open(newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        top = None
        for row in reader:
            if top is None or ranking_key(row) > ranking_key(top):
                top = row
        if top is None:
            raise ValueError("No data rows found")
        return top


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Find most likely clone by count, SW_score, then identity."
    )
    parser.add_argument("tsv", type=Path, help="exhaustive TSV file")
    args = parser.parse_args()

    top = find_top_clone(args.tsv)

    print("Top clone (ranked by Count, SW_score, Identity):")
    print(f"  Gene: {top['Gene']}")
    print(f"  Count: {top['Count']}")
    print(f"  SW_score: {top['SW_score']}")
    print(f"  Identity: {top['Identity']}")
    print(f"  Swigh_score: {top['Swigh_score']}")
    print(f"  Sequence: {top['Sequence']}")


if __name__ == "__main__":
    main()
