import streamlit as st
import duckdb
import pandas as pd
import json
import os
from dotenv import load_dotenv

# Page Config
st.set_page_config(page_title="SolTracker Pro", page_icon="📈", layout="wide")
load_dotenv()
MY_WALLET = os.getenv("MY_WALLET")

st.title("📈 Solana Trade Dashboard")
st.markdown(f"**Tracking Wallet:** `{MY_WALLET}`")

# --- DATABASE CONNECTION ---
def get_data():
    con = duckdb.connect('solana_tracker.db')
    df = con.execute("SELECT * FROM transactions ORDER BY timestamp DESC").df()
    con.close()
    return df

data = get_data()

# --- TOP METRICS ---
total_tx = len(data)
swaps_count = len(data[data['type'] == 'SWAP'])
transfers_count = len(data[data['type'] == 'TRANSFER'])

m1, m2, m3 = st.columns(3)
m1.metric("Total Transactions", total_tx)
m2.metric("Total Swaps", swaps_count)
m3.metric("Transfers", transfers_count)

st.divider()

# --- RECENT TRADES SECTION ---
st.subheader("🔄 Recent Swap Analysis")

# We'll process the last 20 swaps for the UI
swaps_only = data[data['type'] == 'SWAP'].head(20)

for _, row in swaps_only.iterrows():
    tx = json.loads(row['raw_data'])
    sig = row['signature']
    
    # Simple logic to identify the trade
    token_moves = tx.get('tokenTransfers', [])
    native_moves = tx.get('nativeTransfers', [])
    
    with st.expander(f"Swap: {sig[:10]}... | {row['timestamp']}"):
        col_out, col_in = st.columns(2)
        
        with col_out:
            st.write("**📤 SENT (Out)**")
            for m in native_moves:
                if m.get('fromUserAccount') == MY_WALLET:
                    st.error(f"{m.get('amount')/10**9:.4f} SOL")
            for m in token_moves:
                if m.get('fromUser') == MY_WALLET:
                    st.error(f"{m.get('tokenAmount'):,.2f} {m.get('mint')[:4]}")
        
        with col_in:
            st.write("**📥 RECEIVED (In)**")
            for m in native_moves:
                if m.get('toUserAccount') == MY_WALLET:
                    st.success(f"{m.get('amount')/10**9:.4f} SOL")
            for m in token_moves:
                if m.get('fromUser') != MY_WALLET:
                    st.success(f"{m.get('tokenAmount'):,.2f} {m.get('mint')[:4]}")
        
        st.link_button("View on Solscan", f"https://solscan.io/tx/{sig}")

# --- FULL DATA TABLE ---
st.divider()
st.subheader("📜 Raw Transaction Log")
st.dataframe(data[['signature', 'type', 'timestamp']], use_container_width=True)