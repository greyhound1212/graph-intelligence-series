"""Generate the deterministic HBL-01 synthetic graph dataset."""

import csv
import hashlib
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data"
SEED = 202701

SPEC = [
    ("Person", "PER", 40),
    ("Organization", "ORG", 20),
    ("Location", "LOC", 25),
    ("Vehicle", "VEH", 15),
    ("Event", "EVT", 20),
    ("Shipment", "SHP", 15),
    ("Transaction", "TX", 10),
    ("Account", "ACC", 5),
]

BASE_NAMES = {
    "Person": "Person",
    "Organization": "Meridian Enterprise",
    "Location": "Port Meridian Site",
    "Vehicle": "Vehicle",
    "Event": "Port Activity",
    "Shipment": "Shipment",
    "Transaction": "Transfer",
    "Account": "Account",
}

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

RULES = [
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

MANDATORY = [
    ("PER-001", "MANAGES", "ORG-001"),
    ("PER-002", "WORKS_FOR", "ORG-001"),
    ("PER-003", "WORKS_FOR", "ORG-002"),
    ("PER-004", "WORKS_FOR", "ORG-004"),
    ("ORG-001", "REGISTERED_AT", "LOC-003"),
    ("ORG-002", "REGISTERED_AT", "LOC-001"),
    ("ORG-004", "REGISTERED_AT", "LOC-004"),
    ("ORG-003", "REGISTERED_AT", "LOC-003"),
    ("ORG-001", "REGISTERED_AT", "LOC-003"),
]

SOURCE_TYPES = [
    "SyntheticRegistry",
    "SyntheticManifest",
    "SyntheticObservation",
    "SyntheticLedger",
]


def write_csv(filename, records, fields):
    """Write records in a stable field order."""
    with (OUT / filename).open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)


def build():
    """Build nodes, relationships, and the associated evidence layer."""
    OUT.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)

    nodes = []
    for label, prefix, count in SPEC:
        for index in range(1, count + 1):
            node_id = f"{prefix}-{index:03d}"
            name = SPECIAL_NAMES.get(
                node_id, f"{BASE_NAMES[label]} {index:03d}"
            )
            nodes.append({
                "id": node_id,
                "label": label,
                "name": name,
                "synthetic": "true",
            })

    by_label = {
        label: [node["id"] for node in nodes if node["label"] == label]
        for label, _, _ in SPEC
    }

    relationships = []
    seen = set()

    def add_relationship(source, rel_type, target):
        key = (source, rel_type, target)
        if key in seen:
            return False
        seen.add(key)
        relationships.append({
            "id": f"REL-{len(relationships) + 1:04d}",
            "source_id": source,
            "type": rel_type,
            "target_id": target,
            "valid_from": "2027-01-01",
            "valid_to": "",
            "synthetic": "true",
        })
        return True

    for relationship in MANDATORY:
        add_relationship(*relationship)

    while len(relationships) < 350:
        rel_type, source_label, target_label = rng.choice(RULES)
        add_relationship(
            rng.choice(by_label[source_label]),
            rel_type,
            rng.choice(by_label[target_label]),
        )

    sources = []
    for index in range(1, 51):
        sources.append({
            "id": f"SRC-{index:04d}",
            "type": SOURCE_TYPES[index % 4],
            "title": f"Harborlight synthetic source {index:03d}",
            "origin_source_id": "",
            "collected_at": "2027-12-31T12:00:00",
            "reliability": ["A", "B", "C"][index % 3],
            "information_credibility": ["1", "2", "3"][index % 3],
            "access_class": "SYNTHETIC",
        })

    assertions = []
    evidence = []
    for index, relationship in enumerate(relationships):
        assertion_id = f"AST-{index + 1:04d}"
        assertions.append({
            "id": assertion_id,
            "subject_id": relationship["source_id"],
            "predicate": relationship["type"],
            "object_id": relationship["target_id"],
            "assessment": "Supported" if index % 7 else "Unverified",
            "valid_from": "2027-01-01",
            "valid_to": "",
        })
        evidence.append({
            "assertion_id": assertion_id,
            "source_id": sources[index % len(sources)]["id"],
        })

    write_csv("nodes.csv", nodes, ["id", "label", "name", "synthetic"])
    write_csv("relationships.csv", relationships, [
        "id", "source_id", "type", "target_id", "valid_from",
        "valid_to", "synthetic",
    ])
    write_csv("sources.csv", sources, list(sources[0]))
    write_csv("assertions.csv", assertions, list(assertions[0]))
    write_csv("evidence.csv", evidence, ["assertion_id", "source_id"])

    manifest = {
        "dataset": "HBL-01",
        "version": "1.0.0",
        "seed": SEED,
        "domain_nodes": len(nodes),
        "domain_relationships": len(relationships),
        "sources": len(sources),
        "assertions": len(assertions),
        "sha256": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(OUT.glob("*.csv"))
        },
    }
    (OUT / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"Generated: {manifest['domain_nodes']} nodes, "
        f"{manifest['domain_relationships']} relationships"
    )


if __name__ == "__main__":
    build()
