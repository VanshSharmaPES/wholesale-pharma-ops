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
* **Purpose**: Scan sales history in a local SQLite database, identify retailer-batch pairings approaching expiry within a configurable return window (default 90 days), and send one-time proactive WhatsApp reminders.
* **Tech Stack**: `pandas`, `APScheduler`, `Twilio WhatsApp API`, `SQLite` (via Python standard `sqlite3`), `python-dotenv`

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
