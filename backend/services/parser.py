"""
Reconciliation Engine - Document Parser

Responsible for parsing voucher and credit note documents in Excel (and later PDF) formats,
normalizing their schemas, and returning standardized pandas DataFrames.
"""

import os
import logging
import pandas as pd
import numpy as np

# Set up logging
logger = logging.getLogger(__name__)

# Standard schema columns expected by the reconciliation engine
STANDARD_COLUMNS = ["product_name", "batch_no", "mrp", "qty", "amount"]

# Column mapping to normalize Marg ERP and typical voucher formats
COLUMN_MAPPING = {
    "product name": "product_name",
    "productname": "product_name",
    "item name": "product_name",
    "itemname": "product_name",
    "product": "product_name",
    "item": "product_name",
    
    "batch": "batch_no",
    "batch no": "batch_no",
    "batch_no": "batch_no",
    "batchno": "batch_no",
    "batch number": "batch_no",
    
    "mrp": "mrp",
    "m.r.p.": "mrp",
    
    "qty": "qty",
    "quantity": "qty",
    
    "amount": "amount",
    "net amount": "amount",
    "net_amount": "amount",
    "total amount": "amount",
    "val": "amount",
    "value": "amount"
}

def parse_document(file_path: str) -> pd.DataFrame:
    """
    Parses a voucher or credit note document (Excel format supported currently).
    
    Normalizes column names to a standard schema:
    - product_name
    - batch_no
    - mrp
    - qty
    - amount
    
    Missing columns are gracefully filled with NaN.
    
    Args:
        file_path (str): Absolute path to the document file (.xlsx or .xls).
        
    Returns:
        pd.DataFrame: A DataFrame with the normalized standard columns.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file format is unsupported or parsing fails.
    """
    if not os.path.exists(file_path):
        error_msg = f"File not found: {file_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
        
    _, ext = os.path.splitext(file_path.lower())
    
    try:
        if ext in [".xlsx", ".xls"]:
            logger.info(f"Parsing Excel file: {file_path}")
            # Read excel file
            df = pd.read_excel(file_path)
        else:
            # Placeholder for PDF parser branch (Task 5)
            error_msg = f"Unsupported file format for Excel parser: {ext}. PDF branch not implemented yet."
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        # Normalize columns: lowercase, strip, and map using COLUMN_MAPPING
        normalized_cols = []
        for col in df.columns:
            col_str = str(col).strip().lower()
            mapped = COLUMN_MAPPING.get(col_str, col_str)
            normalized_cols.append(mapped)
            
        df.columns = normalized_cols
        
        # Select and reorder columns, adding missing ones with NaN
        final_data = {}
        for col in STANDARD_COLUMNS:
            if col in df.columns:
                # Cast to standard data types if possible
                if col == "mrp" or col == "amount":
                    final_data[col] = pd.to_numeric(df[col], errors="coerce")
                elif col == "qty":
                    final_data[col] = pd.to_numeric(df[col], errors="coerce")
                else:
                    final_data[col] = df[col].astype(str).str.strip()
            else:
                logger.warning(f"Column '{col}' is missing in the file. Gracefully filling with NaN.")
                final_data[col] = np.nan
                
        df_standard = pd.DataFrame(final_data)
        logger.info(f"Successfully parsed and normalized {len(df_standard)} rows from {file_path}")
        return df_standard
        
    except Exception as e:
        error_msg = f"Failed to parse Excel file '{file_path}': {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg) from e
