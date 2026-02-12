import os
import requests
from dotenv import load_dotenv
from database_manager import init_db, save_transactions # Import your new librarian

load_dotenv()
API_KEY = os.getenv("HELIUS_API_KEY")
WALLET = os.getenv("MY_WALLET")

# Initialize the DB
init_db()

url = f"https://api.helius.xyz/v0/addresses/{WALLET}/transactions?api-key={API_KEY}"

print("📡 Fetching latest trades from Helius...")
response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    # Save the 85 (or more) transactions to DuckDB
    save_transactions(data)
else:
    print(f"❌ Error: {response.status_code}")