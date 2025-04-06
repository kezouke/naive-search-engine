#!/usr/bin/env python3
import sys
from cassandra.cluster import Cluster

cluster = Cluster(["cassandra-server"])
session = cluster.connect()
session.execute("USE search_keyspace;")

# Create tables if not exist
session.execute("""
CREATE TABLE IF NOT EXISTS terms (
    term text PRIMARY KEY,
    df int
);
""")

session.execute("""
CREATE TABLE IF NOT EXISTS postings (
    term text,
    doc_id text,
    tf int,
    PRIMARY KEY (term, doc_id)
);
""")

current_term = None
doc_map = {}  # doc_id -> tf

def flush_term(term, doc_map):
    """
    When we move to a new term, flush the aggregated results to Cassandra.
    """
    df = len(doc_map)  # number of distinct docs that contain this term

    # Insert the df into 'terms' table
    session.execute(
        "INSERT INTO terms (term, df) VALUES (%s, %s)",
        (term, df)
    )

    # Insert all postings
    for doc_id, tf in doc_map.items():
        session.execute(
            "INSERT INTO postings (term, doc_id, tf) VALUES (%s, %s, %s)",
            (term, doc_id, tf)
        )

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue

    parts = line.split("\t")
    if len(parts) != 3:
        continue
    term, doc_id, tf_str = parts
    tf = int(tf_str)

    if current_term is None:
        current_term = term
        doc_map = {}

    # If we've reached a new term, flush the old one
    if term != current_term:
        flush_term(current_term, doc_map)
        current_term = term
        doc_map = {}

    # Aggregate
    doc_map[doc_id] = doc_map.get(doc_id, 0) + tf

# Flush the final term
if current_term is not None:
    flush_term(current_term, doc_map)

cluster.shutdown()
