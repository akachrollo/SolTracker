import duckdb
import json

DB_FILE = "solana_tracker.db"

def init_db():
    """Creates the table if it doesn't exist."""
    conn = duckdb.connect(DB_FILE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            signature TEXT PRIMARY KEY,
            timestamp INTEGER,
            type TEXT,
            fee INTEGER,
            raw_data JSON
        )
    """)
    conn.close()

def save_transactions(tx_list):
    """Saves a list of transactions, skipping duplicates."""
    conn = duckdb.connect(DB_FILE)
    
    # We use 'INSERT OR IGNORE' so if we already have the transaction, it won't error
    for tx in tx_list:
        conn.execute("""
            INSERT OR IGNORE INTO transactions 
            VALUES (?, ?, ?, ?, ?)
        """, (
            tx.get('signature'),
            tx.get('timestamp'),
            tx.get('type'),
            tx.get('fee', 0),
            json.dumps(tx) # Save the full raw data so we never lose details
        ))
    
    # Show a quick count of how many we have now
    total = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    conn.close()
    print(f"💾 Database updated. Total stored transactions: {total}")