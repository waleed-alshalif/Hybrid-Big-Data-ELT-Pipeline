import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.quality_rules import validate_and_clean_record

def test_valid_record():
    record = {
        "order_id": "ORD-001",
        "order_date": "2025-01-31",
        "status": "مؤكد",
        "customer_id": "CUST-10",
        "customer_name": "أحمد",
        "customer_phone": "771234567",
        "customer_email": "ahmed@mail.com",
        "currency": "YER",
        "delivery_cost": "1000",
        "payment_amount": "5000",
        "total_amount": "6000",
        "items_json": '[{"item_id": "ITM-1", "price": 5000}]'
    }
    result = validate_and_clean_record(record)
    assert result["status"] == "valid"
    assert len(result["data"]["corrections"]) == 0

def test_corrected_record():
    record = {
        "order_id": "ORD-002",
        "order_date": "2025 /01 /31",
        "customer_id": "CUST-20",
        "customer_phone": "+967 77 123 4567",
        "customer_email": "user@@mail..com",
        "currency": "لاير يمني",
        "delivery_cost": "1,000.00",
        "payment_amount": "خمسة آلاف",
        "total_amount": "٦٠٠٠",
        "items_json": '[{"item_id": "ITM-2"}]'
    }
    result = validate_and_clean_record(record)
    assert result["status"] == "corrected"
    assert result["data"]["customer_email"] == "user@mail.com"
    assert result["data"]["currency"] == "YER"
    assert result["data"]["payment_amount"] == "5000"
    assert result["data"]["total_amount"] == "6000"
    assert result["data"]["order_date"] == "2025-01-31"
    assert len(result["data"]["corrections"]) > 0

def test_quarantine_record():
    record = {
        "order_id": "",  # معرف مفقود
        "order_date": "2099-00-00",  # تاريخ غير منطقي
        "customer_id": "",
        "items_json": "corrupted json{"
    }
    result = validate_and_clean_record(record)
    assert result["status"] == "quarantine"
    assert "ID_ORDER_MISSING" in result["data"]["error_codes"]
    assert "DATE_IMPOSSIBLE_INVALID" in result["data"]["error_codes"]
    assert "JSON_ITEMS_CORRUPTED" in result["data"]["error_codes"]
    