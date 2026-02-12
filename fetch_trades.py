import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("HELIUS_API_KEY")
WALLET = os.getenv("MY_WALLET")

url = f"https://api.helius.xyz/v0/addresses/{WALLET}/transactions?api-key={API_KEY}"

response = requests.get(url)

if response.status_code == 200:
    txs = response.json()
    
    for tx in txs[:5]:  # Look at the top 5
        print(f"\nType: {tx.get('type')} | Signature: {tx.get('signature')[:10]}...")
        
        # Helius provides a 'tokenTransfers' list which is gold for trackers
        transfers = tx.get('tokenTransfers', [])
        for transfer in transfers:
            user = transfer.get('toUser')
            amount = transfer.get('tokenAmount')
            mint = transfer.get('mint')
            
            if user == WALLET:
                print(f"  📥 RECEIVED: {amount} of token {mint[:5]}...")
            else:
                print(f"  📤 SENT: {amount} of token {mint[:5]}...")
else:
    print("Error fetching data.")