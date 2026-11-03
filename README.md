# Operation Harborlight

**Synthetic Graph Intelligence Datasets for the Graph Intelligence Series**

Operation Harborlight is a fully synthetic, reproducible graph intelligence training environment for a six-book educational series covering Neo4j, Cypher, social network analysis, Python, advanced graph analytics, and intelligence reporting.

**All people, organizations, locations, events, transactions, and relationships are fictional.** These datasets contain no real investigative intelligence. A network connection, centrality score, or shared address is not evidence of wrongdoing.

## Dataset series

| Dataset | Book | Focus |
|---|---|---|
| HBL-01 | Graph Intelligence Fundamentals | Graph modeling, Neo4j, and provenance |
| HBL-02 | Cypher for Intelligence Analysis | Queries, patterns, and traversals |
| HBL-03 | Social Network Analysis for Intelligence Professionals | Centrality and communities |
| HBL-04 | Python for Graph Intelligence | Automation and graph processing |
| HBL-05 | Advanced Graph Analytics for Investigations | Advanced analytical workflows |
| HBL-06 | From Graph Data to Intelligence Products | Interpretation and reporting |

**Status:** HBL-01 is the validated baseline. HBL-02 through HBL-06 use provisional scaling profiles for test datasets; their final investigative scenarios and specifications may change. Core entity identifiers are stable, but later datasets are not yet guaranteed to preserve every earlier relationship.

## Repository structure

```text
graph-intelligence-harborlight/
├── README.md
├── LICENSE
├── .gitignore
├── .env.example
├── requirements.txt
├── data/
│   ├── hbl-01/
│   ├── hbl-02/
│   ├── hbl-03/
│   ├── hbl-04/
│   ├── hbl-05/
│   └── hbl-06/
├── generator/
│   └── generate.py
├── neo4j/
│   ├── import.py
│   └── constraints.cypher
└── tests/
    └── test_dataset.py
```

Each generated `data/hbl-XX/` directory contains:

| File | Purpose |
|---|---|
| `nodes.csv` | Domain entities, labels, and names |
| `relationships.csv` | Directed, typed domain relationships |
| `sources.csv` | Fictional source metadata |
| `assertions.csv` | Assertions about entity relationships |
| `evidence.csv` | Assertion-to-source attribution |
| `manifest.json` | Dataset metadata, counts, seeds, and SHA-256 checksums |

## Current dataset profiles

| Dataset | Domain nodes | Domain relationships | Sources | Assertions | Total Neo4j nodes | Total Neo4j relationships |
|---|---:|---:|---:|---:|---:|---:|
| HBL-01 | 150 | 350 | 50 | 350 | 550 | 1,400 |
| HBL-02 | 300 | 900 | 100 | 900 | 1,300 | 3,600 |
| HBL-03 | 450 | 1,800 | 150 | 1,800 | 2,400 | 7,200 |
| HBL-04 | 600 | 3,000 | 200 | 3,000 | 3,800 | 12,000 |
| HBL-05 | 900 | 6,000 | 300 | 6,000 | 7,200 | 24,000 |
| HBL-06 | 1,200 | 10,000 | 400 | 10,000 | 11,600 | 40,000 |

These are generator targets, not independently verified database counts for all six datasets. **HBL-01 has been verified in Neo4j: 550 nodes and 1,400 relationships.**

## Requirements

- Python 3.10+
- Neo4j 5.x or a compatible current release
- The official Neo4j Python driver and `python-dotenv` for database imports

The dataset generator itself uses only the Python standard library.

```bash
python -m pip install 'neo4j>=5,<7' 'python-dotenv>=1,<2'
```

If a maintained `requirements.txt` exists, you can instead run `python -m pip install -r requirements.txt`.

## Generate datasets

```bash
# Generate all six datasets
python generator/generate.py

# Generate one dataset
python generator/generate.py --dataset hbl-01
python generator/generate.py --dataset hbl-06
```

Generation uses dataset-specific deterministic seeds, starting at `202701` for HBL-01. Each `manifest.json` records the seed, version, counts, and SHA-256 checksums. Re-running generation overwrites generated files; preserve published versions with Git tags or GitHub Releases.

## Import into Neo4j

Create a `.env` file in the project root:

```dotenv
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=replace_with_your_password
HARBORLIGHT_DATASET=hbl-01
```

Use the URI supplied by Neo4j Aura if connecting to Aura. **Never commit `.env` or real credentials.** Commit only `.env.example` with placeholder values.

The importer must be configured to read from `data/<dataset-id>/`, using `HARBORLIGHT_DATASET` to select the dataset.

```bash
python neo4j/import.py
```

The import process creates constraints, imports domain nodes and relationships, imports sources and assertions, and connects assertions to subjects, objects, and supporting sources. It uses `MERGE` for repeatable imports but does not remove obsolete records.

**Import each dataset into a separate database, or reset a dedicated test database before switching datasets.** Identifiers overlap across dataset versions, so their counts cannot simply be added together.

To delete all graph data in the selected **test** database:

```cypher
MATCH (n)
DETACH DELETE n;
```

**Warning:** This operation is destructive and does not remove constraints or indexes.

