from pathvalidate import sanitize_filename
from pyspark.sql import SparkSession, functions as F
import os

spark = SparkSession.builder \
    .appName("data preparation") \
    .master("local[2]") \
    .config("spark.driver.memory", "4g") \
    .config("spark.executor.memory", "4g") \
    .config("spark.sql.parquet.enableVectorizedReader", "true") \
    .config("spark.hadoop.fs.defaultFS", "hdfs://cluster-master:9000") \
    .getOrCreate()

try:
    # 1. Read with column pruning
    df = spark.read.parquet("/a.parquet").select("id", "title", "text")

    # 2. Efficient sampling
    n = 1000
    sampled_df = df.orderBy(F.rand(seed=0)).limit(n)

    # 3. Distributed file creation
    os.makedirs("data", exist_ok=True)


    def create_docs(partition):
        for row in partition:
            doc_id = str(row["id"])
            doc_title = row["title"].replace(" ", "_")
            safe_filename = f"{sanitize_filename(doc_id)}_{sanitize_filename(doc_title)}.txt"
            with open(f"data/{safe_filename}", "w", encoding="utf-8") as f:
                f.write(row["text"])


    sampled_df.foreachPartition(create_docs)

    # 4. Write TSV without coalesce
    (sampled_df
     .select(
        F.col("id").cast("string").alias("doc_id"),
        F.col("title").alias("doc_title"),
        F.col("text").alias("doc_text")
    )
     .write
     .option("sep", "\t")
     .csv("/index/data", mode="overwrite")
     )

finally:
    spark.stop()