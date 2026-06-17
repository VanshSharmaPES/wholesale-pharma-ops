# Wholesale Pharma Operations System

A specialized Python-based operations system designed for a wholesale pharmaceutical shop based in Amritsar, Punjab, India. The system integrates with **Marg ERP** (accounting/billing) exports to streamline two critical operations:

1. **Reconciliation Engine**: Automates the detection of financial and quantity discrepancies between credit note vouchers and sales returns.
2. **Expiry Return Reminder System**: Tracks batches of products sold to retailers, calculates return windows, and schedules automated WhatsApp reminders before products expire.

---

## 🛠️ Modules & Stack

### Module 1: Reconciliation Engine
* **Purpose**: Parse credit note/voucher files (PDF or Excel formats), align items, match prices/quantities, and generate a discrepancy report.
* **Discrepancy Types**:
  * `MRP_MISMATCH`
  * `QTY_MISMATCH`
  * `AMOUNT_MISMATCH`
  * `MISSING_IN_CREDIT_NOTE`
  * `MISSING_IN_VOUCHER`
  * `MATCHED_OK`
* **Tech Stack**: `pdfplumber`, `openpyxl`, `pandas`, `RapidFuzz`

### Module 2: Expiry Return Reminder System
* **Purpose**: Scan sales history in PostgreSQL, identify retailer-batch pairings approaching expiry within a configurable return window (default 90 days), and send one-time proactive WhatsApp reminders.
* **Tech Stack**: `pandas`, `APScheduler`, `Twilio WhatsApp API`, `PostgreSQL`, `psycopg2`/`SQLAlchemy`, `python-dotenv`

---

## 🚦 Implementation Checklist

- [x] **Task 1: Project Scaffold** - Directory structure and empty placeholder files.
- [ ] **Task 2: Environment Setup** - `.env.example` and `requirements.txt`.
- [ ] **Task 3: Dummy Data Generator** - Punjabi-localized data generator script.
- [ ] **Task 4: parse_document() Excel** - Excel parsing functionality.
- [ ] **Task 5: parse_document() PDF** - PDF parsing extraction.
- [ ] **Task 6: fuzzy_match_items()** - RapidFuzz match implementation.
- [ ] **Task 7: detect_discrepancies()** - Discrepancy rule evaluation.
- [ ] **Task 8: generate_report()** - CSV and styled HTML reporting.
- [ ] **Task 9: CLI Entrypoint (Module 1)** - End-to-end reconciliation CLI.
- [ ] **Task 10: PostgreSQL Schema** - Migration and DB initialization.
- [ ] **Task 11: Excel Data Loader** - Sales data importer for Marg ERP Excel files.
- [ ] **Task 12: get_expiring_batches()** - Expiry database query builder.
- [ ] **Task 13: format_reminder_message()** - High-quality localized templates.
- [ ] **Task 14: WhatsApp & Logging** - Twilio messaging and notification deduplication.
- [ ] **Task 15: Scheduler Setup** - APScheduler BackgroundScheduler setup.

---

## 🏗️ Folder Structure

```
├── backend/
│   ├── api/
│   │   ├── expiry.py
│   │   └── reconciliation.py
│   ├── models/
│   │   └── db_models.py
│   ├── services/
│   │   ├── discrepancy.py
│   │   ├── expiry_engine.py
│   │   ├── matcher.py
│   │   ├── messenger.py
│   │   ├── parser.py
│   │   ├── queries.py
│   │   ├── reconciler.py
│   │   ├── reporter.py
│   │   └── whatsapp.py
│   ├── db_init.py
│   ├── generate_dummy_data.py
│   ├── load_sales_data.py
│   ├── main.py
│   ├── reconcile.py
│   ├── scheduler.py
│   └── schema.sql
├── data/
├── frontend/
├── tests/
├── .gitignore
├── .env.example
├── README.md
└── requirements.txt
```
