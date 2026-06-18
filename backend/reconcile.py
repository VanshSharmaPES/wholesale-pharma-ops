"""
Reconciliation Engine - CLI Entrypoint

Wires together the document parser, fuzzy matcher, discrepancy detector,
and report generator to reconcile retail return requests with wholesaler credit notes.
"""

import sys
import logging
import argparse
from backend.services.parser import parse_document
from backend.services.matcher import fuzzy_match_items
from backend.services.discrepancy import detect_discrepancies
from backend.services.reporter import generate_report

# Configure logging to standard output
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("reconcile_cli")

def run_reconciliation(voucher_path: str, credit_note_path: str, output_path: str) -> None:
    """
    Runs the end-to-end reconciliation pipeline.
    
    Args:
        voucher_path (str): Path to the retail voucher file (.xlsx, .xls, .pdf).
        credit_note_path (str): Path to the credit note file (.xlsx, .xls, .pdf).
        output_path (str): Base output path for CSV and HTML reports.
    """
    logger.info("Starting reconciliation run...")
    try:
        # Step 1: Parse voucher
        logger.info(f"Parsing voucher file: {voucher_path}")
        df_voucher = parse_document(voucher_path)
        
        # Step 2: Parse credit note
        logger.info(f"Parsing credit note file: {credit_note_path}")
        df_credit = parse_document(credit_note_path)
        
        # Step 3: Fuzzy match items
        df_matched = fuzzy_match_items(df_voucher, df_credit)
        
        # Step 4: Detect discrepancies
        df_discrepancies = detect_discrepancies(df_matched)
        
        # Step 5: Generate report
        generate_report(
            df_discrepancies,
            output_path,
            voucher_path=voucher_path,
            credit_note_path=credit_note_path
        )
        
        logger.info("Reconciliation process completed successfully!")
        
    except Exception as e:
        logger.error(f"Reconciliation run failed: {str(e)}", exc_info=True)
        sys.exit(1)

def main() -> None:
    """Parses command-line arguments and triggers reconciliation."""
    parser = argparse.ArgumentParser(
        description="Reconcile Marg ERP retail returns vouchers with wholesale credit notes."
    )
    parser.add_argument(
        "--voucher",
        required=True,
        help="Path to the voucher file (Excel or PDF)."
    )
    parser.add_argument(
        "--credit-note",
        required=True,
        help="Path to the credit note file (Excel or PDF)."
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Base path to save the output reports (extensions .csv and .html will be appended)."
    )
    
    args = parser.parse_command_line_args = parser.parse_args()
    
    run_reconciliation(
        voucher_path=args.voucher,
        credit_note_path=args.credit_note,
        output_path=args.output
    )

if __name__ == "__main__":
    main()
