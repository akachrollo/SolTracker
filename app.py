import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
from fetch_trades import fetch_and_update, init_db
from price_fetcher import get_token_prices, get_eur_rate
import os

st.set_page_config(page_title="SolTracker", page_icon="💸", layout="wide")

# --- SIDEBAR ---
with st.sidebar:
    st.title("💸 SolTracker")
    if st.button("🔄 Refresh Transactions", type="primary"):
        with st.spinner("Syncing with Blockchain..."):
            msg = fetch_and_update()
            st.success(msg)
            st.rerun()
    st.markdown("---")
    st.caption("Values shown in **EURO (€)**")

# --- DATA LOADING ---
if not os.path.exists("solana_tracker.db"):
    init_db()

conn = duckdb.connect("solana_tracker.db", read_only=True)

try:
    # Load all transactions
    df = conn.execute("SELECT * FROM transactions ORDER BY timestamp DESC").fetchdf()
    
    # Calculate Holdings
    if not df.empty:
        holdings_query = """
            SELECT 
                token_mint, 
                SUM(token_amount) as total_balance
            FROM transactions 
            GROUP BY token_mint
            HAVING total_balance > 0.000001
        """
        df_holdings = conn.execute(holdings_query).fetchdf()
    else:
        df_holdings = pd.DataFrame(columns=['token_mint', 'total_balance'])

except Exception as e:
    st.error(f"Database Error: {e}")
    df = pd.DataFrame()
    df_holdings = pd.DataFrame()

conn.close()

# --- GET PRICES & CONVERT TO EURO ---
eur_rate = get_eur_rate()

# SAFETY CHECK: Ensure columns exist even if data is empty
if df_holdings.empty:
    df_holdings['price_eur'] = 0.0
    df_holdings['eur_value'] = 0.0
else:
    unique_mints = df_holdings['token_mint'].unique().tolist()
    prices_usd = get_token_prices(unique_mints)
    
    # Calculate Prices in EUR
    df_holdings['price_eur'] = df_holdings['token_mint'].map(prices_usd).fillna(0) * eur_rate
    df_holdings['eur_value'] = df_holdings['total_balance'] * df_holdings['price_eur']

# --- DASHBOARD ---

# Top Metric
total_value = df_holdings['eur_value'].sum() if not df_holdings.empty else 0
st.metric("💰 Net Worth", f"€{total_value:,.2f}")

tab1, tab2, tab3 = st.tabs(["📊 Overview", "🎒 Portfolio", "📜 History"])

with tab1:
    st.subheader("Transaction Volume")
    
    if not df.empty:
        df['date'] = df['timestamp'].dt.date
        daily_counts = df.groupby('date').size().reset_index(name='transactions')
        
        # Interactive Bar Chart
        fig = px.bar(daily_counts, x='date', y='transactions', color_discrete_sequence=['#14F195'])
        fig.update_layout(clickmode='event+select')
        
        selection = st.plotly_chart(fig, on_select="rerun", key="daily_chart")
        
        # --- SMART FILTER LOGIC ---
        if selection and selection['selection']['points']:
            # USER CLICKED A BAR -> SHOW TIME (HH:mm:ss)
            point = selection['selection']['points'][0]
            selected_date = point['x']
            st.info(f"📅 Details for: **{selected_date}**")
            
            # Filter specifically for the selected date
            filtered_df = df[df['date'].astype(str) == selected_date]
            
            # Format: Show detailed Time
            time_format = "HH:mm:ss"
            
            # Show the filtered table
            st.dataframe(
                filtered_df[['timestamp', 'type', 'token_mint', 'token_amount', 'signature']],
                column_config={
                    "timestamp": st.column_config.DatetimeColumn("Time", format=time_format),
                    "token_amount": st.column_config.NumberColumn("Amount", format="%.4f"),
                    "signature": st.column_config.TextColumn("Signature", width="small"),
                    "token_mint": "Token Addr",
                },
                use_container_width=True,
                hide_index=True
            )
            
        else:
            # DEFAULT VIEW -> Show Nothing or Summary
            st.caption("Tip: Click a bar in the chart above to see the transactions for that day.")

    else:
        st.info("No transactions found yet.")

with tab2:
    st.subheader("Your Bags (€)")
    # Now this is safe because we forced the columns to exist above
    display_df = df_holdings[['token_mint', 'total_balance', 'price_eur', 'eur_value']].copy()
    display_df = display_df.sort_values(by='eur_value', ascending=False)
    
    st.dataframe(
        display_df,
        column_config={
            "token_mint": "Token",
            "total_balance": st.column_config.NumberColumn("Balance", format="%.4f"),
            "price_eur": st.column_config.NumberColumn("Price (€)", format="€%.4f"),
            "eur_value": st.column_config.NumberColumn("Value (€)", format="€%.2f"),
        },
        use_container_width=True,
        hide_index=True
    )

with tab3:
    st.subheader("Full History Log")
    
    if not df.empty and not df_holdings.empty:
        # Create a price map {mint: price_eur}
        # Use .get to safely handle missing prices
        price_map = dict(zip(df_holdings.token_mint, df_holdings.price_eur))
        
        df['current_price_eur'] = df['token_mint'].map(price_map).fillna(0)
        df['est_value_eur'] = df['token_amount'] * df['current_price_eur']
    else:
        df['est_value_eur'] = 0

    st.dataframe(
        df[['timestamp', 'type', 'token_mint', 'token_amount', 'est_value_eur', 'signature']],
        column_config={
            "timestamp": st.column_config.DatetimeColumn("Date", format="D MMM HH:mm"),
            "token_amount": st.column_config.NumberColumn("Amount", format="%.4f"),
            "est_value_eur": st.column_config.NumberColumn("Est. Value Now (€)", format="€%.2f"),
            "signature": st.column_config.TextColumn("Signature", width="small"),
        },
        use_container_width=True,
        hide_index=True
    )