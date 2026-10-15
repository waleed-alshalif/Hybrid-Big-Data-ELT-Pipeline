import re
import json
from datetime import datetime

# Rule 1: تحويل الأرقام المشرقية (العربية) إلى أرقام لاتينية
def normalize_arabic_digits(val):
    if not val:
        return val
    arabic_digits = "٠١٢٣٤٥٦٧٨٩٫"
    latin_digits = "0123456789."
    trans = str.maketrans(arabic_digits, latin_digits)
    return str(val).translate(trans)

# Rule 2: إزالة فواصل الآلاف
def clean_thousand_separators(val):
    if not val:
        return val
    val = normalize_arabic_digits(val)
    return re.sub(r'(?<=\d),(?=\d)', '', str(val).strip())

# Rule 3: فحص وتوحيد العملات المقبولة
VALID_CURRENCIES = {"YER", "SAR", "USD"}
def standardize_currency(val):
    if not val:
        return "YER"
    val_clean = str(val).strip().upper()
    if val_clean in ["لاير", "لاير يمني", "ريال", "ريال يمني", "YER"]:
        return "YER"
    if val_clean in ["سعودي", "ريال سعودي", "SAR"]:
        return "SAR"
    if val_clean in ["دولار", "دولار امريكي", "USD"]:
        return "USD"
    if val_clean in VALID_CURRENCIES:
        return val_clean
    return None

# Rule 4: معالجة الأسعار المكتوبة بالكلمات
WORD_TO_NUM = {
    "ألف": 1000, "الف": 1000, "ألفان": 2000, "الفان": 2000, 
    "ألفين": 2000, "الفين": 2000, "ثلاثة آلاف": 3000, "ثلاثة الاف": 3000,
    "أربعة آلاف": 4000, "اربعة الاف": 4000, "خمسة آلاف": 5000, "خمسة الاف": 5000
}
def parse_price_words(val):
    if not val:
        return val
    val_clean = str(val).strip()
    return str(WORD_TO_NUM.get(val_clean, val))

# Rule 5: فحص وتوحيد رقم الهاتف اليمني (9 أرقام تبدأ بالمفاتيح المعتمدة)
def validate_and_clean_yemeni_phone(val):
    if not val:
        return None, True, False  # إذا كان الحقل فارغاً لا يعتبر خطأ عزل
    
    raw_str = str(val).strip()
    digits = normalize_arabic_digits(raw_str)
    digits = re.sub(r'[\s\-\(\)\+]', '', digits)
    
    # معالجة المفتاح الدولي أو الصفر المحلي
    if digits.startswith("00967"):
        digits = digits[5:]
    elif digits.startswith("967"):
        digits = digits[3:]
    elif digits.startswith("0") and len(digits) == 10:
        digits = digits[1:]
        
    valid_prefixes = ("77", "78", "73", "71", "70")
    if len(digits) == 9 and digits.startswith(valid_prefixes):
        was_corrected = (digits != raw_str)
        return digits, True, was_corrected
        
    return digits, False, False

# Rule 6: تنظيف البريد الإلكتروني من الرموز المكررة
def clean_email(val):
    if not val:
        return val
    val = str(val).strip()
    val = re.sub(r'@+', '@', val)
    return re.sub(r'\.+', '.', val)

# Rule 7: توحيد التاريخ مع فحص المنطقية
def standardize_date(val):
    if not val:
        return None
    val = normalize_arabic_digits(val).strip()
    val = val.replace("T", " ")
    val = re.sub(r'\s*/\s*', '/', val)
    val = re.sub(r'\s*-\s*', '-', val)
    
    formats = [
        "%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d",
        "%d-%m-%Y %H:%M:%S", "%d-%m-%Y", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y"
    ]
    for fmt in formats:
        try:
            parsed = datetime.strptime(val, fmt)
            if 1990 <= parsed.year <= 2035:
                return parsed.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None

# Rule 8: تنظيف المسافات المحيطة بالنصوص
def clean_string_status(val):
    if not val:
        return ""
    return str(val).strip()


