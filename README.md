<div align="center">

# ⚡ خط أنابيب ELT هجين عالي الأداء للبيانات الضخمة

### معمارية هجينة لمعالجة البيانات الضخمة، والتحقق من الجودة، والتصحيح الآلي، والحجر الصحي

<p>
  <img src="https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/Apache%20Spark-3.5.5-orange?style=for-the-badge&logo=apachespark&logoColor=white">
  <img src="https://img.shields.io/badge/MongoDB-WiredTiger-green?style=for-the-badge&logo=mongodb&logoColor=white">
  <img src="https://img.shields.io/badge/Architecture-ELT-red?style=for-the-badge">
</p>

<p align="center">
  <b>
    خط بيانات متكامل لمعالجة واستيعاب 30 مليون سجل باستخدام
    Python Batch وApache PySpark وMongoDB، مع الحفاظ على البيانات
    الأصلية وتطبيق قواعد جودة البيانات والحجر الصحي.
  </b>
</p>

</div>

---

# 👩‍💻 إعداد وتطوير المشروع

<div align="center">

## **المهندسة: أبرار مروان الدبعي**

### مهندسة ذكاء اصطناعي وباحثة في هندسة البيانات الضخمة

[![GitHub](https://img.shields.io/badge/GitHub-AbrarMarwan-181717?style=for-the-badge&logo=github)](https://github.com/AbrarMarwan)

</div>

| البيان | التفاصيل |
|---|---|
| **الجامعة** | جامعة الرازي |
| **الكلية** | كلية الحاسوب وتكنولوجيا المعلومات |
| **التخصص** | بكالوريوس ذكاء اصطناعي |
| **المستوى** | المستوى الرابع |
| **المقرر** | البيانات الضخمة - العملي |
| **المشرف** | م. عمر أبوسند |

---

# 📌 1. نظرة عامة على المشروع

يطبق المشروع خط بيانات هجين لمعالجة بيانات الطلبات الضخمة وغير النظيفة
وفق معمارية **ELT (Extract – Load – Transform)**.

يعتمد المشروع على مبدأ **عدم فقدان البيانات (Zero Data Loss)**، حيث يتم
تحميل البيانات كاملة إلى طبقة البيانات الخام `orders_raw` قبل تنفيذ أي
عمليات فحص أو تصحيح.

بعد ذلك يتم تحليل السجلات وتصنيفها إلى:

- ✅ سجلات سليمة `Valid`
- 🔧 سجلات تم تصحيحها `Corrected`
- 🚨 سجلات غير قابلة للإصلاح وتم عزلها `Quarantined`

---

# 🏗️ 2. معمارية خط البيانات

```mermaid
flowchart TD

    A["ملف CSV المصدر"] --> B{"فحص حجم الملف"}

    B -->|"أقل من 200 MB"| C["Python Batch"]
    B -->|"200 MB أو أكثر"| D["Apache PySpark"]

    C --> E[("MongoDB<br/>orders_raw")]
    D --> E

    E --> F["محرك فحص جودة البيانات"]

    F --> G["سليم / مصحح"]
    F --> H["أخطاء غير قابلة للإصلاح"]

    G --> I[("orders_validated")]
    H --> J[("orders_quarantine")]

    G --> K["Audit Trail"]
````

---

# 🔀 3. التوجيه التلقائي للمحرك

يتم اختيار محرك المعالجة تلقائيًا اعتمادًا على حجم الملف:

| حجم الملف          | محرك المعالجة    |
| ------------------ | ---------------- |
| أقل من **200 MB**  | 🐍 Python Batch  |
| **200 MB أو أكثر** | ⚡ Apache PySpark |

وبذلك لا يحتاج المستخدم إلى اختيار المحرك يدويًا.

---

# 🔄 4. تسلسل عملية المعالجة

```text
                    ┌─────────────────────┐
                    │      ملف CSV        │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    Router الحجم     │
                    └──────────┬──────────┘
                               │
               ┌───────────────┴───────────────┐
               │                               │
               ▼                               ▼
       ملف أقل من 200MB                ملف 200MB أو أكثر
               │                               │
               ▼                               ▼
       Python Batch Engine             Apache PySpark
               │                               │
               └───────────────┬───────────────┘
                               ▼
                     ┌──────────────────┐
                     │   orders_raw     │
                     │    Raw Layer     │
                     └────────┬─────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  فحص جودة البيانات │
                    └────────┬─────────┘
                             │
                  ┌──────────┴──────────┐
                  │                     │
                  ▼                     ▼
             Valid / Corrected     Quarantined
                  │                     │
                  ▼                     ▼
        orders_validated       orders_quarantine
```

---

# 💡 5. الركائز الهندسية الأساسية

## 🗄️ التحميل الخام — Raw Layer

يتم حفظ جميع السجلات الأصلية في:

```text
orders_raw
```

مع الاحتفاظ بمعلومات المصدر مثل:

```text
run_id
source_file
source_row_number
ingested_at
engine_used
raw_record
```

وهذا يضمن إمكانية الرجوع إلى البيانات الأصلية في أي وقت.

---

## 📝 أثر التصحيح — Audit Trail

لا يتم تعديل البيانات بصمت.

كل عملية تصحيح يتم توثيقها داخل `corrections` مع:

```text
field
original_value
corrected_value
rule_code
```

مثال:

```json
{
  "field": "currency",
  "original_value": "ريال",
  "corrected_value": "YER",
  "rule_code": "CURRENCY_STANDARDIZED"
}
```

---

## 🚨 الحجر الصحي — Quarantine

السجلات التي تحتوي على أخطاء جوهرية لا يمكن تصحيحها بأمان يتم عزلها
داخل:

```text
orders_quarantine
```

مع الاحتفاظ بالبيانات الأصلية وأكواد الأخطاء.

---

## 🔑 المفتاح التجاري وIdempotency

يعتمد النظام على:

```text
order_id
```

كمفتاح تجاري ثابت.

ويتم استخدام **Unique Index + Upsert** لمنع تكرار السجلات عند إعادة
تشغيل خط البيانات.

---

# 📊 6. نتائج القياس والأداء الفعلي

تم تنفيذ الاختبار على مجموعة البيانات الضخمة الكاملة بحجم:

**12.65 GB**

وتتكون من:

**30,000,000 سجل**

| المقياس                                 |         القيمة الفعلية |
| --------------------------------------- | ---------------------: |
| 📦 إجمالي السجلات المعالجة              |         **30,000,000** |
| ⚡ زمن استيعاب البيانات باستخدام PySpark |     **2,763.81 ثانية** |
| 🚀 معدل التدفق Throughput               | **10,854.6 سجل/ثانية** |
| 🗄️ السجلات المستوعبة في Raw            |         **30,000,000** |
| ✅ السجلات السليمة Valid                 |         **23,765,736** |
| 🔧 السجلات المصححة Corrected            |          **4,011,232** |
| 🚨 سجلات الحجر الصحي Quarantined        |          **2,223,032** |
| 🔐 فحص الاتساق الرياضي                  |        **PASSED (OK)** |

### معادلة الاتساق

```text
23,765,736
+
4,011,232
+
2,223,032
=
30,000,000
```

وبالتالي:

```text
Total Raw
=
Valid
+
Corrected
+
Quarantined
```

### نتيجة الاتساق

```text
23,765,736 + 4,011,232 + 2,223,032
=
30,000,000
```

✅ **تم اجتياز فحص الاتساق بنجاح.**

---

# 🔄 7. مقاييس الـ Upsert وIdempotency

| العملية       |          العدد |
| ------------- | -------------: |
| **Inserted**  | **27,489,117** |
| **Updated**   |    **197,711** |
| **Unchanged** |     **90,140** |

توضح هذه النتائج قدرة النظام على التعامل مع إعادة المعالجة والتحديثات
دون إنشاء نسخ مكررة من السجلات المعتمدة.

---

# 🧪 8. قواعد جودة البيانات

يطبق المشروع مجموعة من قواعد فحص وتصحيح البيانات بشكل آلي.

| قاعدة الجودة               | الوظيفة                                  |
| -------------------------- | ---------------------------------------- |
| `DATE_STANDARDIZED`        | توحيد صيغ التاريخ                        |
| `CURRENCY_STANDARDIZED`    | توحيد صيغ العملات                        |
| `NUMBER_NORMALIZED`        | تطبيع القيم الرقمية                      |
| `PHONE_NORMALIZED`         | توحيد أرقام الهواتف                      |
| `INVALID_YEMENI_PHONE`     | اكتشاف أرقام الهواتف اليمنية غير الصحيحة |
| `EMAIL_REPEATED_SYMBOLS`   | معالجة تكرار الرموز في البريد الإلكتروني |
| `JSON_SYNTAX_REPAIRED`     | إصلاح JSON القابل للإصلاح                |
| `MISSING_ORDER_ID`         | عزل السجلات التي تفتقد رقم الطلب         |
| `MISSING_CUSTOMER_ID`      | اكتشاف معرف العميل المفقود               |
| `AMBIGUOUS_NEGATIVE_VALUE` | عزل القيم المالية السالبة غير الواضحة    |

---

# 📅 9. توحيد التواريخ

يتم التعامل مع عدة صيغ للتاريخ، مثل:

```text
YYYY-MM-DDTHH:MM:SS
YYYY-MM-DD HH:MM:SS
YYYY-MM-DD
YYYY/MM/DD
DD/MM/YYYY
MM/DD/YYYY
```

ثم يتم توحيد القيم القابلة للمعالجة إلى الصيغة القياسية.

---

# 💰 10. توحيد العملات

يتم تحويل المرادفات المحلية إلى الرموز القياسية:

```text
ريال    → YER
سعودي   → SAR
دولار   → USD
```

---

# 🔢 11. تطبيع الأرقام

يتعامل النظام مع:

* الأرقام العربية/المشرقية.
* فواصل الآلاف.
* الصيغ الرقمية المختلفة.
* بعض القيم المكتوبة بالكلمات.

مثال:

```text
١٢٥٠
↓
1250
```

---

# 📱 12. فحص أرقام الهواتف

يتم فحص أرقام الهواتف اليمنية والتحقق من توافقها مع البادئات المدعومة:

```text
77
78
73
71
70
```

ويتم تصنيف الأرقام غير الصحيحة أو الوهمية وفق قواعد الجودة.

---

# 🧾 13. معالجة JSON

يتم فحص حقل:

```text
items_json
```

واكتشاف الحالات غير الصحيحة.

إذا كان الخطأ قابلًا للإصلاح يتم تصحيحه وتسجيل العملية داخل:

```text
corrections
```

أما التلف الهيكلي غير القابل للإصلاح فيتم عزله داخل:

```text
orders_quarantine
```

---

# 🗃️ 14. طبقات MongoDB

يستخدم المشروع قاعدة البيانات:

```text
midterm_data_pipeline
```

وتتكون من:

```text
midterm_data_pipeline
│
├── orders_raw
│
├── orders_validated
│
└── orders_quarantine
```

### `orders_raw`

البيانات الأصلية الكاملة.

### `orders_validated`

السجلات السليمة والمصححة.

### `orders_quarantine`

السجلات غير القابلة للإصلاح مع أكواد الأخطاء.

---

# 📈 15. المقاييس التي يوفرها النظام

يتم تسجيل مجموعة من مؤشرات الأداء، منها:

```text
read_rows
loaded_raw
count_valid
count_corrected
count_quarantine
throughput
seconds_elapsed
partitions
consistency_check
status
```

ويتم حفظ النتائج في:

```text
reports/results.json
```

---

# 📁 16. هيكل المشروع

```text
minimal_corrected_project/
│
├── config/
│   └── settings.py
│
├── data/
│   ├── orders_sample.csv
│   └── orders_huge_mixed_quality.csv
│
├── notebooks/
│   ├── individual_pipeline.ipynb
│   └── sample.ipynb
│
├── reports/
│   └── results.json
│
├── src/
│   ├── batch_loader.py
│   ├── mongo.py
│   ├── pipeline.py
│   ├── quality_rules.py
│   ├── router.py
│   ├── sample.py
│   └── spark_loader.py
│
├── tests/
│   └── test_quality.py
│
├── run_analysis.py
├── requirements.txt
├── pytest.ini
└── README.md
```

---

# 🛠️ 17. التقنيات المستخدمة

| التقنية                               | الاستخدام                                 |
| ------------------------------------- | ----------------------------------------- |
| 🐍 **Python 3.12**                    | معالجة الملفات الصغيرة وإدارة خط البيانات |
| ⚡ **Apache Spark 3.5.5**              | معالجة البيانات الضخمة                    |
| 🔥 **PySpark**                        | معالجة DataFrame الموزعة                  |
| 🍃 **MongoDB**                        | تخزين Raw وValidated وQuarantine          |
| 🔗 **PyMongo**                        | الاتصال بـMongoDB من Python               |
| 🔌 **MongoDB Spark Connector 10.7.0** | ربط Spark بـMongoDB                       |
| 🧪 **Pytest**                         | اختبار قواعد جودة البيانات                |

---

# ⚙️ 18. متطلبات التشغيل

## Python

```text
Python 3.12
```

## Apache Spark

```text
Apache Spark 3.5.5
```

## MongoDB

يجب تشغيل MongoDB محليًا باستخدام:

```text
mongodb://localhost:27017/
```

## Windows Hadoop Utilities

يتطلب التشغيل المحلي وجود:

```text
C:\hadoop\bin\winutils.exe
```

ويتم استخدام مجلد مؤقت لـSpark:

```text
E:\spark_temp
```

---

# 📦 19. تثبيت المتطلبات

من داخل مجلد المشروع:

```bash
pip install -r requirements.txt
```

---

# ▶️ 20. تشغيل المشروع

يستخدم المشروع نقطة تشغيل واحدة:

```bash
python run_analysis.py
```

يقوم البرنامج تلقائيًا بتشغيل المسارين:

```text
orders_sample.csv
        ↓
Python Batch
```

و:

```text
orders_huge_mixed_quality.csv
        ↓
Apache PySpark
```

وبذلك يتم اختبار المسارين المطلوبين ضمن تشغيل واحد.

---

# 🧪 21. تشغيل الاختبارات

لتشغيل اختبارات قواعد جودة البيانات:

```bash
pytest
```

أو:

```bash
python -m pytest
```

---

# 📊 22. ملف النتائج

بعد اكتمال التشغيل يتم إنشاء:

```text
reports/results.json
```

ويحتوي على نتائج التشغيل، ومنها:

```text
Router
Processing Engine
Records
Valid
Corrected
Quarantined
Throughput
Partitions
Consistency Check
Status
```

---

# 📸 23. أدلة التنفيذ

يفضل إرفاق لقطات الشاشة التالية ضمن التقرير أو المستودع:

### 1️⃣ إثبات الـRouter

إظهار:

```text
Sample < 200 MB
        ↓
Python Batch

Large ≥ 200 MB
        ↓
PySpark
```

### 2️⃣ MongoDB Compass

إظهار قاعدة البيانات:

```text
midterm_data_pipeline
│
├── orders_raw
├── orders_validated
└── orders_quarantine
```

### 3️⃣ سجل Validated

إظهار سجل يحتوي على:

```text
order_id
quality_status
corrections
id_run
record_raw
```

### 4️⃣ سجل Quarantine

إظهار:

```text
error_codes
details_error
order_id
record_raw
```

### 5️⃣ Audit Trail

إظهار:

```text
field
original_value
corrected_value
rule_code
```

### 6️⃣ نتائج الأداء

إظهار:

```text
30,000,000 Records
10,854.6 Records/sec
2,763.81 Seconds
Valid
Corrected
Quarantined
Consistency: PASSED
```

---

# 🔐 24. سلامة البيانات

يعتمد المشروع على مبدأ:

```text
                ┌─────────────────┐
                │    orders_raw   │
                │   Zero Loss     │
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │  Quality Engine │
                └────────┬────────┘
                         │
             ┌───────────┴───────────┐
             │                       │
             ▼                       ▼
       Valid / Corrected       Quarantine
```

وبالتالي لا يتم حذف السجلات غير الصحيحة من المصدر، بل يتم الاحتفاظ بها
وعزلها مع توثيق سبب العزل.

---

# 🚀 25. أبرز مميزات المشروع

* ✅ معمارية Hybrid ELT
* ✅ التوجيه التلقائي حسب حجم الملف
* ✅ حد التوجيه 200 MB
* ✅ Python Streaming Batch
* ✅ Apache PySpark للملفات الضخمة
* ✅ Raw Layer قبل معالجة الجودة
* ✅ Zero Data Loss
* ✅ Fixed Schema
* ✅ MongoDB Integration
* ✅ MongoDB Spark Connector
* ✅ أكثر من 8 قواعد لجودة البيانات
* ✅ Audit Trail
* ✅ Quarantine Layer
* ✅ Stable Business Key
* ✅ Unique Index
* ✅ Upsert
* ✅ Idempotency
* ✅ Consistency Check
* ✅ Performance Metrics
* ✅ Automated Tests

---

# 🎓 26. الأهداف الأكاديمية

يجمع المشروع بين مجموعة من المفاهيم العملية في هندسة البيانات الضخمة:

```text
                ┌──────────────────────┐
                │     Big Data         │
                └──────────┬───────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
       ELT / ETL       Distributed       NoSQL
                       Processing        Database
          │                │                │
          └────────────────┼────────────────┘
                           │
                           ▼
                    Data Quality
                           │
                           ▼
                  Audit & Lineage
                           │
                           ▼
                    Idempotency
```

---

# 🏆 27. النتيجة النهائية

تم تصميم وتنفيذ خط بيانات هجين قادر على التعامل مع بيانات ضخمة تصل إلى:

## **30 مليون سجل**

وبحجم:

## **12.65 GB**

مع تحقيق:

```text
Raw Records        = 30,000,000
Valid              = 23,765,736
Corrected          = 4,011,232
Quarantined        = 2,223,032
```

وفحص الاتساق:

```text
23,765,736
+
4,011,232
+
2,223,032
=
30,000,000
```

### ✅ CONSISTENCY CHECK: PASSED

### 🚀 THROUGHPUT: 10,854.6 RECORDS/SECOND

### ⏱️ PROCESSING TIME: 2,763.81 SECONDS

### 🗄️ RAW INGESTION: 30,000,000 RECORDS

---

<div align="center">

# ⚡ Hybrid ELT Big Data Pipeline

### Python Batch • Apache PySpark • MongoDB • Data Quality • Audit Trail • Quarantine

**إعداد: أبرار مروان الدبعي**

</div>
 
