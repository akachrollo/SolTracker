import duckdb
import pandas as pd

def get_stats():
    # Connect to your local database file
    con = duckdb.connect('solana_tracker.db')
    
    # 1. Get the total count
    total = con.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    
    # 2. Get the breakdown of transaction types (Swaps vs Transfers)
    # We use .df() to turn the result into a pretty Pandas table
    type_counts = con.execute("""
        SELECT type, COUNT(*) as count 
        FROM transactions 
        GROUP BY type 
        ORDER BY count DESC
    """).df()
    
    print(f"--- 📊 WALLET STATS (Total: {total}) ---")
    print(type_counts)
    
    # 3. Look at your last 3 actual Swaps
    print("\n--- 🔄 RECENT SWAPS ---")
    swaps = con.execute("""
        SELECT signature, type 
        FROM transactions 
        WHERE type = 'SWAP' 
        LIMIT 3
    """).df()
    print(swaps)
    
    con.close()

if __name__ == "__main__":
    get_stats()