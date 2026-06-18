"""
Reconciliation Engine - Discrepancy Detector

Evaluates matched and unmatched rows to identify specific discrepancies:
- MISSING_IN_VOUCHER: Item is in credit note but not in voucher.
- MISSING_IN_CREDIT_NOTE: Item is in voucher but not in credit note.
- MRP_MISMATCH: Item MRP differs between voucher and credit note.
- QTY_MISMATCH: Item quantity differs between voucher and credit note.
- AMOUNT_MISMATCH: Item total amount differs between voucher and credit note.
- MATCHED_OK: Perfect agreement in MRP, Qty, and Amount.
"""

import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

def detect_discrepancies(df_matched: pd.DataFrame) -> pd.DataFrame:
    """
    Evaluates each matched and unmatched row in a merged DataFrame
    and assigns a discrepancy_type category.
    
    Args:
        df_matched (pd.DataFrame): DataFrame output from fuzzy_match_items.
        
    Returns:
        pd.DataFrame: DataFrame with an added 'discrepancy_type' column.
    """
    logger.info("Detecting discrepancies across matched items...")
    
    # Work on a copy to avoid mutating the input DataFrame
    df = df_matched.copy()
    
    discrepancy_types = []
    
    for idx, row in df.iterrows():
        try:
            # Extract names to check for missing rows
            p_voucher = row.get("product_name_voucher")
            p_credit = row.get("product_name_credit")
            
            # Check if missing in voucher
            if pd.isna(p_voucher) or p_voucher == "" or str(p_voucher).strip().lower() == "nan":
                discrepancy_types.append("MISSING_IN_VOUCHER")
                continue
                
            # Check if missing in credit note
            if pd.isna(p_credit) or p_credit == "" or str(p_credit).strip().lower() == "nan":
                discrepancy_types.append("MISSING_IN_CREDIT_NOTE")
                continue
                
            # Extract numeric fields
            mrp_v = row.get("mrp_voucher")
            mrp_c = row.get("mrp_credit")
            qty_v = row.get("qty_voucher")
            qty_c = row.get("qty_credit")
            amt_v = row.get("amount_voucher")
            amt_c = row.get("amount_credit")
            
            # 1. MRP Mismatch check
            if pd.isna(mrp_v) or pd.isna(mrp_c) or abs(float(mrp_v) - float(mrp_c)) > 0.01:
                discrepancy_types.append("MRP_MISMATCH")
                continue
                
            # 2. Quantity Mismatch check
            if pd.isna(qty_v) or pd.isna(qty_c) or abs(float(qty_v) - float(qty_c)) > 0.01:
                discrepancy_types.append("QTY_MISMATCH")
                continue
                
            # 3. Amount Mismatch check
            if pd.isna(amt_v) or pd.isna(amt_c) or abs(float(amt_v) - float(amt_c)) > 0.01:
                discrepancy_types.append("AMOUNT_MISMATCH")
                continue
                
            # If all checks pass
            discrepancy_types.append("MATCHED_OK")
            
        except Exception as e:
            logger.error(f"Error evaluating discrepancy at index {idx}: {str(e)}")
            # Default to AMOUNT_MISMATCH or error indicator
            discrepancy_types.append("AMOUNT_MISMATCH")
            
    df["discrepancy_type"] = discrepancy_types
    logger.info(f"Discrepancy detection complete. Breakdown:\n{df['discrepancy_type'].value_counts()}")
    return df
