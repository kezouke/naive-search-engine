#!/usr/bin/env python3
import sys
import math
from pyspark.sql import SparkSession, functions as F

# -------------------------------------------------------------------
# BM25 Hyperparameters
K1 = 1.2
B = 0.75

def tokenize_query(query_str):
    """Very naive tokenizer: split by whitespace."""
    return query_str.lower().split()

if __name__ == "__main__":
    # 1) Read user query from command line arguments
    #    e.g. user calls:  ./search.sh "dogs and cats"
    #    sys.argv[0] = 'query.py', sys.argv[1] = 'dogs and cats'
    query_terms = []
    if len(sys.argv) > 1:
        # Join everything after sys.argv[0] into a single string, then tokenize
        raw_query = " ".join(sys.argv[1:])
        query_terms = tokenize_query(raw_query)
    else:
        # If no arguments passed, fallback or exit
        print("No query given. Usage: spark-submit query.py \"your query\"")
        sys.exit(0)

    if not query_terms:
        print("No valid query terms found.")
        sys.exit(0)

    # 2) Initialize Spark Session
    #    IMPORTANT: We configure the Spark Cassandra connector via .config(...)
    # Initialize Spark Session with proper YARN configuration
    spark = SparkSession.builder \
        .appName("BM25_Ranker") \
        .config("spark.driver.memory", "2g") \
        .config("spark.executor.memory", "2g") \
        .config("spark.yarn.am.memory", "1g") \
        .config("spark.hadoop.fs.defaultFS", "hdfs://cluster-master:9000") \
        .config("spark.cassandra.connection.host", "cassandra-server") \
        .config("spark.cassandra.connection.port", "9042") \
        .config("spark.sql.extensions", "com.datastax.spark.connector.CassandraSparkExtensions") \
        .getOrCreate()

    # 3) Read global stats from Cassandra
    #    We assume the table stats has a row with primary key: id='global'
    #    containing doc_count, total_length, avg_doc_length
    stats_df = (spark.read
        .format("org.apache.spark.sql.cassandra")
        .options(table="stats", keyspace="search_keyspace")
        .load()
        .filter("id = 'global'")  # pick the single row that has global stats
    )

    # Collect that row into driver memory
    row = stats_df.collect()[0]
    doc_count = row["doc_count"]       # total number of documents in the corpus
    avg_doc_length = row["avg_doc_length"]  # average doc length in the corpus

    # 4) Read postings and terms tables from Cassandra
    #    postings: (term, doc_id, tf)
    #    terms: (term, df)
    #    docs: (doc_id, doc_title, doc_length)
    postings_df = (spark.read
        .format("org.apache.spark.sql.cassandra")
        .options(table="postings", keyspace="search_keyspace")
        .load()
    )
    terms_df = (spark.read
        .format("org.apache.spark.sql.cassandra")
        .options(table="terms", keyspace="search_keyspace")
        .load()
    )
    docs_df = (spark.read
        .format("org.apache.spark.sql.cassandra")
        .options(table="docs", keyspace="search_keyspace")
        .load()
    )

    # 5) Filter postings to only rows whose 'term' is in the user query
    #    This drastically reduces data we handle if the vocabulary is large.
    #    Then join with `terms_df` to get df(term).
    query_terms_broadcast = list(set(query_terms))  # unique terms
    postings_filtered_df = postings_df.filter(F.col("term").isin(query_terms_broadcast))

    # Join postings with terms on "term", so we can get df (document frequency)
    joined_df = postings_filtered_df.join(
        terms_df,
        on="term",
        how="inner"  # Only terms that actually exist in the index
    )

    # Also join with docs to get doc_length and doc_title
    joined_df = joined_df.join(
        docs_df,
        on="doc_id",
        how="inner"
    )
    # After these joins, each row has:
    #  term, tf, df, doc_id, doc_length, doc_title

    # 6) Create a UDF or use Spark SQL functions for the BM25 formula:
    #
    #   BM25(q,d) = sum over each term t in q of:
    #     log( (N - df(t) + 0.5) / (df(t) + 0.5) ) *
    #       ((k1+1)*tf(t,d) / (k1*(1 - b + b*(dl(d)/avg_dl)) + tf(t,d)) )
    #
    #   Where:
    #     N = doc_count
    #     df(t) = # docs containing term t
    #     tf(t,d) = # frequency of term t in doc d
    #     dl(d) = doc_length(d)

    def bm25_score(df, tf, doc_length):
        """Compute BM25 for a single term-document pair."""
        # IDF part
        idf_num = (doc_count - df + 0.5)
        idf_den = (df + 0.5)
        idf = math.log((idf_num / idf_den), 2)  # base-2 or natural log both are common

        # TF part
        numerator = (K1 + 1.0) * tf
        denominator = K1 * (1.0 - B + B * (float(doc_length) / float(avg_doc_length))) + tf
        return float(idf * (numerator / denominator))

    # Build a Spark UDF
    bm25_udf = F.udf(lambda df, tf, dl: bm25_score(df, tf, dl), "float")

    # 7) Add a column "bm25" for each (term, doc_id).
    #    Then we want to sum over all terms in the user query for each doc.
    scored_df = joined_df.withColumn(
        "bm25",
        bm25_udf(F.col("df"), F.col("tf"), F.col("doc_length"))
    )

    # 8) Group by doc_id, doc_title, then sum the BM25 across all matched terms
    final_scores_df = (scored_df
        .groupBy("doc_id", "doc_title")
        .agg(F.sum("bm25").alias("score"))
        .orderBy(F.desc("score"))
        .limit(10)
    )

    # 9) Collect or show the top 10
    top_docs = final_scores_df.collect()

    print("\n=== TOP 10 SEARCH RESULTS ===")
    for row in top_docs:
        print(f"DocID={row['doc_id']}  Title={row['doc_title'][:60]}  Score={row['score']:.4f}")

    spark.stop()
