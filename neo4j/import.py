
"""
Import the Harborlight HBL-01 dataset into Neo4j.

Required environment variables:
    NEO4J_URI
    NEO4J_USER
    NEO4J_PASSWORD

The variables are loaded from the .env file in the project root.

Usage:
    python neo4j/import.py
"""

import csv
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase


# Project configuration
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
CONSTRAINTS_FILE = Path(__file__).with_name("constraints.cypher")
ENV_FILE = ROOT / ".env"

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

ALLOWED_RELATIONSHIP_TYPES = {
    "WORKS_FOR",
    "MANAGES",
    "REGISTERED_AT",
    "OPERATES",
    "PARTICIPATED_IN",
    "OCCURRED_AT",
    "INVOLVES_VEHICLE",
    "SENT",
    "RECEIVED",
    "ORIGINATED_AT",
    "DESTINED_FOR",
    "HOLDS_ACCOUNT",
    "DEBITED_FROM",
    "CREDITED_TO",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


def load_configuration() -> tuple[str, str, str]:
    """Load and validate Neo4j connection settings."""
    if not ENV_FILE.is_file():
        raise FileNotFoundError(
            f"Environment file not found: {ENV_FILE}"
        )

    load_dotenv(ENV_FILE)

    required = (
        "NEO4J_URI",
        "NEO4J_USER",
        "NEO4J_PASSWORD",
    )

    missing = [key for key in required if not os.getenv(key)]

    if missing:
        raise RuntimeError(
            "Missing environment variables: "
            + ", ".join(missing)
        )

    return (
        os.environ["NEO4J_URI"],
        os.environ["NEO4J_USER"],
        os.environ["NEO4J_PASSWORD"],
    )


def read_csv(filename: str) -> list[dict[str, str]]:
    """Read a CSV file from the data directory."""
    path = DATA_DIR / filename

    if not path.is_file():
        raise FileNotFoundError(f"CSV file not found: {path}")

    with path.open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def create_constraints(driver) -> None:
    """Create Neo4j constraints from the Cypher file."""
    logger.info("Creating database constraints...")

    statements = CONSTRAINTS_FILE.read_text(
        encoding="utf-8"
    ).split(";")

    for statement in statements:
        statement = statement.strip()

        if statement:
            driver.execute_query(statement)

    logger.info("Database constraints ready.")


def import_nodes(driver) -> None:
    """Import domain entities into Neo4j."""
    rows = read_csv("nodes.csv")

    for row in rows:
        label = row["label"]

        if label not in ALLOWED_LABELS:
            raise ValueError(f"Unsupported node label: {label}")

        query = f"""
        MERGE (n:Entity:{label} {{id: $id}})
        SET n.name = $name,
            n.synthetic = true
        """

        driver.execute_query(
            query,
            id=row["id"],
            name=row["name"],
        )

    logger.info("Imported %d nodes.", len(rows))


def import_relationships(driver) -> None:
    """Import relationships between domain entities."""
    rows = read_csv("relationships.csv")

    for row in rows:
        relationship_type = row["type"]

        if relationship_type not in ALLOWED_RELATIONSHIP_TYPES:
            raise ValueError(
                f"Unsupported relationship type: {relationship_type}"
            )

        query = f"""
        MATCH (a:Entity {{id: $source}})
        MATCH (b:Entity {{id: $target}})
        MERGE (a)-[r:{relationship_type} {{id: $id}}]->(b)
        SET r.valid_from = date($date),
            r.synthetic = true
        """

        driver.execute_query(
            query,
            source=row["source_id"],
            target=row["target_id"],
            id=row["id"],
            date=row["valid_from"],
        )

    logger.info("Processed %d relationships.", len(rows))


def import_sources(driver) -> None:
    """Import source metadata."""
    rows = read_csv("sources.csv")

    query = """
    MERGE (s:Source {id: $id})
    SET s += $props
    """

    for row in rows:
        driver.execute_query(
            query,
            id=row["id"],
            props=row,
        )

    logger.info("Imported %d sources.", len(rows))


def import_assertions(driver) -> None:
    """Import assertions and connect them to domain entities."""
    rows = read_csv("assertions.csv")

    query = """
    MATCH (subject:Entity {id: $subject})
    MATCH (object:Entity {id: $object})

    MERGE (a:Assertion {id: $id})
    SET a.predicate = $predicate,
        a.assessment = $assessment,
        a.valid_from = date($date)

    MERGE (a)-[:ABOUT_SUBJECT]->(subject)
    MERGE (a)-[:ABOUT_OBJECT]->(object)
    """

    for row in rows:
        driver.execute_query(
            query,
            id=row["id"],
            predicate=row["predicate"],
            assessment=row["assessment"],
            date=row["valid_from"],
            subject=row["subject_id"],
            object=row["object_id"],
        )

    logger.info("Processed %d assertions.", len(rows))


def import_evidence(driver) -> None:
    """Connect assertions to their supporting sources."""
    rows = read_csv("evidence.csv")

    query = """
    MATCH (a:Assertion {id: $assertion_id})
    MATCH (s:Source {id: $source_id})
    MERGE (a)-[:SUPPORTED_BY]->(s)
    """

    for row in rows:
        driver.execute_query(
            query,
            assertion_id=row["assertion_id"],
            source_id=row["source_id"],
        )

    logger.info("Processed %d evidence records.", len(rows))


def main() -> None:
    """Execute the Harborlight import pipeline."""
    uri, username, password = load_configuration()

    logger.info("Starting Harborlight HBL-01 import...")

    with GraphDatabase.driver(
        uri,
        auth=(username, password),
    ) as driver:
        driver.verify_connectivity()
        logger.info("Connected to Neo4j.")

        create_constraints(driver)
        import_nodes(driver)
        import_relationships(driver)
        import_sources(driver)
        import_assertions(driver)
        import_evidence(driver)

    logger.info("Harborlight import completed successfully.")


if __name__ == "__main__":
    main()
