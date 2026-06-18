"""
Reconciliation Engine - Report Generator

Generates CSV and styled HTML discrepancy reports from the reconciliation engine output.
"""

import os
import logging
import base64
import mimetypes
from datetime import datetime
import pandas as pd
from jinja2 import Template

logger = logging.getLogger(__name__)

# Premium glassmorphic HTML template for reconciliation reports
HTML_REPORT_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Marg ERP Reconciliation Report</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #f8fafc;
            --bg-card: rgba(255, 255, 255, 0.85);
            --border-color: #e2e8f0;
            --text-primary: #0f172a;
            --text-secondary: #475569;
            
            /* Status Colors */
            --color-matched: #10b981;
            --bg-matched: #ecfdf5;
            --color-mrp: #f97316;
            --bg-mrp: #fff7ed;
            --color-qty: #8b5cf6;
            --bg-qty: #f5f3ff;
            --color-amount: #ef4444;
            --bg-amount: #fef2f2;
            --color-missing-cn: #3b82f6;
            --bg-missing-cn: #eff6ff;
            --color-missing-v: #eab308;
            --bg-missing-v: #fef9c3;
        }

        body {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            margin: 0;
            padding: 40px 20px;
            min-height: 100vh;
            background-image: 
                radial-gradient(at 0% 0%, rgba(79, 70, 229, 0.05) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(124, 58, 237, 0.05) 0px, transparent 50%);
        }

        .container {
            max-width: 1280px;
            margin: 0 auto;
        }

        header {
            margin-bottom: 40px;
            animation: fadeIn 0.8s ease-out;
        }

        h1 {
            font-family: 'Outfit', sans-serif;
            font-size: 2.5rem;
            font-weight: 700;
            margin: 0 0 10px 0;
            background: linear-gradient(135deg, #4f46e5, #7c3aed);
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .meta-info {
            font-size: 0.95rem;
            color: var(--text-secondary);
        }

        /* Summary Cards Grid */
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
            animation: slideUp 0.8s ease-out;
        }

        .card {
            background: var(--bg-card);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            cursor: pointer;
        }

        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 20px -8px rgba(79, 70, 229, 0.15);
            border-color: rgba(79, 70, 229, 0.3);
        }

        .card.active {
            border-color: #4f46e5;
            box-shadow: 0 12px 20px -8px rgba(79, 70, 229, 0.25);
            background: rgba(255, 255, 255, 0.95);
            transform: translateY(-2px) scale(1.02);
        }

        .card-title {
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-secondary);
            margin-bottom: 8px;
        }

        .card-value {
            font-family: 'Outfit', sans-serif;
            font-size: 2rem;
            font-weight: 700;
            color: var(--text-primary);
        }

        .card-value.amount {
            color: #4f46e5;
        }

        /* Table Card */
        .table-card {
            background: var(--bg-card);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
            overflow: hidden;
            animation: slideUp 1s ease-out;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }

        th {
            background-color: rgba(241, 245, 249, 0.8);
            font-weight: 600;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-secondary);
            padding: 16px 24px;
            border-bottom: 1px solid var(--border-color);
        }

        td {
            padding: 18px 24px;
            border-bottom: 1px solid var(--border-color);
            font-size: 0.95rem;
            vertical-align: middle;
            transition: background-color 0.2s ease;
        }

        tr:last-child td {
            border-bottom: none;
        }

        tr:hover td {
            background-color: rgba(248, 250, 252, 0.6);
        }

        /* Status Badge */
        .badge {
            display: inline-flex;
            align-items: center;
            padding: 6px 12px;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 0.02em;
        }

        .badge-matched_ok { color: var(--color-matched); background: var(--bg-matched); }
        .badge-mrp_mismatch { color: var(--color-mrp); background: var(--bg-mrp); }
        .badge-qty_mismatch { color: var(--color-qty); background: var(--bg-qty); }
        .badge-amount_mismatch { color: var(--color-amount); background: var(--bg-amount); }
        .badge-missing_in_credit_note { color: var(--color-missing-cn); background: var(--bg-missing-cn); }
        .badge-missing_in_voucher { color: var(--color-missing-v); background: var(--bg-missing-v); }

        /* Mismatch Indicators */
        .diff-value {
            font-size: 0.8rem;
            color: #ef4444;
            display: block;
            margin-top: 2px;
        }

        .original-value {
            color: var(--text-secondary);
        }

        .empty-cell {
            color: #cbd5e1;
            font-style: italic;
        }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        @keyframes slideUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Source Files Container & Link Cards */
        .source-files-container {
            display: flex;
            gap: 16px;
            margin-top: 20px;
            flex-wrap: wrap;
            animation: fadeIn 1s ease-out;
        }

        .file-link-card {
            display: flex;
            align-items: center;
            gap: 14px;
            background: var(--bg-card);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 12px 18px;
            text-decoration: none;
            color: var(--text-primary);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.03);
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            min-width: 250px;
        }

        .file-link-card:hover {
            transform: translateY(-2px);
            border-color: rgba(79, 70, 229, 0.4);
            box-shadow: 0 10px 15px -3px rgba(79, 70, 229, 0.1);
            background: rgba(255, 255, 255, 0.95);
        }

        .file-icon {
            font-size: 1.5rem;
        }

        .file-details {
            display: flex;
            flex-direction: column;
            gap: 2px;
        }

        .file-label {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-secondary);
            font-weight: 600;
        }

        .file-name {
            font-size: 0.85rem;
            font-weight: 500;
            color: #4f46e5;
            word-break: break-all;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Marg ERP Reconciliation Report</h1>
            <div class="meta-info">
                Wholesale Shop: Amritsar Branch &bull; Generated: {{ timestamp }} &bull; Total Checked Rows: {{ total_items }}
            </div>
            {% if voucher_url or credit_note_url %}
            <div class="source-files-container">
                {% if voucher_url %}
                <a href="#" id="voucher-file-link" data-file="{{ voucher_url }}" data-name="{{ voucher_filename }}" class="file-link-card" title="Open {{ voucher_filename }}">
                    <span class="file-icon">📄</span>
                    <div class="file-details">
                        <span class="file-label">Source Retail Voucher</span>
                        <span class="file-name">{{ voucher_filename }}</span>
                    </div>
                </a>
                {% endif %}
                {% if credit_note_url %}
                <a href="#" id="credit-note-file-link" data-file="{{ credit_note_url }}" data-name="{{ credit_note_filename }}" class="file-link-card" title="Open {{ credit_note_filename }}">
                    <span class="file-icon">🧾</span>
                    <div class="file-details">
                        <span class="file-label">Wholesaler Credit Note</span>
                        <span class="file-name">{{ credit_note_filename }}</span>
                    </div>
                </a>
                {% endif %}
            </div>
            {% endif %}
        </header>

        <div class="summary-grid">
            <div class="card" data-status="all">
                <div class="card-title">Total Items</div>
                <div class="card-value">{{ total_items }}</div>
            </div>
            <div class="card" style="border-left: 4px solid var(--color-matched)" data-status="MATCHED_OK">
                <div class="card-title">Matched OK</div>
                <div class="card-value" style="color: var(--color-matched)">{{ stats.MATCHED_OK }}</div>
            </div>
            <div class="card" style="border-left: 4px solid var(--color-mrp)" data-status="MRP_MISMATCH">
                <div class="card-title">MRP Mismatch</div>
                <div class="card-value" style="color: var(--color-mrp)">{{ stats.MRP_MISMATCH }}</div>
            </div>
            <div class="card" style="border-left: 4px solid var(--color-qty)" data-status="QTY_MISMATCH">
                <div class="card-title">Qty Mismatch</div>
                <div class="card-value" style="color: var(--color-qty)">{{ stats.QTY_MISMATCH }}</div>
            </div>
            <div class="card" style="border-left: 4px solid var(--color-amount)" data-status="AMOUNT_MISMATCH">
                <div class="card-title">Amount Mismatch</div>
                <div class="card-value" style="color: var(--color-amount)">{{ stats.AMOUNT_MISMATCH }}</div>
            </div>
            <div class="card" style="border-left: 4px solid var(--color-missing-cn)" data-status="MISSING_IN_CREDIT_NOTE">
                <div class="card-title">Missing in Wholesaler</div>
                <div class="card-value" style="color: var(--color-missing-cn)">{{ stats.MISSING_IN_CREDIT_NOTE }}</div>
            </div>
            <div class="card" style="border-left: 4px solid var(--color-missing-v)" data-status="MISSING_IN_VOUCHER">
                <div class="card-title">Missing in Voucher</div>
                <div class="card-value" style="color: var(--color-missing-v)">{{ stats.MISSING_IN_VOUCHER }}</div>
            </div>
        </div>

        <div class="table-card">
            <table>
                <thead>
                    <tr>
                        <th>Product (Voucher / Credit Note)</th>
                        <th>Batch (V / CN)</th>
                        <th>MRP</th>
                        <th>QTY</th>
                        <th>Amount</th>
                        <th>Discrepancy Status</th>
                    </tr>
                </thead>
                <tbody>
                    {% for row in rows %}
                    <tr data-status="{{ row.discrepancy_type }}">
                        <td>
                            {% if row.product_name_voucher %}
                                <div class="original-value">{{ row.product_name_voucher }}</div>
                            {% else %}
                                <span class="empty-cell">N/A</span>
                            {% endif %}
                            
                            {% if row.product_name_credit and row.product_name_credit != row.product_name_voucher %}
                                <div class="diff-value">CN: {{ row.product_name_credit }}</div>
                            {% endif %}
                        </td>
                        <td>
                            {% if row.batch_no_voucher %}
                                <div class="original-value">{{ row.batch_no_voucher }}</div>
                            {% else %}
                                <span class="empty-cell">N/A</span>
                            {% endif %}
                            
                            {% if row.batch_no_credit and row.batch_no_credit != row.batch_no_voucher %}
                                <div class="diff-value">CN: {{ row.batch_no_credit }}</div>
                            {% endif %}
                        </td>
                        <td>
                            {% if row.mrp_voucher is not none and not row.mrp_voucher_isna %}
                                <span class="original-value">₹{{ "%.2f"|format(row.mrp_voucher) }}</span>
                            {% else %}
                                <span class="empty-cell">N/A</span>
                            {% endif %}
                            
                            {% if row.mrp_credit is not none and not row.mrp_credit_isna and row.mrp_credit != row.mrp_voucher %}
                                <div class="diff-value">CN: ₹{{ "%.2f"|format(row.mrp_credit) }}</div>
                            {% endif %}
                        </td>
                        <td>
                            {% if row.qty_voucher is not none and not row.qty_voucher_isna %}
                                <span class="original-value">{{ row.qty_voucher }}</span>
                            {% else %}
                                <span class="empty-cell">N/A</span>
                            {% endif %}
                            
                            {% if row.qty_credit is not none and not row.qty_credit_isna and row.qty_credit != row.qty_voucher %}
                                <div class="diff-value">CN: {{ row.qty_credit }}</div>
                            {% endif %}
                        </td>
                        <td>
                            {% if row.amount_voucher is not none and not row.amount_voucher_isna %}
                                <span class="original-value">₹{{ "%.2f"|format(row.amount_voucher) }}</span>
                            {% else %}
                                <span class="empty-cell">N/A</span>
                            {% endif %}
                            
                            {% if row.amount_credit is not none and not row.amount_credit_isna and row.amount_credit != row.amount_voucher %}
                                <div class="diff-value">CN: ₹{{ "%.2f"|format(row.amount_credit) }}</div>
                            {% endif %}
                        </td>
                        <td>
                            <span class="badge badge-{{ row.discrepancy_type|lower }}">{{ row.discrepancy_type.replace('_', ' ') }}</span>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    <script>
        function openEmbeddedFile(dataUri, filename) {
            try {
                const parts = dataUri.split(',');
                const contentType = parts[0].split(':')[1].split(';')[0];
                const byteCharacters = atob(parts[1]);
                const byteNumbers = new Array(byteCharacters.length);
                for (let i = 0; i < byteCharacters.length; i++) {
                    byteNumbers[i] = byteCharacters.charCodeAt(i);
                }
                const byteArray = new Uint8Array(byteNumbers);
                const blob = new Blob([byteArray], {type: contentType});
                const fileURL = URL.createObjectURL(blob);
                
                if (contentType === 'application/pdf') {
                    window.open(fileURL, '_blank');
                } else {
                    const link = document.createElement('a');
                    link.href = fileURL;
                    link.download = filename;
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                }
            } catch (e) {
                console.error('Failed to open embedded file:', e);
                alert('Could not open embedded file: ' + e.message);
            }
        }

        document.addEventListener('DOMContentLoaded', () => {
            const cards = document.querySelectorAll('.summary-grid .card');
            const rows = document.querySelectorAll('table tbody tr');

            cards.forEach(card => {
                card.addEventListener('click', () => {
                    const targetStatus = card.getAttribute('data-status');
                    
                    // Toggle active class
                    cards.forEach(c => c.classList.remove('active'));
                    card.classList.add('active');

                    // Filter rows
                    rows.forEach(row => {
                        const rowStatus = row.getAttribute('data-status');
                        if (targetStatus === 'all' || rowStatus === targetStatus) {
                            row.style.display = '';
                        } else {
                            row.style.display = 'none';
                        }
                    });
                });
            });
            
            // Activate 'Total Items' card by default
            const totalCard = document.querySelector('.summary-grid .card[data-status="all"]');
            if (totalCard) totalCard.classList.add('active');

            // Source files opening logic
            const voucherLink = document.getElementById('voucher-file-link');
            if (voucherLink) {
                voucherLink.addEventListener('click', (e) => {
                    e.preventDefault();
                    openEmbeddedFile(voucherLink.getAttribute('data-file'), voucherLink.getAttribute('data-name'));
                });
            }

            const creditLink = document.getElementById('credit-note-file-link');
            if (creditLink) {
                creditLink.addEventListener('click', (e) => {
                    e.preventDefault();
                    openEmbeddedFile(creditLink.getAttribute('data-file'), creditLink.getAttribute('data-name'));
                });
            }
        });
    </script>
</body>
</html>
"""

def generate_report(
    df_discrepancy: pd.DataFrame, 
    output_path: str, 
    voucher_path: str = None, 
    credit_note_path: str = None
) -> None:
    """
    Saves the discrepancy DataFrame as both a CSV and a styled HTML file.
    
    Args:
        df_discrepancy (pd.DataFrame): The reconciled DataFrame containing the discrepancy_type column.
        output_path (str): Base output path. Sub-reports (CSV and HTML) will append their extensions.
        voucher_path (str, optional): Path to the source voucher file.
        credit_note_path (str, optional): Path to the source credit note file.
        
    Raises:
        IOError: If files cannot be saved to the destination path.
    """
    try:
        # Determine base path and extension
        base_path, _ = os.path.splitext(output_path)
        csv_path = base_path + ".csv"
        html_path = base_path + ".html"
        
        logger.info(f"Generating reports. Target CSV: {csv_path}, Target HTML: {html_path}")
        
        # Embed voucher and credit note as base64 data URIs for the HTML report
        abs_voucher_url = None
        abs_credit_url = None
        
        if voucher_path and os.path.exists(voucher_path):
            try:
                mime_type, _ = mimetypes.guess_type(voucher_path)
                if not mime_type:
                    mime_type = "application/octet-stream"
                with open(voucher_path, "rb") as f:
                    b64_data = base64.b64encode(f.read()).decode("utf-8")
                abs_voucher_url = f"data:{mime_type};base64,{b64_data}"
            except Exception as e:
                logger.warning(f"Could not embed voucher file {voucher_path}: {e}")
            
        if credit_note_path and os.path.exists(credit_note_path):
            try:
                mime_type, _ = mimetypes.guess_type(credit_note_path)
                if not mime_type:
                    mime_type = "application/octet-stream"
                with open(credit_note_path, "rb") as f:
                    b64_data = base64.b64encode(f.read()).decode("utf-8")
                abs_credit_url = f"data:{mime_type};base64,{b64_data}"
            except Exception as e:
                logger.warning(f"Could not embed credit note file {credit_note_path}: {e}")
            
        # Ensure target directory exists
        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
            
        # 1. Save CSV
        df_discrepancy.to_csv(csv_path, index=False)
        logger.info(f"Successfully saved CSV report to {csv_path}")
        
        # 2. Compile stats
        total_items = len(df_discrepancy)
        stats = {
            "MATCHED_OK": 0,
            "MRP_MISMATCH": 0,
            "QTY_MISMATCH": 0,
            "AMOUNT_MISMATCH": 0,
            "MISSING_IN_CREDIT_NOTE": 0,
            "MISSING_IN_VOUCHER": 0
        }
        
        # Count actual status frequencies
        counts = df_discrepancy["discrepancy_type"].value_counts().to_dict()
        for key in stats:
            stats[key] = counts.get(key, 0)
            
        # 3. Format row data for Jinja rendering (handles NaNs gracefully)
        rows_to_render = []
        for _, row in df_discrepancy.iterrows():
            row_dict = row.to_dict()
            
            # Add helper fields to easily handle NaN checks in Jinja
            row_dict["mrp_voucher_isna"] = pd.isna(row["mrp_voucher"])
            row_dict["mrp_credit_isna"] = pd.isna(row["mrp_credit"])
            row_dict["qty_voucher_isna"] = pd.isna(row["qty_voucher"])
            row_dict["qty_credit_isna"] = pd.isna(row["qty_credit"])
            row_dict["amount_voucher_isna"] = pd.isna(row["amount_voucher"])
            row_dict["amount_credit_isna"] = pd.isna(row["amount_credit"])
            
            rows_to_render.append(row_dict)
            
        # 4. Render HTML Report
        template = Template(HTML_REPORT_TEMPLATE)
        timestamp_str = datetime.now().strftime("%Y-%m-%d %I:%M %p")
        
        html_content = template.render(
            timestamp=timestamp_str,
            total_items=total_items,
            stats=stats,
            rows=rows_to_render,
            voucher_url=abs_voucher_url,
            credit_note_url=abs_credit_url,
            voucher_filename=os.path.basename(voucher_path) if voucher_path else None,
            credit_note_filename=os.path.basename(credit_note_path) if credit_note_path else None
        )
        
        # Write HTML file
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        logger.info(f"Successfully saved styled HTML report to {html_path}")
        
    except Exception as e:
        error_msg = f"Failed to generate reports at '{output_path}': {str(e)}"
        logger.error(error_msg)
        raise IOError(error_msg) from e
