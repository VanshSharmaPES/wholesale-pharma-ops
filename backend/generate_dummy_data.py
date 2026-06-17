"""
Pharma Wholesale Operations - Dummy Data Generator

Produces realistic, localized dummy data for a wholesale pharmaceutical shop in Amritsar, Punjab.
Generates:
1. Retailer list (10-15 retailers with Punjab addresses and +91 phone numbers).
2. Sales history (50-100 sales records with real Indian pharma products, batch numbers, and expiries).
3. 3 Voucher/Credit Note pairs with deliberate discrepancies covering all 6 discrepancy types:
   - MATCHED_OK
   - MRP_MISMATCH
   - QTY_MISMATCH
   - AMOUNT_MISMATCH
   - MISSING_IN_CREDIT_NOTE
   - MISSING_IN_VOUCHER
"""

import os
import random
import logging
from datetime import datetime, timedelta
import pandas as pd

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Constants for localized dummy generation
CITIES = ["Amritsar", "Jalandhar", "Ludhiana", "Patiala", "Bathinda", "Gurdaspur", "Batala"]
AREAS = ["Ranjit Avenue", "Mall Road", "Lawrence Road", "Hall Bazar", "Putligarh", "Majitha Road"]
RETAILER_SUFFIXES = ["Medicos", "Pharmacy", "Chemists", "Drug House", "Medical Hall"]

PRODUCTS = {
    "Dolo 650": 30.90,
    "Calpol": 15.50,
    "Augmentin": 223.10,
    "Pantop": 120.00,
    "Metformin 500mg": 55.00,
    "Combiflam": 45.00,
    "Pan D": 199.50,
    "Azithromycin 500mg": 119.00
}

def generate_phone() -> str:
    """Generate a realistic +91 Punjab mobile number."""
    return f"+91{random.randint(70000, 99999)}{random.randint(10000, 99999)}"

def generate_batch() -> str:
    """Generate a batch number in A1234 or B5678 format."""
    letter = random.choice(["A", "B"])
    digits = "".join(str(random.randint(0, 9)) for _ in range(4))
    return f"{letter}{digits}"

