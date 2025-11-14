#!/usr/bin/env python3
"""
Script pour initialiser les prix d'essence
À exécuter une fois au démarrage
"""

import json
from pathlib import Path
from scraper_essence import scrape_essence_quebec

if __name__ == "__main__":
    prices_file = Path(__file__).parent / "prices_essence.json"
    
    print("Initializing gas prices from EssenceQuébec...")
    prices = scrape_essence_quebec()
    
    if prices:
        with prices_file.open('w', encoding='utf-8') as f:
            json.dump(prices, f, ensure_ascii=False, indent=2)
        print(f"✓ Prices initialized: {len(prices)} regions found")
        print("\nSample prices:")
        for region, price in list(prices.items())[:5]:
            print(f"  - {region}: {price}")
    else:
        print("✗ Failed to initialize prices")
        print("Will use default prices from settings")
