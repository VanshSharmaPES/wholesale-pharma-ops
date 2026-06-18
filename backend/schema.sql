-- SQLite Schema for Expiry Return Reminder System

-- 1. Retailers Table
CREATE TABLE IF NOT EXISTS retailers (
    retailer_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    address TEXT,
    phone TEXT NOT NULL
);

-- 2. Sales Table
CREATE TABLE IF NOT EXISTS sales (
    sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
    retailer_id INTEGER NOT NULL,
    invoice_no TEXT NOT NULL,
    sale_date TEXT NOT NULL,
    product_name TEXT NOT NULL,
    batch_no TEXT NOT NULL,
    expiry_date TEXT NOT NULL,
    qty_sold INTEGER NOT NULL,
    mrp REAL NOT NULL,
    amount REAL,
    FOREIGN KEY (retailer_id) REFERENCES retailers(retailer_id)
);

-- 3. Reminder Log Table (to prevent duplicate notifications for same retailer-batch)
CREATE TABLE IF NOT EXISTS reminder_log (
    reminder_id INTEGER PRIMARY KEY AUTOINCREMENT,
    retailer_id INTEGER NOT NULL,
    batch_no TEXT NOT NULL,
    sent_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status TEXT,
    message_id TEXT,
    FOREIGN KEY (retailer_id) REFERENCES retailers(retailer_id)
);
