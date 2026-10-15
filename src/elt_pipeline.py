import sys
import os
import time
from pymongo import MongoClient, UpdateOne

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import MONGO_URI, DB_NAME, COLLECTION_RAW, COLLECTION_VALIDATED, COLLECTION_QUARANTINE, ELT_CHUNK_SIZE
from src.quality_rules import validate_and_clean_record

def process_elt_transformation(run_id, batch_chunk_size=ELT_CHUNK_SIZE):
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    
    raw_col = db[COLLECTION_RAW]
    valid_col = db[COLLECTION_VALIDATED]
    quarantine_col = db[COLLECTION_QUARANTINE]

    start_time = time.time()
    
    total_raw_in_run = raw_col.count_documents({"run_id": run_id})
    print(f"\n[ELT Pipeline] Processing {total_raw_in_run} raw records for run_id: {run_id} ...")

    raw_cursor = raw_col.find({"run_id": run_id}).batch_size(batch_chunk_size)
    
    valid_bulk_ops = []
    quarantine_docs = []
    
    count_valid = 0
    count_corrected = 0
    count_quarantine = 0
    total_inserted = 0
    total_updated = 0
    error_cases_count = {}

    for doc in raw_cursor:
        raw_data = doc.get("raw_record", {})
        result = validate_and_clean_record(raw_data)
        
        # حماية إضافية في حال أرجعت الدالة قيمة فارغة
        if not result or not isinstance(result, dict):
            continue

        status = result.get("status")
        data = result.get("data", {})
        if status in ["valid", "corrected"]:
            if status == "valid":
                count_valid += 1
            else:
                count_corrected += 1
            
            # Idempotent Upsert بناءً على order_id
            valid_bulk_ops.append(
                UpdateOne(
                    {"order_id": data["order_id"]},
                    {"$set": data},
                    upsert=True
                )
            )
        else:
            count_quarantine += 1
            data["run_id"] = run_id
            quarantine_docs.append(data)
            for err in data.get("error_codes", []):
                error_cases_count[err] = error_cases_count.get(err, 0) + 1

        if len(valid_bulk_ops) >= batch_chunk_size:
            bulk_res = valid_col.bulk_write(valid_bulk_ops, ordered=False)
            total_inserted += bulk_res.upserted_count
            total_updated += bulk_res.modified_count
            valid_bulk_ops = []

        if len(quarantine_docs) >= batch_chunk_size:
            quarantine_col.insert_many(quarantine_docs, ordered=False)
            quarantine_docs = []

    if valid_bulk_ops:
        bulk_res = valid_col.bulk_write(valid_bulk_ops, ordered=False)
        total_inserted += bulk_res.upserted_count
        total_updated += bulk_res.modified_count

    if quarantine_docs:
        quarantine_col.insert_many(quarantine_docs, ordered=False)

    total_raw_processed = count_valid + count_corrected + count_quarantine
    total_unchanged = (count_valid + count_corrected) - (total_inserted + total_updated)
    duration = time.time() - start_time

    # فحص معادلة الاتساق الإلزامية (البند 6.11)
    consistency_passed = (total_raw_processed == total_raw_in_run)
    print(f"\n[ELT Pipeline] Finished {total_raw_processed} records in {duration:.2f}s")
    print(f"Consistency Check: {'PASSED (OK)' if consistency_passed else 'FAILED'}")
    print(f"  Valid: {count_valid} | Corrected: {count_corrected} | Quarantine: {count_quarantine}")
    print(f"  Upsert Metrics -> Inserted: {total_inserted}, Updated: {total_updated}, Unchanged: {total_unchanged}")

    client.close()

    return {
        "run_id": run_id,
        "processed_raw": total_raw_processed,
        "count_valid": count_valid,
        "count_corrected": count_corrected,
        "count_quarantine": count_quarantine,
        "count_inserted": total_inserted,
        "count_updated": total_updated,
        "count_unchanged": total_unchanged,
        "error_case_counts": error_cases_count,
        "transformation_seconds": duration,
        "consistency_check": consistency_passed
    }