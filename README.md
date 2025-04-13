# Naive Search Engine Implementation

A distributed search engine implementation using Spark, Hadoop, and Cassandra with BM25 ranking.

## Methodology

### Architecture Components
1. **Data Preparation**:
   - Samples 1000 documents from Parquet files
   - Stores raw text files in HDFS
   - Creates TSV metadata using Spark distributed processing
   - Uses column pruning and efficient sampling for performance

2. **Indexing Pipeline**:
   - Two MapReduce jobs:
     - **Job 1**: Calculates document statistics (doc_length, total_count)
     - **Job 2**: Builds inverted index (term frequencies)
   - Stores results in Cassandra:
     - `docs`: Document metadata
     - `terms`: Document frequencies
     - `postings`: Term frequencies
     - `stats`: Global corpus statistics

3. **Query Processing**:
   - BM25 ranking algorithm implementation in Spark
   - Cassandra for low-latency lookups
   - Distributed scoring across Spark executors
   - Top-10 results with relevance scores

### Key Design Choices
- **Cassandra Storage**: Chosen for write-optimized operations during indexing and low-latency reads during querying
- **Spark SQL**: Enables efficient joins and aggregations for BM25 calculation
- **BM25 Ranking**: Better than TF-IDF for handling document length normalization
- **HDFS**: Reliable distributed storage for raw documents and intermediate data

## Demonstration

### Running the Search Engine
1. **Start Services**:
```bash
docker-compose up --build
```

2. **Prepare Data** (Inside container):
```bash
hdfs dfs -put /app/a.parquet /
/app/prepare_data.sh
```

3. **Run Indexer**:
```bash
/app/index.sh
```

4. **Execute Query**:
```bash
/app/search.sh "your query here"
```

## Configurations & Explanations

### Docker Compose Configs
```yaml
ports:
  - "8088:8088"  # YARN ResourceManager UI
  - "4040:4040"  # Spark Application UI
  - "9870:9870"  # HDFS NameNode UI
volumes:
  - "./app:/app" # Mount local code into container
platform: linux/amd64 # Ensure Mac M1/M2 compatibility
```

### Spark Configs (prepare_data.py)
```python
.config("spark.driver.memory", "4g") # Handle large document texts
.config("spark.executor.memory", "4g") # Process bigger partitions
.config("spark.sql.parquet.enableVectorizedReader", "true") # Faster Parquet parsing
```

### Cassandra Configs
```python
Cluster(['cassandra-server']) # Connect to containerized Cassandra
session.set_keyspace('search_keyspace') # Isolate search data
```

### Hadoop Configs (index.sh)
```bash
-D mapreduce.reduce.memory.mb=2048 # Handle large posting lists
-D mapreduce.reduce.java.opts=-Xmx1800m # Prevent OOM errors
-numReduceTasks 1 # Force global statistics aggregation
```

### Search Configs (search.sh)
```bash
--packages com.datastax.spark:spark-cassandra-connector_2.12:3.5.0 # Cassandra integration
--archives /app/.venv.tar.gz#.venv # Distribute Python environment
--conf spark.yarn.appMasterEnv.PYSPARK_PYTHON=./.venv/bin/python # Ensure Python version consistency
```

## BM25 Implementation
The ranking uses the following formula:


$$
BM25(q,d) = \sum_{t \in q} \log\frac{N - df(t) + 0.5}{df(t) + 0.5} \cdot \frac{(k_1 + 1)tf(t,d)}{k_1(1 - b + b\frac{dl(d)}{avgdl}) + tf(t,d)}
$$

Where:
- $N$ = Total documents
- $df(t)$ = Document frequency of term t
- $tf(t,d)$ = Term frequency in document d
- $dl(d)$ = Document length
- $avgdl$ = Average document length
- $k_1=1.2$, $b=0.75$ (standard values for web documents)