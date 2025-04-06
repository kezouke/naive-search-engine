#!/usr/bin/env python3
import sys
import traceback
import time
from cassandra.cluster import Cluster

def connect_cassandra():
    for attempt in range(5):
        try:
            sys.stderr.write(f"Attempting Cassandra connection (try {attempt+1})...\n")
            cluster = Cluster(['cassandra-server'], port=9042)
            session = cluster.connect()
            session.execute("CREATE KEYSPACE IF NOT EXISTS search_keyspace "
                            "WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};")
            session.set_keyspace('search_keyspace')
            sys.stderr.write("Successfully connected to Cassandra!\n")
            return cluster, session
        except Exception as e:
            sys.stderr.write(f"Connection attempt {attempt+1} failed: {e}\n")
            time.sleep(5)
    # If we still fail after 5 attempts, raise
    raise RuntimeError("Could not connect to Cassandra after 5 retries.")

try:
    cluster, session = connect_cassandra()

    session.execute("""
        CREATE TABLE IF NOT EXISTS docs (
            doc_id text PRIMARY KEY,
            doc_title text,
            doc_length int
        )
    """)
    session.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            id text PRIMARY KEY,
            doc_count int,
            total_length int,
            avg_doc_length float
        )
    """)

    doc_count = 0
    total_length = 0

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t")
        # Expect: DOC doc_id doc_title doc_length
        if len(parts) != 4 or parts[0] != "DOC":
            sys.stderr.write(f"Skipping malformed line: {line}\n")
            continue
        _, doc_id, doc_title, doc_len_str = parts
        try:
            doc_len = int(doc_len_str)
        except ValueError:
            continue

        session.execute("""
            INSERT INTO docs (doc_id, doc_title, doc_length)
            VALUES (%s, %s, %s)
        """, (doc_id, doc_title, doc_len))

        doc_count += 1
        total_length += doc_len

    if doc_count > 0:
        avg_doc_length = total_length / doc_count
        session.execute("""
            INSERT INTO stats (id, doc_count, total_length, avg_doc_length)
            VALUES ('global', %s, %s, %s)
        """, (doc_count, total_length, avg_doc_length))

    cluster.shutdown()

except Exception as ex:
    sys.stderr.write(f"Reducer fatal error: {ex}\n")
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
