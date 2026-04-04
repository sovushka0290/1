
import os
import csv
import json
import time
from datetime import datetime
from core.config import log
# Get project root relative to this file

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SHADOW_LEDGER_PATH = os.path.join(PROJECT_ROOT, "public_shadow_ledger.html")


def mirror_to_shadow_ledger(deed_id, description, verdict, tx_hash=None, fraud_reason=None):
    """Duplicates blockchain records to a human-readable public dashboard."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Logic: Keep a local CSV for data
    csv_path = os.path.join(PROJECT_ROOT, "shadow_data.csv")
    file_exists = os.path.isfile(csv_path)
    
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Timestamp", "Deed ID", "Description", "Verdict", "Solana TX", "Status"])
        
        status = "ETCHED" if tx_hash else "BLOCKED"
        writer.writerow([timestamp, deed_id, description[:100], verdict, tx_hash or "N/A", status])

    # Re-generate beautiful HTML for Jury Visualization
    generate_shadow_html(csv_path)

def generate_shadow_html(csv_path):
    """Creates a high-fidelity web dashboard reflecting the ProtoQol ledger."""
    with open(csv_path, "r", encoding="utf-8") as f:
        rows = list(csv.reader(f))[1:] # Skip header
        rows.reverse() # Latest first

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>ProtoQol Public Shadow Ledger</title>
        <style>
            body {{ font-family: 'Inter', sans-serif; background: #0a0a0a; color: #fff; padding: 40px; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            h1 {{ color: #00ffa3; text-transform: uppercase; letter-spacing: 2px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; background: #111; border-radius: 12px; overflow: hidden; }}
            th, td {{ padding: 15px; text-align: left; border-bottom: 1px solid #222; }}
            th {{ background: #1a1a1a; color: #00ffa3; }}
            .verdict-adal {{ color: #00ffa3; font-weight: bold; }}
            .verdict-aram {{ color: #ff0055; font-weight: bold; }}
            .tx-link {{ color: #00d1ff; text-decoration: none; font-size: 0.8em; }}
            .status-badge {{ padding: 4px 8px; border-radius: 4px; font-size: 0.7em; text-transform: uppercase; }}
            .status-etched {{ background: rgba(0, 255, 163, 0.1); color: #00ffa3; border: 1px solid #00ffa3; }}
            .status-blocked {{ background: rgba(255, 0, 85, 0.1); color: #ff0055; border: 1px solid #ff0055; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>ProtoQol // Public Shadow Ledger</h1>
            <p>Real-time Blockchain Mirror & Integrity Audit Feed</p>
            <table>
                <thead>
                    <tr>
                        <th>Time</th>
                        <th>Verdict</th>
                        <th>Description</th>
                        <th>Solana Transaction</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    for r in rows:
        ts, d_id, desc, verdict, tx, status = r
        v_class = "verdict-adal" if verdict == "ADAL" else "verdict-aram"
        s_class = "status-etched" if status == "ETCHED" else "status-blocked"
        tx_link = f'<a href="https://explorer.solana.com/tx/{tx}?cluster=devnet" target="_blank" class="tx-link">{tx[:16]}...</a>' if tx != "N/A" else "N/A"
        
        html_content += f"""
                    <tr>
                        <td>{ts}</td>
                        <td class="{v_class}">{verdict} <span class="status-badge {s_class}">{status}</span></td>
                        <td>{desc}...</td>
                        <td>{tx_link}</td>
                    </tr>
        """
        
    html_content += """
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    
    with open(SHADOW_LEDGER_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)

log.info(f"✓ Shadow Ledger Sync Module Ready at {SHADOW_LEDGER_PATH}")
