
"""
Validate synthetic datasets for the Graph Intelligence Series.

Supported datasets:
    HBL-01 through HBL-06

Checks:
    - Expected dataset counts
    - Unique identifiers
    - Valid entity labels and relationship types
    - Relationship referential integrity
    - Assertion-to-relationship consistency
    - Evidence attribution integrity
    - Manifest metadata and SHA-256 checksums

Usage:
    python -m unittest discover -s tests -v
    python tests/test_dataset.py
"""

import csv
import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

EXPECTED_PROFILES = {
    "hbl-01": {"nodes": 150, "relationships": 350, "sources": 50},
    "hbl-02": {"nodes": 300, "relationships": 900, "sources": 100},
    "hbl-03": {"nodes": 450, "relationships": 1800, "sources": 150},
    "hbl-04": {"nodes": 600, "relationships": 3000, "sources": 200},
    "hbl-05": {"nodes": 900, "relationships": 6000, "sources": 300},
    "hbl-06": {"nodes": 1200, "relationships": 10000, "sources": 400},
}

ALLOWED_LABELS = {
    "Person",
    "Organization",
    "Location",
    "Vehicle",
    "Event",
    "Shipment",
    "Transaction",
    "Account",
}

RELATIONSHIP_RULES = {
    "WORKS_FOR": ("Person", "Organization"),
    "MANAGES": ("Person", "Organization"),
    "REGISTERED_AT": ("Organization", "Location"),
    "OPERATES": ("Organization", "Vehicle"),
    "PARTICIPATED_IN": ("Person", "Event"),
    "OCCURRED_AT": ("Event", "Location"),
    "INVOLVES_VEHICLE": ("Event", "Vehicle"),
    "SENT": ("Organization", "Shipment"),
    "RECEIVED": ("Organization", "Shipment"),
    "ORIGINATED_AT": ("Shipment", "Location"),
    "DESTINED_FOR": ("Shipment", "Location"),
    "HOLDS_ACCOUNT": ("Organization", "Account"),
    "DEBITED_FROM": ("Transaction", "Account"),
    "CREDITED_TO": ("Transaction", "Account"),
}

CSV_FILES = (
    "nodes.csv",
    "relationships.csv",
    "sources.csv",
    "assertions.csv",
    "evidence.csv",
)


