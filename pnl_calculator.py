import duckdb
import json
import os
from dotenv import load_dotenv

load_dotenv()
MY_WALLET = os.getenv("MY_WALLET")
WSOL_MINT = "So11111111111111111111111111111111111111112"

def analyze_swaps():
    con = duckdb.connect('solana_tracker.db')
    swaps = con.execute("SELECT signature, raw_data FROM transactions WHERE type = 'SWAP'").fetchall()
    
    print(f"--- 💸 PnL ANALYSIS ({len(swaps)} Swaps) ---")
    
    for sig, raw_json in swaps:
        tx = json.loads(raw_json)
        
        # Dictionaries to sum up totals (e.g., {'SOL': 0.5, 'BONK': 1000})
        sent_totals = {}
        rcvd_totals = {}

        # 1. Process Native SOL
        for move in tx.get('nativeTransfers', []):
            amt = move.get('amount') / 10**9
            if move.get('fromUserAccount') == MY_WALLET:
                sent_totals['SOL'] = sent_totals.get('SOL', 0) + amt
            elif move.get('toUserAccount') == MY_WALLET:
                rcvd_totals['SOL'] = rcvd_totals.get('SOL', 0) + amt

        # 2. Process Token Transfers
        for move in tx.get('tokenTransfers', []):
            amt = move.get('tokenAmount')
            mint = move.get('mint')
            
            # Label wSOL nicely, otherwise use first 4 chars of address
            symbol = "wSOL" if mint == WSOL_MINT else mint[:4]

            if move.get('fromUser') == MY_WALLET:
                sent_totals[symbol] = sent_totals.get(symbol, 0) + amt
            else:
                rcvd_totals[symbol] = rcvd_totals.get(symbol, 0) + amt

        # 3. Print Clean Results
        # We only print if the amount is significant (> 0.002) OR if it's a non-SOL token
        # This hides the tiny 0.000005 SOL rent adjustments
        
        sent_str = []
        for sym, qty in sent_totals.items():
            if qty > 0.002 or sym not in ['SOL', 'wSOL']:
                sent_str.append(f"{qty:,.4f} {sym}")
        
        rcvd_str = []
        for sym, qty in rcvd_totals.items():
            if qty > 0.002 or sym not in ['SOL', 'wSOL']:
                rcvd_str.append(f"{qty:,.4f} {sym}")

        if sent_str or rcvd_str:
            print(f"TX: {sig[:8]}... | 📤 OUT: {' + '.join(sent_str)}  ➡️  📥 IN: {' + '.join(rcvd_str)}")

    con.close()

if __name__ == "__main__":
    analyze_swaps()