def validate_and_clean_record(raw_dict):
    clean_raw = {}
    for k, v in raw_dict.items():
        if k:
            k_clean = str(k).replace('\ufeff', '').strip().lower()
            clean_raw[k_clean] = v

    corrections = []
    quarantine_errors = []

    # 1. فحص order_id
    order_id = str(clean_raw.get("order_id", "") or "").strip()
    if not order_id or order_id.lower() in ["null", "none", "nan", ""]:
        quarantine_errors.append("MISSING_ORDER_ID")

    # 2. فحص customer_id
    customer_id = str(clean_raw.get("customer_id", "") or "").strip()
    if not customer_id or customer_id.lower() in ["null", "none", "nan", ""]:
        quarantine_errors.append("MISSING_CUSTOMER_ID")

    # 3. فحص التاريخ ومعيار ISO القياسي
    raw_date = str(clean_raw.get("order_date", "") or "").strip()
    norm_date = standardize_date(raw_date)
    if not norm_date:
        quarantine_errors.append("INVALID_IMPOSSIBLE_DATE")
    else:
        # فحص هل التاريخ كان مكتوباً بالفعل بصيغة ISO القياسية (سواء احتوى وقتاً أو لا)
        is_iso_standard = bool(re.match(r'^\d{4}-\d{2}-\d{2}([ T]\d{2}:\d{2}:\d{2})?$', raw_date))
        if not is_iso_standard:
            corrections.append({
                "field": "order_date",
                "original_value": raw_date,
                "corrected_value": norm_date,
                "rule_code": "DATE_STANDARDIZED"
            })

    # 4. فحص items_json
    items_raw = str(clean_raw.get("items_json", "") or "").strip()
    items_parsed = None
    if not items_raw or items_raw in ["[]", "{}", '""', "''"]:
        quarantine_errors.append("EMPTY_ITEMS")
    else:
        cleaned_json = items_raw
        if cleaned_json.startswith('"') and cleaned_json.endswith('"') and len(cleaned_json) > 1:
            cleaned_json = cleaned_json[1:-1]
            
        cleaned_json = cleaned_json.replace('""', '"').replace('\\"', '"').strip()
        
        if cleaned_json.startswith('[') and not cleaned_json.endswith(']'):
            if cleaned_json.endswith('}'):
                cleaned_json += ']'
            elif not cleaned_json.endswith('"'):
                cleaned_json += '"}]'

        try:
            items_parsed = json.loads(cleaned_json)
            if not items_parsed or not isinstance(items_parsed, list) or len(items_parsed) == 0:
                quarantine_errors.append("EMPTY_ITEMS")
            else:
                if cleaned_json != items_raw and ('""' in items_raw or '\\"' in items_raw or not items_raw.endswith(']')):
                    corrections.append({
                        "field": "items_json",
                        "original_value": items_raw,
                        "corrected_value": json.dumps(items_parsed, ensure_ascii=False),
                        "rule_code": "JSON_SYNTAX_REPAIRED"
                    })
        except Exception:
            quarantine_errors.append("CORRUPTED_ITEMS_JSON")

    # 5. فحص العملة
    raw_curr = str(clean_raw.get("currency", "") or "").strip()
    c_curr = standardize_currency(raw_curr)
    if not c_curr:
        quarantine_errors.append("INVALID_CURRENCY")
    elif raw_curr and c_curr != raw_curr.upper():
        corrections.append({
            "field": "currency",
            "original_value": raw_curr,
            "corrected_value": c_curr,
            "rule_code": "CURRENCY_STANDARDIZED"
        })

    # 6. فحص الأرقام والقيم المالية والسالبة
    for field in ["delivery_cost", "payment_amount", "total_amount"]:
        orig = str(clean_raw.get(field, "") or "").strip()
        parsed_words = parse_price_words(orig)
        cleaned_num_str = clean_thousand_separators(parsed_words)
        try:
            num_val = float(cleaned_num_str) if cleaned_num_str else 0.0
            if num_val < 0:
                quarantine_errors.append("AMBIGUOUS_NEGATIVE_VALUE")
        except ValueError:
            quarantine_errors.append(f"INVALID_NUMERIC_{field.upper()}")

    # 7. فحص رقم الهاتف اليمني
    raw_phone = str(clean_raw.get("customer_phone", "") or "").strip()
    c_phone, is_valid_phone, phone_corrected = validate_and_clean_yemeni_phone(raw_phone)
    if raw_phone and not is_valid_phone:
        quarantine_errors.append("INVALID_YEMENI_PHONE")

    # العزل المباشر إذا وُجدت أخطاء حاسمة
    if quarantine_errors:
        if len(quarantine_errors) > 1:
            quarantine_errors.append("MULTIPLE_CONFLICTING_ERRORS")
        return {
            "status": "quarantined",
            "data": {
                "order_id": order_id if order_id else None,
                "error_codes": list(set(quarantine_errors)),
                "raw_record": raw_dict
            }
        }

    # بناء بيانات السجل المقبول (Validated / Corrected)
    clean_data = dict(clean_raw)
    clean_data["order_id"] = order_id
    clean_data["customer_id"] = customer_id
    clean_data["order_date"] = norm_date
    clean_data["currency"] = c_curr or "YER"
    if items_parsed:
        clean_data["items_json"] = json.dumps(items_parsed, ensure_ascii=False)

    # معالجة الهاتف الصالح
    if phone_corrected:
        corrections.append({
            "field": "customer_phone",
            "original_value": raw_phone,
            "corrected_value": c_phone,
            "rule_code": "PHONE_NORMALIZED"
        })
    clean_data["customer_phone"] = c_phone or ""

    # تصحيح البريد الإلكتروني
    raw_email = str(clean_raw.get("customer_email", "") or "").strip()
    c_email = clean_email(raw_email)
    if c_email != raw_email:
        corrections.append({
            "field": "customer_email",
            "original_value": raw_email,
            "corrected_value": c_email,
            "rule_code": "EMAIL_REPEATED_SYMBOLS"
        })
    clean_data["customer_email"] = c_email

    # تصحيح الحقول المالية المكتوبة بكلمات أو فواصل
    for field in ["delivery_cost", "payment_amount", "total_amount"]:
        orig = str(clean_raw.get(field, "") or "").strip()
        parsed_words = parse_price_words(orig)
        cleaned_num = clean_thousand_separators(parsed_words)
        if orig and cleaned_num != orig:
            corrections.append({
                "field": field,
                "original_value": orig,
                "corrected_value": cleaned_num,
                "rule_code": "NUMBER_NORMALIZED"
            })
        clean_data[field] = cleaned_num

    # تنظيف المسافات البيضاء دون اعتبارها خطأ جودة
    for str_field in ["status", "payment_status", "delivery_type", "city", "district", "customer_name"]:
        orig = str(clean_raw.get(str_field, "") or "")
        clean_data[str_field] = clean_string_status(orig)

    quality_status = "corrected" if len(corrections) > 0 else "valid"
    clean_data["quality_status"] = quality_status
    clean_data["corrections"] = corrections

    return {
        "status": quality_status,
        "data": clean_data
    }