def read_csv(dataset_dir: Path, filename: str) -> list[dict[str, str]]:
    """Read a dataset CSV file."""
    path = dataset_dir / filename

    if not path.is_file():
        raise FileNotFoundError(f"Missing CSV file: {path}")

    with path.open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def read_manifest(dataset_dir: Path) -> dict:
    """Read the dataset manifest."""
    path = dataset_dir / "manifest.json"

    if not path.is_file():
        raise FileNotFoundError(f"Missing manifest: {path}")

    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    """Calculate the SHA-256 checksum of a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


class DatasetTests(unittest.TestCase):
    """Validate all Harborlight dataset profiles."""

    @classmethod
    def setUpClass(cls) -> None:
        """Load all datasets before running tests."""
        cls.datasets = {}

        for dataset_id in EXPECTED_PROFILES:
            dataset_dir = DATA_DIR / dataset_id

            if not dataset_dir.is_dir():
                raise FileNotFoundError(
                    f"Dataset directory not found: {dataset_dir}. "
                    "Run python generator/generate.py first."
                )

            cls.datasets[dataset_id] = {
                "directory": dataset_dir,
                "nodes": read_csv(dataset_dir, "nodes.csv"),
                "relationships": read_csv(
                    dataset_dir, "relationships.csv"
                ),
                "sources": read_csv(dataset_dir, "sources.csv"),
                "assertions": read_csv(
                    dataset_dir, "assertions.csv"
                ),
                "evidence": read_csv(dataset_dir, "evidence.csv"),
                "manifest": read_manifest(dataset_dir),
            }

    def test_expected_counts(self) -> None:
        """Verify record counts against the dataset profiles."""
        for dataset_id, data in self.datasets.items():
            with self.subTest(dataset=dataset_id):
                profile = EXPECTED_PROFILES[dataset_id]

                self.assertEqual(
                    len(data["nodes"]), profile["nodes"]
                )
                self.assertEqual(
                    len(data["relationships"]),
                    profile["relationships"],
                )
                self.assertEqual(
                    len(data["sources"]), profile["sources"]
                )
                self.assertEqual(
                    len(data["assertions"]),
                    profile["relationships"],
                )
                self.assertEqual(
                    len(data["evidence"]),
                    profile["relationships"],
                )

    def test_unique_identifiers(self) -> None:
        """Verify unique identifiers within each record category."""
        for dataset_id, data in self.datasets.items():
            with self.subTest(dataset=dataset_id):
                for category in (
                    "nodes",
                    "relationships",
                    "sources",
                    "assertions",
                ):
                    identifiers = [
                        row["id"] for row in data[category]
                    ]

                    self.assertEqual(
                        len(identifiers),
                        len(set(identifiers)),
                        f"Duplicate IDs in {dataset_id}/{category}",
                    )

                evidence_pairs = [
                    (row["assertion_id"], row["source_id"])
                    for row in data["evidence"]
                ]

                self.assertEqual(
                    len(evidence_pairs),
                    len(set(evidence_pairs)),
                    f"Duplicate evidence links in {dataset_id}",
                )

    def test_node_labels(self) -> None:
        """Verify that all domain entities use supported labels."""
        for dataset_id, data in self.datasets.items():
            with self.subTest(dataset=dataset_id):
                self.assertTrue(
                    all(
                        row["label"] in ALLOWED_LABELS
                        for row in data["nodes"]
                    )
                )

    def test_relationship_integrity(self) -> None:
        """Verify relationship endpoints and label compatibility."""
        for dataset_id, data in self.datasets.items():
            with self.subTest(dataset=dataset_id):
                node_labels = {
                    row["id"]: row["label"]
                    for row in data["nodes"]
                }

                relationship_keys = set()

                for relationship in data["relationships"]:
                    source_id = relationship["source_id"]
                    target_id = relationship["target_id"]
                    relationship_type = relationship["type"]

                    self.assertIn(source_id, node_labels)
                    self.assertIn(target_id, node_labels)
                    self.assertIn(
                        relationship_type, RELATIONSHIP_RULES
                    )

                    expected_source, expected_target = (
                        RELATIONSHIP_RULES[relationship_type]
                    )

                    self.assertEqual(
                        node_labels[source_id], expected_source
                    )
                    self.assertEqual(
                        node_labels[target_id], expected_target
                    )

                    key = (
                        source_id,
                        relationship_type,
                        target_id,
                    )

                    self.assertNotIn(
                        key,
                        relationship_keys,
                        f"Duplicate relationship in {dataset_id}: {key}",
                    )
                    relationship_keys.add(key)

    def test_assertion_integrity(self) -> None:
        """Verify assertions match generated domain relationships."""
        for dataset_id, data in self.datasets.items():
            with self.subTest(dataset=dataset_id):
                relationship_keys = {
                    (
                        row["source_id"],
                        row["type"],
                        row["target_id"],
                    )
                    for row in data["relationships"]
                }

                assertion_keys = set()

                for assertion in data["assertions"]:
                    key = (
                        assertion["subject_id"],
                        assertion["predicate"],
                        assertion["object_id"],
                    )

                    self.assertIn(
                        key,
                        relationship_keys,
                        f"Orphan assertion in {dataset_id}: {key}",
                    )
                    self.assertNotIn(key, assertion_keys)
                    assertion_keys.add(key)

                self.assertEqual(
                    assertion_keys, relationship_keys
                )

    def test_evidence_integrity(self) -> None:
        """Verify every assertion has exactly one valid source link."""
        for dataset_id, data in self.datasets.items():
            with self.subTest(dataset=dataset_id):
                assertion_ids = {
                    row["id"] for row in data["assertions"]
                }
                source_ids = {
                    row["id"] for row in data["sources"]
                }

                evidence_counts = {
                    assertion_id: 0
                    for assertion_id in assertion_ids
                }

                for evidence in data["evidence"]:
                    assertion_id = evidence["assertion_id"]
                    source_id = evidence["source_id"]

                    self.assertIn(assertion_id, assertion_ids)
                    self.assertIn(source_id, source_ids)

                    evidence_counts[assertion_id] += 1

                self.assertTrue(
                    all(count == 1 for count in evidence_counts.values()),
                    f"Invalid evidence coverage in {dataset_id}",
                )

    def test_manifest_counts(self) -> None:
        """Verify manifest counts match the generated CSV files."""
        for dataset_id, data in self.datasets.items():
            with self.subTest(dataset=dataset_id):
                manifest = data["manifest"]

                domain_nodes = len(data["nodes"])
                domain_relationships = len(data["relationships"])
                sources = len(data["sources"])
                assertions = len(data["assertions"])
                evidence = len(data["evidence"])

                self.assertEqual(
                    manifest["dataset"], dataset_id.upper()
                )
                self.assertEqual(
                    manifest["seed"],
                    202701 + int(dataset_id.split("-")[1]) - 1,
                )
                self.assertEqual(
                    manifest["domain_nodes"], domain_nodes
                )
                self.assertEqual(
                    manifest["domain_relationships"],
                    domain_relationships,
                )
                self.assertEqual(
                    manifest["sources"], sources
                )
                self.assertEqual(
                    manifest["assertions"], assertions
                )
                self.assertEqual(
                    manifest["evidence_links"], evidence
                )
                self.assertEqual(
                    manifest["total_nodes"],
                    domain_nodes + sources + assertions,
                )
                self.assertEqual(
                    manifest["total_relationships"],
                    domain_relationships + 2 * assertions + evidence,
                )

    def test_manifest_checksums(self) -> None:
        """Verify SHA-256 checksums for every generated CSV file."""
        for dataset_id, data in self.datasets.items():
            with self.subTest(dataset=dataset_id):
                manifest = data["manifest"]
                dataset_dir = data["directory"]

                self.assertEqual(
                    set(manifest["sha256"]),
                    set(CSV_FILES),
                )

                for filename in CSV_FILES:
                    expected_checksum = manifest["sha256"][filename]
                    actual_checksum = sha256(dataset_dir / filename)

                    self.assertEqual(
                        actual_checksum,
                        expected_checksum,
                        f"Checksum mismatch: {dataset_id}/{filename}",
                    )

    def test_core_entity_consistency(self) -> None:
        """Verify that core entity identities remain stable."""
        baseline = {
            row["id"]: (row["label"], row["name"])
            for row in self.datasets["hbl-01"]["nodes"]
        }

        for dataset_id, data in self.datasets.items():
            with self.subTest(dataset=dataset_id):
                current = {
                    row["id"]: (row["label"], row["name"])
                    for row in data["nodes"]
                }

                for entity_id, expected in baseline.items():
                    self.assertIn(entity_id, current)
                    self.assertEqual(current[entity_id], expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
