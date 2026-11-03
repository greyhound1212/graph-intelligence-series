
"""
Generate deterministic synthetic datasets for the Graph Intelligence Series.

Datasets:
    HBL-01: Graph Intelligence Fundamentals
    HBL-02: Cypher for Intelligence Analysis
    HBL-03: Social Network Analysis
    HBL-04: Python for Graph Intelligence
    HBL-05: Advanced Graph Analytics
    HBL-06: From Graph Data to Intelligence Products

Usage:
    python generator/generate.py
    python generator/generate.py --dataset hbl-01
    python generator/generate.py --dataset hbl-06
"""

import argparse
import csv
import hashlib
import json
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
BASE_SEED = 202701
VERSION = "1.0.0"

# Provisional scaling profiles for Books 2–6.
# Replace these values with finalized dataset specifications.
DATASET_PROFILES = {
    "hbl-01": {
        "multiplier": 1,
        "relationships": 350,
        "sources": 50,
    },
    "hbl-02": {
        "multiplier": 2,
        "relationships": 900,
        "sources": 100,
    },
    "hbl-03": {
        "multiplier": 3,
        "relationships": 1800,
        "sources": 150,
    },
    "hbl-04": {
        "multiplier": 4,
        "relationships": 3000,
        "sources": 200,
    },
    "hbl-05": {
        "multiplier": 6,
        "relationships": 6000,
        "sources": 300,
    },
    "hbl-06": {
        "multiplier": 8,
        "relationships": 10000,
        "sources": 400,
    },
}

NODE_SPECIFICATIONS = [
    ("Person", "PER", 40, "Person"),
    ("Organization", "ORG", 20, "Meridian Enterprise"),
    ("Location", "LOC", 25, "Port Meridian Site"),
    ("Vehicle", "VEH", 15, "Vehicle"),
    ("Event", "EVT", 20, "Port Activity"),
    ("Shipment", "SHP", 15, "Shipment"),
    ("Transaction", "TX", 10, "Transfer"),
    ("Account", "ACC", 5, "Account"),
]

SPECIAL_NAMES = {
    "PER-001": "Mara Voss",
    "PER-002": "Elias Renner",
    "PER-003": "Sofia Kade",
    "PER-004": "Jonas Vale",
    "PER-005": "Nina Solberg",
    "ORG-001": "Meridian Freight Ltd",
    "ORG-002": "North Quay Storage",
    "ORG-003": "Bluewater Trade Services",
    "ORG-004": "Harborline Transport",
    "LOC-001": "East Dock Warehouse",
    "LOC-002": "North Terminal",
    "LOC-003": "Meridian Business Center",
    "LOC-004": "West Logistics Yard",
}

RELATIONSHIP_RULES = [
    ("WORKS_FOR", "Person", "Organization"),
    ("MANAGES", "Person", "Organization"),
    ("REGISTERED_AT", "Organization", "Location"),
    ("OPERATES", "Organization", "Vehicle"),
    ("PARTICIPATED_IN", "Person", "Event"),
    ("OCCURRED_AT", "Event", "Location"),
    ("INVOLVES_VEHICLE", "Event", "Vehicle"),
    ("SENT", "Organization", "Shipment"),
    ("RECEIVED", "Organization", "Shipment"),
    ("ORIGINATED_AT", "Shipment", "Location"),
    ("DESTINED_FOR", "Shipment", "Location"),
    ("HOLDS_ACCOUNT", "Organization", "Account"),
    ("DEBITED_FROM", "Transaction", "Account"),
    ("CREDITED_TO", "Transaction", "Account"),
]

MANDATORY_RELATIONSHIPS = [
    ("PER-001", "MANAGES", "ORG-001"),
    ("PER-002", "WORKS_FOR", "ORG-001"),
    ("PER-003", "WORKS_FOR", "ORG-002"),
    ("PER-004", "WORKS_FOR", "ORG-004"),
    ("ORG-001", "REGISTERED_AT", "LOC-003"),
    ("ORG-002", "REGISTERED_AT", "LOC-001"),
    ("ORG-004", "REGISTERED_AT", "LOC-004"),
    ("ORG-003", "REGISTERED_AT", "LOC-003"),
]

CSV_FIELDS = {
    "nodes.csv": [
        "id", "label", "name", "synthetic"
    ],
    "relationships.csv": [
        "id", "source_id", "type", "target_id",
        "valid_from", "valid_to", "synthetic"
    ],
    "sources.csv": [
        "id", "type", "title", "origin_source_id",
        "collected_at", "reliability",
        "information_credibility", "access_class"
    ],
    "assertions.csv": [
        "id", "subject_id", "predicate", "object_id",
        "assessment", "valid_from", "valid_to"
    ],
    "evidence.csv": [
        "assertion_id", "source_id"
    ],
}


def generate_nodes(multiplier: int) -> list[dict]:
    """Generate domain entities with stable identifiers."""
    nodes = []

    for label, prefix, base_count, default_name in NODE_SPECIFICATIONS:
        count = base_count * multiplier

        for index in range(1, count + 1):
            entity_id = f"{prefix}-{index:03d}"

            nodes.append({
                "id": entity_id,
                "label": label,
                "name": SPECIAL_NAMES.get(
                    entity_id,
                    f"{default_name} {index:03d}",
                ),
                "synthetic": "true",
            })

    return nodes


