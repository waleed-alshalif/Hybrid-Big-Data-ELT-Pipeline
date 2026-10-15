import sys
import os
import uuid
import time
import argparse

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.mongo_setup import init_mongo
from src.file_router import route_file
from src.batch_loader import run_batch_loader
from src.spark_loader import run_spark_loader
from src.elt_pipeline import process_elt_transformation
from src.metrics import save_metrics

def main():
    parser = argparse.ArgumentParser(description="Hybrid Big Data Pipeline CLI (Midterm Project)")
    parser.add_argument("--file", required=True, help="Path to input CSV dataset")
    args = parser.parse_args()

    init_mongo()
    engine, file_size_mb = route_file(args.file)
    run_id = str(uuid.uuid4())
    total_start = time.time()

    if engine == "python_batch":
        load_stats = run_batch_loader(args.file, run_id)
    else:
        load_stats = run_spark_loader(args.file, run_id)

    elt_stats = process_elt_transformation(run_id)

    total_duration = time.time() - total_start

    final_report = {
        "run_id": run_id,
        "file_name": os.path.basename(args.file),
        "file_size_mb": round(file_size_mb, 2),
        "engine_used": engine,
        "rows_read": load_stats.get("loaded_raw", 0),
        "raw_loaded": load_stats.get("loaded_raw", 0),
        "valid_count": elt_stats["count_valid"],
        "corrected_count": elt_stats["count_corrected"],
        "quarantine_count": elt_stats["count_quarantine"],
        "inserted_count": elt_stats["count_inserted"],
        "updated_count": elt_stats["count_updated"],
        "unchanged_count": elt_stats["count_unchanged"],
        "elapsed_seconds": round(total_duration, 2),
        "throughput": round(load_stats.get("loaded_raw", 0) / total_duration, 2) if total_duration > 0 else 0,
        "engine_details": {
            "batch_size": load_stats.get("batch_size"),
            "partitions": load_stats.get("partitions")
        },
        "error_case_counts": elt_stats["error_case_counts"],
        "consistency_check": elt_stats["consistency_check"]
    }

    save_metrics(final_report)

if __name__ == "__main__":
    main()