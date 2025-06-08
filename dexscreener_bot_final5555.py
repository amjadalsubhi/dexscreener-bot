
import time
import json
import os
import requests

# ------------------ Config ------------------
DEX_API_URL = "https://api.dexscreener.io/latest/dex/pairs/solana"
FETCH_INTERVAL_SECONDS = 15
OUTPUT_FILE = "dex_log.json"

# ------------------ Fetcher ------------------
def fetch_recent_pairs():
    try:
        res = requests.get(DEX_API_URL, timeout=5)
        res.raise_for_status()
        return res.json().get("pairs", [])
    except Exception as e:
        print(f"[Fetcher] Error: {e}")
        return []

# ------------------ Processor ------------------
def process_pairs(raw_data):
    processed = []
    for pair in raw_data:
        try:
            processed.append({
                "name": pair.get("baseToken", {}).get("name"),
                "symbol": pair.get("baseToken", {}).get("symbol"),
                "pair_address": pair.get("pairAddress"),
                "price_usd": pair.get("priceUsd"),
                "liquidity_usd": pair.get("liquidity", {}).get("usd"),
                "txns_5m": pair.get("txns", {}).get("m5", {}).get("buys", 0) + pair.get("txns", {}).get("m5", {}).get("sells", 0),
                "created_at": pair.get("pairCreatedAt")
            })
        except Exception as e:
            print(f"[Processor] Error: {e}")
    return processed

# ------------------ Storage ------------------
def save_to_json(data):
    if not data:
        return
    try:
        if not os.path.exists(OUTPUT_FILE):
            with open(OUTPUT_FILE, "w") as f:
                json.dump(data, f, indent=2)
        else:
            with open(OUTPUT_FILE, "r+") as f:
                existing = json.load(f)
                existing.extend(data)
                f.seek(0)
                json.dump(existing, f, indent=2)
    except Exception as e:
        print(f"[Storage] Error: {e}")

# ------------------ Main Loop ------------------
def run_bot():
    seen = set()
    print("🚀 DexScanner bot started...")
    while True:
        raw_data = fetch_recent_pairs()
        if not raw_data:
            time.sleep(FETCH_INTERVAL_SECONDS)
            continue

        new_pairs = [p for p in raw_data if p.get("pairAddress") not in seen]
        processed = process_pairs(new_pairs)

        for p in processed:
            seen.add(p["pair_address"])
            print(f"🪙 {p['symbol']} | Price: {p['price_usd']} | Liq: {p['liquidity_usd']} | TXNs/5m: {p['txns_5m']}")

        save_to_json(processed)
        time.sleep(FETCH_INTERVAL_SECONDS)

if __name__ == "__main__":
    run_bot()
