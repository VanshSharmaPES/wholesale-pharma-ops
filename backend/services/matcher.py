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

def _aggregate_df(df: pd.DataFrame) -> pd.DataFrame:
    """Groups the DataFrame by product name and batch number to aggregate quantities and values."""
    if df.empty:
        return df
        
    df_temp = df.copy()
    
    # We want to group by case-insensitive name and batch
    df_temp["prod_key"] = df_temp["product_name"].astype(str).str.strip().str.upper()
    df_temp["batch_key"] = df_temp["batch_no"].astype(str).str.strip().str.upper()
    
    agg_funcs = {
        "product_name": "first",
        "batch_no": "first",
        "mrp": "first",
        "qty": "sum",
        "amount": "sum"
    }
    
    # Preserve any other columns
    for col in df.columns:
        if col not in agg_funcs:
            agg_funcs[col] = "first"
            
    df_grouped = df_temp.groupby(["prod_key", "batch_key"], as_index=False).agg(agg_funcs)
    
    # Remove temporary grouping keys
    if "prod_key" in df_grouped.columns:
        df_grouped = df_grouped.drop(columns=["prod_key"])
    if "batch_key" in df_grouped.columns:
        df_grouped = df_grouped.drop(columns=["batch_key"])
        
    return df_grouped

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
    # Aggregate inputs to handle split rows (e.g. same product/batch split on voucher or credited as total)
    df_voucher = _aggregate_df(df_voucher)
    df_credit = _aggregate_df(df_credit)
    
    logger.info(f"Starting fuzzy matching with threshold {threshold}...")
    
    # Track which rows are matched
    matched_voucher_indices = set()
    matched_credit_indices = set()
    
    # Store matched rows
    matched_rows = []
    
    # Pass 1: Exact Batch Match + Moderate Name Similarity (>= 45)
    for v_idx, v_row in df_voucher.iterrows():
        v_product = str(v_row["product_name"]).strip()
        v_batch = str(v_row["batch_no"]).strip().lower()
        
        if not v_batch or v_batch in ["nan", "none", ""]:
            continue
            
        best_c_idx = None
        best_sim = -1
        
        for c_idx, c_row in df_credit.iterrows():
            if c_idx in matched_credit_indices:
                continue
                
            c_product = str(c_row["product_name"]).strip()
            c_batch = str(c_row["batch_no"]).strip().lower()
            
            if c_batch == v_batch:
                # Compute name similarity using both token_sort_ratio and token_set_ratio
                prod_sim = max(
                    fuzz.token_sort_ratio(v_product.lower(), c_product.lower()),
                    fuzz.token_set_ratio(v_product.lower(), c_product.lower())
                )
                
                if prod_sim >= 45 and prod_sim > best_sim:
                    best_sim = prod_sim
                    best_c_idx = c_idx
                    
        if best_c_idx is not None:
            matched_voucher_indices.add(v_idx)
            matched_credit_indices.add(best_c_idx)
            c_row = df_credit.loc[best_c_idx]
            
            # Exact batch matches are high quality
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
                "match_score": float(best_sim)
            }
            matched_rows.append(merged_row)
            
    # Pass 2: Fuzzy Name Match (similarity >= threshold) + Fuzzy Batch Match Bonus
    for v_idx, v_row in df_voucher.iterrows():
        if v_idx in matched_voucher_indices:
            continue
            
        v_product = str(v_row["product_name"]).strip()
        v_batch = str(v_row["batch_no"]).strip()
        
        best_c_idx = None
        best_score = -1
        
        for c_idx, c_row in df_credit.iterrows():
            if c_idx in matched_credit_indices:
                continue
                
            c_product = str(c_row["product_name"]).strip()
            c_batch = str(c_row["batch_no"]).strip()
            
            # Use max of token_sort_ratio and token_set_ratio for more flexible matching
            prod_sim = max(
                fuzz.token_sort_ratio(v_product.lower(), c_product.lower()),
                fuzz.token_set_ratio(v_product.lower(), c_product.lower())
            )
            
            if prod_sim >= threshold:
                # Calculate batch match bonus/penalty
                if v_batch.lower() == c_batch.lower() and v_batch.lower() not in ["nan", "none", ""]:
                    score = prod_sim + 1000  # Exact batch match gets the highest priority
                else:
                    batch_sim = fuzz.ratio(v_batch.lower(), c_batch.lower())
                    if batch_sim >= 80:
                        score = prod_sim + 500  # Moderate batch match
                    else:
                        score = prod_sim  # Product matches, batch doesn't
                        
                if score > best_score:
                    best_score = score
                    best_c_idx = c_idx
                    
        if best_c_idx is not None:
            matched_voucher_indices.add(v_idx)
            matched_credit_indices.add(best_c_idx)
            c_row = df_credit.loc[best_c_idx]
            
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
                "match_score": float(best_score if best_score < 1000 else (best_score - 1000))
            }
            matched_rows.append(merged_row)
            
    # 3. Append unmatched voucher rows
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
            
    # 4. Append unmatched credit note rows
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
