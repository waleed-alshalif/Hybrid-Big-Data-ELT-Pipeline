import sys
import os
import json
from pymongo import MongoClient

sys.path.append(os.path.abspath("."))
from config.settings import MONGO_URI, DB_NAME, COLLECTION_RAW, COLLECTION_VALIDATED, COLLECTION_QUARANTINE

def inspect_database():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]

    print("=" * 60)
    print(f"🔍 Checking MongoDB Database: [{DB_NAME}]")
    print("=" * 60)

    # 1. فحص المجموعات وعدد الوثائق
    collections = [COLLECTION_RAW, COLLECTION_VALIDATED, COLLECTION_QUARANTINE]
    for col_name in collections:
        count = db[col_name].count_documents({})
        print(f"📦 Collection: {col_name:<20} | Documents: {count:,}")

    print("\n" + "-" * 60)
    print("📑 Sample Records Inspection:")
    print("-" * 60)

    # 2. فحص عينة من orders_validated (للتأكد من الـ Audit Trail)
    valid_sample = db[COLLECTION_VALIDATED].find_one({"quality_status": "corrected"})
    if valid_sample:
        print("\n✅ Sample Corrected Record in [orders_validated]:")
        valid_sample.pop("_id", None)
        print(json.dumps(valid_sample, ensure_ascii=False, indent=2))
    else:
        print("\n⚠️ No corrected records found in orders_validated.")

    # 3. فحص عينة من orders_quarantine (للتأكد من رموز الأخطاء)
    quarantine_sample = db[COLLECTION_QUARANTINE].find_one()
    if quarantine_sample:
        print("\n⛔ Sample Quarantined Record in [orders_quarantine]:")
        quarantine_sample.pop("_id", None)
        print(json.dumps(quarantine_sample, ensure_ascii=False, indent=2))
    else:
        print("\n⚠️ No quarantined records found in orders_quarantine.")

    # 4. فحص الفهارس (Indexes)
    print("\n" + "-" * 60)
    print("🔑 Indexes in [orders_validated]:")
    indexes = db[COLLECTION_VALIDATED].index_information()
    for idx_name, idx_info in indexes.items():
        print(f"  - Index: {idx_name} | Keys: {idx_info['key']} | Unique: {idx_info.get('unique', False)}")
    print("=" * 60)

    client.close()

if __name__ == "__main__":
    inspect_database()