import sys
import os
import csv
import time
from datetime import datetime
from pymongo import MongoClient

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import MONGO_URI, DB_NAME, COLLECTION_RAW, BATCH_SIZE

def run_batch_loader(file_path, run_id):
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    raw_col = db[COLLECTION_RAW]

    file_name = os.path.basename(file_path)
    start_time = time.time()
    batch = []
    batch_index = 1
    total_loaded = 0

    try:
        with open(file_path, mode='r', encoding='utf-8-sig', errors='ignore') as infile:
            reader = csv.DictReader(infile)
            
            for row_num, row in enumerate(reader, start=1):
                clean_row = {str(k).replace('\ufeff', '').strip(): (str(v) if v is not None else "") for k, v in row.items() if k}
                
                # الالتزام بحقول Raw Layer المحددة في الوثيقة
                raw_document = {
                    "run_id": run_id,
                    "source_file": file_name,
                    "source_row_number": row_num,
                    "ingested_at": datetime.utcnow().isoformat(),
                    "engine_used": "python_batch",
                    "raw_record": clean_row
                }
                batch.append(raw_document)

                if len(batch) >= BATCH_SIZE:
                    b_start = time.time()
                    try:
                        raw_col.insert_many(batch, ordered=False)
                        b_duration = time.time() - b_start
                        total_loaded += len(batch)
                        rate = len(batch) / b_duration if b_duration > 0 else 0
                        print(f"  -> [Batch #{batch_index}] {len(batch)} records inserted | Batch Rate: {rate:.1f} rec/s")
                    except Exception as e:
                        print(f"  [!] Error in batch #{batch_index}: {e}")
                    batch = []
                    batch_index += 1

            if batch:
                raw_col.insert_many(batch, ordered=False)
                total_loaded += len(batch)
                print(f"  -> [Final Batch] {len(batch)} records inserted")

    finally:
        client.close()

    total_time = time.time() - start_time
    avg_throughput = total_loaded / total_time if total_time > 0 else 0

    print(f"\n[Python Batch] Finished: {total_loaded} rows in {total_time:.2f}s | Throughput: {avg_throughput:.1f} rec/s\n")

    return {
        "engine": "python_batch",
        "loaded_raw": total_loaded,
        "seconds_elapsed": total_time,
        "throughput": avg_throughput,
        "batch_size": BATCH_SIZE
    }