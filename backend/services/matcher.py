"""
Reconciliation Engine - Fuzzy Matcher

Uses RapidFuzz to match items between vouchers and credit notes based on fuzzy product names
and batch numbers. Returns a merged DataFrame for discrepancy analysis.
"""

import logging
import pandas as pd
import numpy as np
from rapidfuzz import fuzz

logger = logging.getLogger(__name__)

def fuzzy_match_items(df_voucher: pd.DataFrame, df_credit: pd.DataFrame, threshold: int = 85) -> pd.DataFrame:
    """
    Fuzzy matches items between a voucher DataFrame and a credit note DataFrame.
    
    Performs a fuzzy outer join. Matches are determined primarily by product_name similarity 
    (above the threshold) and prioritized by batch_no similarity.
    
    Args:
        df_voucher (pd.DataFrame): Normalized voucher DataFrame.
        df_credit (pd.DataFrame): Normalized credit note DataFrame.
        threshold (int): Minimum similarity score (0-100) for product name matching. Defaults to 85.
        
    Returns:
        pd.DataFrame: Merged DataFrame with columns suffixed with '_voucher' and '_credit'.
    """
    logger.info(f"Starting fuzzy matching with threshold {threshold}...")
    
    # Track which rows are matched
    matched_voucher_indices = set()
    matched_credit_indices = set()
    
    # Store matched rows
    matched_rows = []
    
    # 1. Find matches for each voucher row
    for v_idx, v_row in df_voucher.iterrows():
        best_c_idx = None
        best_score = -1
        
        v_product = str(v_row["product_name"]).strip()
        v_batch = str(v_row["batch_no"]).strip()
        
        for c_idx, c_row in df_credit.iterrows():
            if c_idx in matched_credit_indices:
                continue
                
            c_product = str(c_row["product_name"]).strip()
            c_batch = str(c_row["batch_no"]).strip()
            
            # Compute product name similarity using token_sort_ratio
            prod_sim = fuzz.token_sort_ratio(v_product.lower(), c_product.lower())
            
            if prod_sim >= threshold:
                # Calculate batch match bonus/penalty
                # Exact batch match gets the highest priority
                if v_batch.lower() == c_batch.lower() and v_batch != "nan" and c_batch != "nan":
                    score = prod_sim + 1000  # Strong match
                else:
                    batch_sim = fuzz.ratio(v_batch.lower(), c_batch.lower())
                    if batch_sim >= 80:
                        score = prod_sim + 500  # Moderate match
                    else:
                        score = prod_sim  # Weak match (product matches, batch doesn't)
                        
                if score > best_score:
                    best_score = score
                    best_c_idx = c_idx
                    
        # If a match was found above threshold
        if best_c_idx is not None:
            matched_voucher_indices.add(v_idx)
            matched_credit_indices.add(best_c_idx)
            
            c_row = df_credit.loc[best_c_idx]
            
            # Create a merged row
            merged_row = {
                "product_name_voucher": v_row["product_name"],
                "product_name_credit": c_row["product_name"],
                "batch_no_voucher": v_row["batch_no"],
                "batch_no_credit": c_row["batch_no"],
                "mrp_voucher": v_row["mrp"],
                "mrp_credit": c_row["mrp"],
                "qty_voucher": v_row["qty"],
                "qty_credit": c_row["qty"],
                "amount_voucher": v_row["amount"],
                "amount_credit": c_row["amount"],
                "match_score": best_score if best_score < 1000 else (best_score - 1000)
            }
            matched_rows.append(merged_row)
            
    # 2. Append unmatched voucher rows
    for v_idx, v_row in df_voucher.iterrows():
        if v_idx not in matched_voucher_indices:
            unmatched_row = {
                "product_name_voucher": v_row["product_name"],
                "product_name_credit": np.nan,
                "batch_no_voucher": v_row["batch_no"],
                "batch_no_credit": np.nan,
                "mrp_voucher": v_row["mrp"],
                "mrp_credit": np.nan,
                "qty_voucher": v_row["qty"],
                "qty_credit": np.nan,
                "amount_voucher": v_row["amount"],
                "amount_credit": np.nan,
                "match_score": 0.0
            }
            matched_rows.append(unmatched_row)
            
    # 3. Append unmatched credit note rows
    for c_idx, c_row in df_credit.iterrows():
        if c_idx not in matched_credit_indices:
            unmatched_row = {
                "product_name_voucher": np.nan,
                "product_name_credit": c_row["product_name"],
                "batch_no_voucher": np.nan,
                "batch_no_credit": c_row["batch_no"],
                "mrp_voucher": np.nan,
                "mrp_credit": c_row["mrp"],
                "qty_voucher": np.nan,
                "qty_credit": c_row["qty"],
                "amount_voucher": np.nan,
                "amount_credit": c_row["amount"],
                "match_score": 0.0
            }
            matched_rows.append(unmatched_row)
            
    df_merged = pd.DataFrame(matched_rows)
    logger.info(f"Fuzzy matching completed. Total matched/merged rows: {len(df_merged)}")
    return df_merged