def generate_data():
    """Main function to generate and save all dummy datasets."""
    try:
        # Define output directory
        out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tests", "sample_data"))
        os.makedirs(out_dir, exist_ok=True)
        logger.info(f"Target directory for dummy data: {out_dir}")

        # 1. Generate Retailers (10 to 15)
        num_retailers = random.randint(10, 15)
        retailers = []
        for r_id in range(1, num_retailers + 1):
            city = random.choice(CITIES)
            area = random.choice(AREAS) if city == "Amritsar" else "Main Bazar"
            name = f"{city} {random.choice(RETAILER_SUFFIXES)} Ltd." if r_id % 3 == 0 else f"Sri Guru {city} {random.choice(RETAILER_SUFFIXES)}"
            address = f"Shop No. {random.randint(10, 150)}, {area}, {city}, Punjab, 143001"
            retailers.append({
                "retailer_id": r_id,
                "name": name,
                "address": address,
                "phone": generate_phone()
            })
        
        df_retailers = pd.DataFrame(retailers)
        retailers_path = os.path.join(out_dir, "retailers.csv")
        df_retailers.to_csv(retailers_path, index=False)
        logger.info(f"Saved {len(df_retailers)} retailers to {retailers_path}")

        # 2. Generate Sales History (50 to 100 records)
        num_sales = random.randint(50, 100)
        sales = []
        today = datetime.now()
        
        # Keep track of active batches to reuse them in returns
        active_batches = {}
        
        for sale_id in range(1, num_sales + 1):
            retailer = random.choice(retailers)
            product_name = random.choice(list(PRODUCTS.keys()))
            mrp = PRODUCTS[product_name]
            
            # Generate or retrieve active batch for product
            if product_name not in active_batches or random.random() < 0.2:
                batch_no = generate_batch()
                # Expiry spread across the next 6 to 18 months (180 to 540 days)
                expiry_date = today + timedelta(days=random.randint(180, 540))
                active_batches[product_name] = (batch_no, expiry_date)
            else:
                batch_no, expiry_date = active_batches[product_name]
                
            qty_sold = random.randint(5, 150)
            amount = round(qty_sold * mrp * 0.85, 2)  # 15% wholesale discount
            
            # Sale date in the past 90 days
            sale_date = today - timedelta(days=random.randint(1, 90))
            invoice_no = f"INV-2026-{1000 + sale_id}"
            
            sales.append({
                "sale_id": sale_id,
                "retailer_id": retailer["retailer_id"],
                "invoice_no": invoice_no,
                "sale_date": sale_date.strftime("%Y-%m-%d"),
                "product_name": product_name,
                "batch_no": batch_no,
                "expiry_date": expiry_date.strftime("%Y-%m-%d"),
                "qty_sold": qty_sold,
                "mrp": mrp,
                "amount": amount
            })
            
        df_sales = pd.DataFrame(sales)
        sales_path = os.path.join(out_dir, "sales.csv")
        df_sales.to_csv(sales_path, index=False)
        logger.info(f"Saved {len(df_sales)} sales records to {sales_path}")

        # 3. Generate 3 Voucher/Credit Note pairs with discrepancies
        # Pair 1: Covers all 6 cases
        v1_items = [
            # MATCHED_OK
            {"Product Name": "Dolo 650", "Batch": "A1001", "MRP": 30.90, "Qty": 50, "Amount": 1545.00},
            # MRP_MISMATCH
            {"Product Name": "Augmentin", "Batch": "B2002", "MRP": 223.10, "Qty": 20, "Amount": 4462.00},
            # QTY_MISMATCH
            {"Product Name": "Pantop", "Batch": "A3003", "MRP": 120.00, "Qty": 40, "Amount": 4800.00},
            # AMOUNT_MISMATCH
            {"Product Name": "Combiflam", "Batch": "B4004", "MRP": 45.00, "Qty": 100, "Amount": 4500.00},
            # MISSING_IN_CREDIT_NOTE
            {"Product Name": "Pan D", "Batch": "A5005", "MRP": 199.50, "Qty": 15, "Amount": 2992.50}
        ]
        
        cn1_items = [
            # MATCHED_OK
            {"Product Name": "Dolo 650", "Batch": "A1001", "MRP": 30.90, "Qty": 50, "Amount": 1545.00},
            # MRP_MISMATCH (mismatching MRP)
            {"Product Name": "Augmentin", "Batch": "B2002", "MRP": 210.00, "Qty": 20, "Amount": 4200.00},
            # QTY_MISMATCH (mismatching Qty)
            {"Product Name": "Pantop", "Batch": "A3003", "MRP": 120.00, "Qty": 35, "Amount": 4200.00},
            # AMOUNT_MISMATCH (mismatching Amount)
            {"Product Name": "Combiflam", "Batch": "B4004", "MRP": 45.00, "Qty": 100, "Amount": 4100.00},
            # MISSING_IN_VOUCHER
            {"Product Name": "Azithromycin 500mg", "Batch": "B6006", "MRP": 119.00, "Qty": 10, "Amount": 1190.00}
        ]

        # Pair 2: Simpler subset of discrepancies
        v2_items = [
            {"Product Name": "Metformin 500mg", "Batch": "A7007", "MRP": 55.00, "Qty": 80, "Amount": 4400.00},
            {"Product Name": "Calpol", "Batch": "B8008", "MRP": 15.50, "Qty": 200, "Amount": 3100.00},
            {"Product Name": "Dolo 650", "Batch": "A9009", "MRP": 30.90, "Qty": 60, "Amount": 1854.00}
        ]
        
        cn2_items = [
            {"Product Name": "Metformin 500mg", "Batch": "A7007", "MRP": 55.00, "Qty": 80, "Amount": 4400.00},
            {"Product Name": "Calpol", "Batch": "B8008", "MRP": 15.50, "Qty": 180, "Amount": 2790.00}, # QTY_MISMATCH
            {"Product Name": "Pan D", "Batch": "B9999", "MRP": 199.50, "Qty": 5, "Amount": 997.50}      # MISSING_IN_VOUCHER
        ]

        # Pair 3: Fully matched to verify a clean scenario, plus one missing item
        v3_items = [
            {"Product Name": "Azithromycin 500mg", "Batch": "A8888", "MRP": 119.00, "Qty": 15, "Amount": 1785.00},
            {"Product Name": "Pantop", "Batch": "B7777", "MRP": 120.00, "Qty": 30, "Amount": 3600.00}
        ]
        
        cn3_items = [
            {"Product Name": "Azithromycin 500mg", "Batch": "A8888", "MRP": 119.00, "Qty": 15, "Amount": 1785.00},
            {"Product Name": "Pantop", "Batch": "B7777", "MRP": 120.00, "Qty": 30, "Amount": 3600.00}
        ]

        pairs = [
            ("voucher_1", v1_items, "credit_note_1", cn1_items),
            ("voucher_2", v2_items, "credit_note_2", cn2_items),
            ("voucher_3", v3_items, "credit_note_3", cn3_items)
        ]

        for v_name, v_data, c_name, c_data in pairs:
            # Create DataFrames
            df_v = pd.DataFrame(v_data)
            df_c = pd.DataFrame(c_data)
            
            # Save as CSV
            v_csv = os.path.join(out_dir, f"{v_name}.csv")
            c_csv = os.path.join(out_dir, f"{c_name}.csv")
            df_v.to_csv(v_csv, index=False)
            df_c.to_csv(c_csv, index=False)
            
            # Save as Excel (for Excel parsing tests)
            v_xlsx = os.path.join(out_dir, f"{v_name}.xlsx")
            c_xlsx = os.path.join(out_dir, f"{c_name}.xlsx")
            df_v.to_excel(v_xlsx, index=False)
            df_c.to_excel(c_xlsx, index=False)
            
            logger.info(f"Saved {v_name} and {c_name} in both CSV and XLSX formats.")

        logger.info("Dummy data generation completed successfully!")
    except Exception as e:
        logger.error(f"Error generating dummy data: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    generate_data()
