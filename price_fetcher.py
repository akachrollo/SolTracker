import requests

def get_eur_rate():
    """Fetches the current USD to EUR exchange rate."""
    try:
        # Free API, no key needed
        url = "https://api.frankfurter.app/latest?from=USD&to=EUR"
        data = requests.get(url, timeout=5).json()
        return data['rates']['EUR']
    except:
        return 0.93 # Fallback if API fails (approximate)

def get_token_prices(mint_addresses):
    """Fetches token prices in USD from DexScreener"""
    if not mint_addresses:
        return {}

    valid_mints = list(set([str(m) for m in mint_addresses if len(str(m)) > 30]))
    chunk_size = 30
    prices = {}

    for i in range(0, len(valid_mints), chunk_size):
        chunk = valid_mints[i:i + chunk_size]
        ids = ",".join(chunk)
        url = f"https://api.dexscreener.com/latest/dex/tokens/{ids}"

        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'pairs' in data and data['pairs']:
                    for pair in data['pairs']:
                        mint = pair.get('baseToken', {}).get('address')
                        price_usd = pair.get('priceUsd')
                        if mint and price_usd and mint not in prices:
                            prices[mint] = float(price_usd)
        except Exception as e:
            print(f"❌ Error: {e}")

    return prices