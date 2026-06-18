"""
Reconciliation Engine - Document Parser

Responsible for parsing voucher and credit note documents in Excel and PDF formats,
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
    "material description": "product_name",
    "materialdescription": "product_name",
    
    "batch": "batch_no",
    "batch no": "batch_no",
    "batch_no": "batch_no",
    "batchno": "batch_no",
    "batch number": "batch_no",
    
    "mrp": "mrp",
    "m.r.p.": "mrp",
    "unit mrp": "mrp",
    
    "qty": "qty",
    "quantity": "qty",
    
    "amount": "amount",
    "net amount": "amount",
    "net_amount": "amount",
    "total amount": "amount",
    "val": "amount",
    "value": "amount",
    "assessable value": "amount",
    "net product value": "amount",
    "product value": "amount"
}

def parse_document(file_path: str) -> pd.DataFrame:
    """
    Parses a voucher or credit note document (Excel or PDF formats).
    
    Normalizes column names to a standard schema:
    - product_name
    - batch_no
    - mrp
    - qty
    - amount
    
    Missing columns are gracefully filled with NaN.
    
    Args:
        file_path (str): Absolute path to the document file (.xlsx, .xls, or .pdf).
        
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
            df = pd.read_excel(file_path)
            return _normalize_excel_df(df)
        elif ext == ".pdf":
            logger.info(f"Parsing PDF file: {file_path}")
            return _parse_pdf(file_path)
        else:
            error_msg = f"Unsupported file format: {ext}"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
    except Exception as e:
        error_msg = f"Failed to parse file '{file_path}': {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg) from e

def _normalize_excel_df(df: pd.DataFrame) -> pd.DataFrame:
    """Normalizes the column schema of an Excel DataFrame."""
    normalized_cols = []
    for col in df.columns:
        col_str = str(col).strip().lower()
        mapped = COLUMN_MAPPING.get(col_str, col_str)
        normalized_cols.append(mapped)
        
    df.columns = normalized_cols
    
    final_data = {}
    for col in STANDARD_COLUMNS:
        if col in df.columns:
            if col in ["mrp", "qty", "amount"]:
                final_data[col] = pd.to_numeric(df[col], errors="coerce")
            else:
                final_data[col] = df[col].astype(str).str.strip()
        else:
            logger.warning(f"Column '{col}' is missing. Filling with NaN.")
            final_data[col] = np.nan
            
    return pd.DataFrame(final_data)

def _parse_pdf(file_path: str) -> pd.DataFrame:
    """Helper to parse a PDF file using pdfplumber."""
    import pdfplumber
    all_rows = []
    
    with pdfplumber.open(file_path) as pdf:
        for page_idx, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            if not tables:
                logger.warning(f"No tables found on page {page_idx + 1}")
                continue
                
            for table in tables:
                if len(table) < 2:
                    continue
                
                # 1. Detect header mapping dynamically by scanning top rows
                header_mapping = {}
                last_header_row_idx = -1
                
                # Scan top rows to detect headers (handles multi-row headers)
                for row_idx, row in enumerate(table[:10]):
                    cleaned_row = [
                        str(cell).strip().lower().replace('\n', ' ')
                        if cell is not None else ""
                        for cell in row
                    ]
                    
                    row_matches = 0
                    for cell_idx, cell in enumerate(cleaned_row):
                        if not cell:
                            continue
                        
                        # Try exact match first
                        if cell in COLUMN_MAPPING:
                            header_mapping[COLUMN_MAPPING[cell]] = cell_idx
                            row_matches += 1
                            continue
                            
                        # Try substring match fallback, sorted by key length descending
                        matched = False
                        for key in sorted(COLUMN_MAPPING.keys(), key=len, reverse=True):
                            if key in cell:
                                header_mapping[COLUMN_MAPPING[key]] = cell_idx
                                row_matches += 1
                                matched = True
                                break
                            
                    if row_matches >= 2:
                        last_header_row_idx = max(last_header_row_idx, row_idx)
                        
                if last_header_row_idx == -1:
                    logger.warning(f"No clear header detected on page {page_idx + 1}. Defaulting to row 0.")
                    last_header_row_idx = 0
                    for cell_idx, cell in enumerate(table[0]):
                        if cell:
                            cell_cleaned = str(cell).strip().lower().replace('\n', ' ')
                            if cell_cleaned in COLUMN_MAPPING:
                                header_mapping[COLUMN_MAPPING[cell_cleaned]] = cell_idx
                            else:
                                for key in sorted(COLUMN_MAPPING.keys(), key=len, reverse=True):
                                    if key in cell_cleaned:
                                        header_mapping[COLUMN_MAPPING[key]] = cell_idx
                                        break
                
                # Set fallback defaults for indices if not detected
                if "product_name" not in header_mapping:
                    header_mapping["product_name"] = 1
                if "batch_no" not in header_mapping:
                    header_mapping["batch_no"] = 2
                
                default_indices = {"mrp": 3, "qty": 4, "amount": 5}
                for col, def_idx in default_indices.items():
                    if col not in header_mapping:
                        header_mapping[col] = min(def_idx, len(table[0]) - 1)
                
                # 2. Extract data rows
                for row in table[last_header_row_idx + 1:]:
                    if not any(row):
                        continue
                    
                    # Skip total/summary rows
                    first_cell = str(row[0]).strip().lower() if row[0] is not None else ""
                    if "total" in first_cell or "grand total" in first_cell:
                        continue
                        
                    row_data = {}
                    for col_name in STANDARD_COLUMNS:
                        idx = header_mapping.get(col_name)
                        if idx is not None and idx < len(row):
                            cell_val = row[idx]
                            if cell_val is None:
                                row_data[col_name] = np.nan
                                continue
                                
                            cell_str = str(cell_val).strip()
                            
                            if col_name == "product_name":
                                # Remove newlines in names
                                row_data[col_name] = " ".join(cell_str.split("\n")).strip()
                            elif col_name == "batch_no":
                                # Extract first line as batch
                                row_data[col_name] = cell_str.split("\n")[0].strip()
                            elif col_name in ["mrp", "qty", "amount"]:
                                lines = [line.strip().replace(",", "") for line in cell_str.split("\n") if line.strip()]
                                num_val = None
                                for line in lines:
                                    try:
                                        num_val = float(line)
                                        break
                                    except ValueError:
                                        # Remove unit names and try again
                                        cleaned = "".join(c for c in line if c.isdigit() or c == '.')
                                        try:
                                            num_val = float(cleaned)
                                            break
                                        except ValueError:
                                            pass
                                row_data[col_name] = num_val if num_val is not None else np.nan
                        else:
                            row_data[col_name] = np.nan
                            
                    # Filter out rows with no product name or batch
                    p_name = row_data.get("product_name")
                    if not p_name or p_name == "nan" or p_name == "":
                        continue
                        
                    all_rows.append(row_data)
                    
    df_out = pd.DataFrame(all_rows)
    if df_out.empty:
        df_out = pd.DataFrame(columns=STANDARD_COLUMNS)
    return df_out