## Verify the import

Total nodes and relationships:

```cypher
MATCH (n)
WITH count(n) AS total_nodes
MATCH ()-[r]->()
RETURN total_nodes, count(r) AS total_relationships;
```

For HBL-01, expect `550` nodes and `1400` relationships.

Breakdown by category:

```cypher
MATCH (n)
RETURN
    count(n) AS total_nodes,
    count(CASE WHEN n:Entity THEN 1 END) AS entities,
    count(CASE WHEN n:Source THEN 1 END) AS sources,
    count(CASE WHEN n:Assertion THEN 1 END) AS assertions;
```

Relationship counts:

```cypher
MATCH ()-[r]->()
RETURN type(r) AS relationship_type, count(r) AS relationship_count
ORDER BY relationship_count DESC;
```

Visualize a sample of the domain graph:

```cypher
MATCH (a:Entity)-[r]->(b:Entity)
RETURN a, r, b
LIMIT 50;
```

## Graph data model

The domain layer uses eight entity labels: `Person`, `Organization`, `Location`, `Vehicle`, `Event`, `Shipment`, `Transaction`, and `Account`. Each domain node also has the `Entity` label.

Examples of domain relationships:

```cypher
(:Person)-[:WORKS_FOR]->(:Organization)
(:Person)-[:MANAGES]->(:Organization)
(:Organization)-[:REGISTERED_AT]->(:Location)
(:Organization)-[:OPERATES]->(:Vehicle)
(:Person)-[:PARTICIPATED_IN]->(:Event)
(:Organization)-[:SENT]->(:Shipment)
(:Shipment)-[:DESTINED_FOR]->(:Location)
(:Transaction)-[:DEBITED_FROM]->(:Account)
```

The provenance layer keeps assertions separate from domain relationships:

```cypher
(:Assertion)-[:ABOUT_SUBJECT]->(:Entity)
(:Assertion)-[:ABOUT_OBJECT]->(:Entity)
(:Assertion)-[:SUPPORTED_BY]->(:Source)
```

The current generator creates one assertion and one evidence link per domain relationship. Assessments such as `Supported` and `Unverified` are synthetic training attributes, not verified investigative conclusions.

## Example Cypher queries

Employment relationships:

```cypher
MATCH (p:Person)-[:WORKS_FOR]->(o:Organization)
RETURN p.name AS person, o.name AS organization
ORDER BY person
LIMIT 20;
```

Organizations sharing an address:

```cypher
MATCH (o1:Organization)-[:REGISTERED_AT]->(l:Location)
      <-[:REGISTERED_AT]-(o2:Organization)
WHERE o1.id < o2.id
RETURN o1.name AS organization_1,
       o2.name AS organization_2,
       l.name AS shared_location;
```

HBL-01 intentionally connects Meridian Freight Ltd and Bluewater Trade Services to Meridian Business Center. A shared address alone does not imply misconduct.

Source attribution:

```cypher
MATCH (a:Assertion)-[:SUPPORTED_BY]->(s:Source)
RETURN a.id AS assertion_id,
       a.predicate AS predicate,
       a.assessment AS assessment,
       s.title AS source
LIMIT 20;
```

Unverified assertions:

```cypher
MATCH (a:Assertion {assessment: 'Unverified'})
RETURN a.id AS assertion_id, a.predicate AS predicate
LIMIT 25;
```

## Data integrity and testing

Recommended checks include unique IDs, valid labels and relationship types, referential integrity, assertion and evidence coverage, expected counts, and CSV checksums.

If `tests/test_dataset.py` has been updated for the six-directory layout, run:

```bash
python -m unittest discover -s tests -v
```

The presence of a test script does not imply that all six datasets have been validated; check the test output before publishing results.

## Analytical limitations

Operation Harborlight is an educational simulation, not an operational intelligence system. Graph patterns are not statistically calibrated to real-world networks. Source reliability and credibility codes are illustrative, not probabilities. Assertions are not independent proof of truth. Source independence, hidden ground truth, and comprehensive temporal reconstruction are not yet fully modeled. Larger datasets currently emphasize scale rather than finalized, book-specific investigative narratives.

Interpret analytical results with attention to provenance, uncertainty, missing information, and alternative explanations.

## Versioning and releases

Use release tags such as `hbl-01-v1.0.0` and `hbl-02-v1.0.0`. Once a dataset is published for a book, preserve its exact files and generator version. Publish corrections under new version tags rather than silently changing existing releases.

## License

This repository is distributed under the **GNU license specified in the repository's `LICENSE` file**. Consult that file for the exact license family, version, permissions, and obligations. If the selected license is the GNU General Public License, identify the precise variant (for example, `GPL-3.0-only` or `GPL-3.0-or-later`) before publishing a formal SPDX identifier.

The datasets are entirely synthetic. Their fictional nature does not override the terms of the repository's license.

## Educational purpose

Operation Harborlight supports reproducible training in graph modeling, Neo4j, Cypher, source provenance, social network analysis, Python, advanced analytics, and intelligence reporting.

**Fictional data. Reproducible methods. Evidence-aware analysis.**
