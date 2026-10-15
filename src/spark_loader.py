import sys
import os
import time
from datetime import datetime

os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

jdk_path = r"C:\Program Files\Eclipse Adoptium\jdk-21.0.12.101-hotspot"
if os.path.exists(jdk_path):
    os.environ["JAVA_HOME"] = jdk_path
    os.environ["PATH"] = os.path.join(jdk_path, "bin") + ";" + os.environ.get("PATH", "")

if os.path.exists(r"C:\hadoop"):
    os.environ["HADOOP_HOME"] = r"C:\hadoop"
    os.environ["hadoop.home.dir"] = r"C:\hadoop"
    os.environ["PATH"] = r"C:\hadoop\bin;" + os.environ.get("PATH", "")

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType
from pymongo import MongoClient

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import MONGO_URI, DB_NAME, COLLECTION_RAW
from src.monitor import SystemMonitor

def get_spark_session():
    jvm_flags = (
        "--add-opens=java.base/java.lang=ALL-UNNAMED "
        "--add-opens=java.base/java.lang.invoke=ALL-UNNAMED "
        "--add-opens=java.base/java.lang.reflect=ALL-UNNAMED "
        "--add-opens=java.base/java.io=ALL-UNNAMED "
        "--add-opens=java.base/java.util=ALL-UNNAMED "
        "--add-opens=java.base/java.util.concurrent=ALL-UNNAMED "
        "--add-opens=java.base/sun.nio.ch=ALL-UNNAMED"
    )

    return SparkSession.builder \
        .appName("HybridDataPipeline_SparkEngine") \
        .master("local[2]") \
        .config("spark.driver.memory", "3g") \
        .config("spark.executor.memory", "3g") \
        .config("spark.driver.memoryOverhead", "1g") \
        .config("spark.driver.extraJavaOptions", jvm_flags) \
        .config("spark.executor.extraJavaOptions", jvm_flags) \
        .config("spark.python.worker.reuse", "true") \
        .getOrCreate()

def run_spark_loader(file_path, run_id):
    monitor = SystemMonitor(interval=4)
    monitor.start()

    spark = get_spark_session()
    start_time = time.time()
    file_name = os.path.basename(file_path)
    current_time_str = datetime.utcnow().isoformat()

    columns = [
        "order_id", "order_date", "status", "customer_id", "customer_name",
        "customer_phone", "customer_email", "city", "district", "delivery_type",
        "delivery_cost", "payment_method", "payment_status", "payment_amount",
        "currency", "total_amount", "items_json"
    ]
    schema = StructType([StructField(c, StringType(), True) for c in columns])

    total_rows = 0
    client = MongoClient(MONGO_URI, connectTimeoutMS=60000, socketTimeoutMS=120000)
    raw_col = client[DB_NAME][COLLECTION_RAW]

    try:
        print(f"\n[PySpark Engine] Reading dataset: {file_path}")
        df = spark.read.format("csv") \
            .option("header", "true") \
            .option("encoding", "UTF-8") \
            .option("quote", "\"") \
            .option("escape", "\"") \
            .schema(schema) \
            .load(file_path)

        input_partitions = df.rdd.getNumPartitions()
        print(f"[PySpark Engine] Partitions allocated: {input_partitions}")
        print("[PySpark Engine] Streaming partition records safely to MongoDB...")

        batch = []
        # استخدام toLocalIterator يمنع تفريغ البيانات بالذاكرة ويحولها لتدفق مستمر
        for row_idx, row in enumerate(df.toLocalIterator(), start=1):
            clean_dict = {
                str(k).replace('\ufeff', '').strip(): (str(v) if v is not None else "")
                for k, v in row.asDict().items() if k
            }

            batch.append({
                "run_id": run_id,
                "source_file": file_name,
                "source_row_number": row_idx,
                "ingested_at": current_time_str,
                "engine_used": "pyspark",
                "raw_record": clean_dict
            })
            total_rows += 1

            if len(batch) >= 2000:
                raw_col.insert_many(batch, ordered=False)
                batch = []

        if batch:
            raw_col.insert_many(batch, ordered=False)

    finally:
        client.close()
        monitor.stop()
        spark.stop()

    total_time = time.time() - start_time
    avg_throughput = total_rows / total_time if total_time > 0 else 0

    print(f"\n[PySpark Engine] Ingestion complete: {total_rows:,} rows loaded in {total_time:.2f}s | Throughput: {avg_throughput:.1f} rows/s\n")

    return {
        "engine": "pyspark",
        "loaded_raw": total_rows,
        "seconds_elapsed": total_time,
        "throughput": avg_throughput,
        "partitions": input_partitions
    }