import requests
import duckdb
import pandas as pd
from datetime import datetime
import os
import json  # <--- NEW: Needed for proper JSON formatting
from dotenv import load_dotenv

# Load env variables
load_dotenv()
API_KEY = os.getenv("HELIUS_API_KEY")
ADDRESS = os.getenv("MY_WALLET")  

DB_FILE = "solana_tracker.db"

def init_db():
    conn = duckdb.connect(DB_FILE)
    # create table if it doesn't exist
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            signature VARCHAR PRIMARY KEY,
            timestamp TIMESTAMP,
            type VARCHAR,
            token_mint VARCHAR,
            token_amount DOUBLE,
            raw_data JSON
        )
    """)
    conn.close()

def fetch_and_update():
    # Safety Check
    if not API_KEY or not ADDRESS:
        return f"❌ Error: Could not find keys. Check .env (Got: {str(API_KEY)[:5]}... / {str(ADDRESS)[:5]}...)"

    conn = duckdb.connect(DB_FILE)
    
    # Get last transaction signature to avoid re-downloading history
    try:
        last_sig = conn.execute("SELECT signature FROM transactions ORDER BY timestamp DESC LIMIT 1").fetchone()
        last_sig = last_sig[0] if last_sig else None
    except:
        last_sig = None

    url = f"https://api.helius.xyz/v0/addresses/{ADDRESS}/transactions?api-key={API_KEY}"
    if last_sig:
        url += f"&before={last_sig}"
    
    print(f"🌍 Fetching for wallet: {ADDRESS[:6]}... (Last Sig: {str(last_sig)[:10]})")
    
    try:
        response = requests.get(url)
        data = response.json()
        
        # Check for API errors
        if isinstance(data, dict) and 'error' in data:
             return f"❌ Helius API Error: {data['error']}"

        if not isinstance(data, list):
            return "❌ API returned unexpected format."
            
        new_tx_count = 0
        for tx in data:
            sig = tx.get('signature')
            ts = datetime.fromtimestamp(tx.get('timestamp', 0))
            tx_type = tx.get('type', 'UNKNOWN')
            
            # --- PARSING LOGIC ---
            mint = "So11111111111111111111111111111111111111112" # Default SOL
            amt = 0.0

            # 1. Check Token Transfers
            if 'tokenTransfers' in tx and tx['tokenTransfers']:
                for t in tx['tokenTransfers']:
                    if t.get('toUserAccount') == ADDRESS or t.get('fromUserAccount') == ADDRESS:
                        mint = t.get('mint', mint)
                        amt = t.get('tokenAmount', 0)
                        break
            
            # 2. Check Native SOL Transfers
            # If we haven't found a token transfer, check for raw SOL movement
            if amt == 0 and 'nativeTransfers' in tx and tx['nativeTransfers']:
                 for t in tx['nativeTransfers']:
                    raw_amt = t.get('amount', 0)
                    if raw_amt > 0:
                        # 1 SOL = 1,000,000,000 Lamports
                        amt = raw_amt / 1_000_000_000
                        mint = "So11111111111111111111111111111111111111112"
                        break
            
            # 3. INSERT INTO DB
            # We use json.dumps(tx) to ensure double-quotes for JSON compatibility
            conn.execute(
                "INSERT OR IGNORE INTO transactions VALUES (?, ?, ?, ?, ?, ?)",
                (sig, ts, tx_type, mint, amt, json.dumps(tx)) 
            )
            new_tx_count += 1
            
        conn.close()
        return f"✅ Success! Found {new_tx_count} new transactions."
        
    except Exception as e:
        return f"❌ Error: {e}"

if __name__ == "__main__":
    init_db()
    print(fetch_and_update())