def generate_relationships(
    nodes: list[dict],
    target_count: int,
    rng: random.Random,
) -> list[dict]:
    """Generate unique, type-valid domain relationships."""
    nodes_by_label = {
        label: [
            node["id"]
            for node in nodes
            if node["label"] == label
        ]
        for label, _, _, _ in NODE_SPECIFICATIONS
    }

    relationships = []
    seen = set()

    def add_relationship(
        source_id: str,
        relationship_type: str,
        target_id: str,
    ) -> bool:
        key = (source_id, relationship_type, target_id)

        if key in seen:
            return False

        seen.add(key)

        relationships.append({
            "id": f"REL-{len(relationships) + 1:04d}",
            "source_id": source_id,
            "type": relationship_type,
            "target_id": target_id,
            "valid_from": "2027-01-01",
            "valid_to": "",
            "synthetic": "true",
        })

        return True

    for relationship in MANDATORY_RELATIONSHIPS:
        add_relationship(*relationship)

    maximum_possible = sum(
        len(nodes_by_label[source_label])
        * len(nodes_by_label[target_label])
        for _, source_label, target_label in RELATIONSHIP_RULES
    )

    if target_count > maximum_possible:
        raise ValueError(
            f"Requested {target_count} relationships, "
            f"but only {maximum_possible} unique combinations exist."
        )

    while len(relationships) < target_count:
        relationship_type, source_label, target_label = (
            rng.choice(RELATIONSHIP_RULES)
        )

        add_relationship(
            rng.choice(nodes_by_label[source_label]),
            relationship_type,
            rng.choice(nodes_by_label[target_label]),
        )

    return relationships


def generate_sources(count: int) -> list[dict]:
    """Generate synthetic provenance sources."""
    source_types = [
        "SyntheticRegistry",
        "SyntheticManifest",
        "SyntheticObservation",
        "SyntheticLedger",
    ]

    sources = []

    for index in range(1, count + 1):
        sources.append({
            "id": f"SRC-{index:04d}",
            "type": source_types[index % len(source_types)],
            "title": f"Harborlight synthetic source {index:03d}",
            "origin_source_id": "",
            "collected_at": "2027-12-31T12:00:00",
            "reliability": ["A", "B", "C"][index % 3],
            "information_credibility": [
                "1", "2", "3"
            ][index % 3],
            "access_class": "SYNTHETIC",
        })

    return sources


def generate_assertions(
    relationships: list[dict],
    sources: list[dict],
) -> tuple[list[dict], list[dict]]:
    """Generate assertions and their supporting evidence links."""
    assertions = []
    evidence = []

    for index, relationship in enumerate(relationships):
        assertion_id = f"AST-{index + 1:04d}"

        assertions.append({
            "id": assertion_id,
            "subject_id": relationship["source_id"],
            "predicate": relationship["type"],
            "object_id": relationship["target_id"],
            "assessment": (
                "Unverified"
                if index % 7 == 0
                else "Supported"
            ),
            "valid_from": relationship["valid_from"],
            "valid_to": relationship["valid_to"],
        })

        evidence.append({
            "assertion_id": assertion_id,
            "source_id": sources[index % len(sources)]["id"],
        })

    return assertions, evidence


def write_csv(
    output_dir: Path,
    filename: str,
    rows: list[dict],
) -> None:
    """Write a CSV file using a predefined column order."""
    path = output_dir / filename

    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=CSV_FIELDS[filename],
        )
        writer.writeheader()
        writer.writerows(rows)


def calculate_sha256(path: Path) -> str:
    """Calculate the SHA-256 checksum of a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generate_dataset(dataset_id: str) -> None:
    """Generate one complete Harborlight dataset."""
    profile = DATASET_PROFILES[dataset_id]
    output_dir = DATA_DIR / dataset_id
    output_dir.mkdir(parents=True, exist_ok=True)

    dataset_number = int(dataset_id.split("-")[1])

    # Each dataset has its own deterministic random sequence.
    seed = BASE_SEED + dataset_number - 1
    rng = random.Random(seed)

    nodes = generate_nodes(profile["multiplier"])

    relationships = generate_relationships(
        nodes,
        profile["relationships"],
        rng,
    )

    sources = generate_sources(profile["sources"])

    assertions, evidence = generate_assertions(
        relationships,
        sources,
    )

    datasets = {
        "nodes.csv": nodes,
        "relationships.csv": relationships,
        "sources.csv": sources,
        "assertions.csv": assertions,
        "evidence.csv": evidence,
    }

    for filename, rows in datasets.items():
        write_csv(output_dir, filename, rows)

    manifest = {
        "dataset": dataset_id.upper(),
        "version": VERSION,
        "seed": seed,
        "synthetic": True,
        "domain_nodes": len(nodes),
        "domain_relationships": len(relationships),
        "sources": len(sources),
        "assertions": len(assertions),
        "evidence_links": len(evidence),
        "total_nodes": len(nodes) + len(sources) + len(assertions),
        "total_relationships": (
            len(relationships)
            + 2 * len(assertions)
            + len(evidence)
        ),
        "sha256": {
            filename: calculate_sha256(output_dir / filename)
            for filename in datasets
        },
    }

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )

    print(
        f"{dataset_id.upper()}: "
        f"{manifest['total_nodes']} nodes, "
        f"{manifest['total_relationships']} relationships"
    )


def main() -> None:
    """Generate the requested datasets."""
    parser = argparse.ArgumentParser(
        description="Generate Harborlight synthetic datasets."
    )

    parser.add_argument(
        "--dataset",
        choices=["all", *DATASET_PROFILES],
        default="all",
        help="Dataset to generate (default: all).",
    )

    args = parser.parse_args()

    selected_datasets = (
        DATASET_PROFILES
        if args.dataset == "all"
        else [args.dataset]
    )

    for dataset_id in selected_datasets:
        generate_dataset(dataset_id)

    print("Dataset generation completed successfully.")


if __name__ == "__main__":
    main()
