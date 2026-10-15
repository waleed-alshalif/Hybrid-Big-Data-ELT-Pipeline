import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pymongo import MongoClient
from config.settings import MONGO_URI, DB_NAME, COLLECTION_RAW, COLLECTION_VALIDATED, COLLECTION_QUARANTINE

def init_mongo():
    client = MongoClient(MONGO_URI)
    try:
        db = client[DB_NAME]
        
        # إنشاء المجموعات إذا لم تكن موجودة
        existing_cols = db.list_collection_names()
        for col_name in [COLLECTION_RAW, COLLECTION_VALIDATED, COLLECTION_QUARANTINE]:
            if col_name not in existing_cols:
                db.create_collection(col_name)
        
        # Unique Index على order_id في orders_validated (متطلب إلزامي للـ Idempotency)
        db[COLLECTION_VALIDATED].create_index([("order_id", 1)], unique=True)
        
        # الفهارس المساعدة لسرعة الاستعلام
        db[COLLECTION_RAW].create_index([("run_id", 1)])
        db[COLLECTION_QUARANTINE].create_index([("run_id", 1)])
        
        print("[MongoDB] Collections and Indexes initialized successfully.")
    finally:
        client.close()

if __name__ == "__main__":
    init_mongo()