#!/usr/bin/env python3
"""
Web scraper pour EssenceQuébec - récupère les prix d'essence par région
"""

import json
import time
import requests
from pathlib import Path
from bs4 import BeautifulSoup

def scrape_essence_quebec_simple():
    """
    Scrape les prix d'essence via requests (sans Selenium)
    Retourne un dictionnaire avec régions et prix
    """
    url = "https://www.essencequebec.com/meilleur-prix"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Chercher les tables avec données
        prices_by_region = {}
        
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            
            if len(rows) < 2:
                continue
            
            # Parser les en-têtes
            headers_row = rows[0]
            headers = [th.get_text(strip=True).lower() for th in headers_row.find_all(['th', 'td'])]
            
            # Chercher indices des colonnes
            region_idx = None
            regie_idx = None
            
            for i, h in enumerate(headers):
                if 'région' in h or 'region' in h:
                    region_idx = i
                if 'régie' in h or 'regie' in h or 'prix' in h:
                    regie_idx = i
            
            # Extraire les données
            if region_idx is not None and regie_idx is not None:
                for row in rows[1:]:
                    cells = row.find_all('td')
                    if len(cells) > max(region_idx, regie_idx):
                        region = cells[region_idx].get_text(strip=True)
                        price = cells[regie_idx].get_text(strip=True)
                        
                        if region and price:
                            prices_by_region[region] = price
        
        if prices_by_region:
            return prices_by_region
        
        # Si pas trouvé, retourner les prix par défaut
        return None
        
    except Exception as e:
        print(f"Erreur lors du scraping simple: {e}")
        return None


def scrape_essence_quebec():
    """
    Version wrapper qui essaie le scraping simple d'abord
    """
    prices = scrape_essence_quebec_simple()
    
    if prices:
        return prices
    
    # Fallback: charger les prix par défaut depuis le fichier
    try:
        prices_file = Path(__file__).parent / "prices_essence.json"
        if prices_file.exists():
            with prices_file.open('r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    
    return None


def get_price_for_region(region_name, prices_dict=None):
    """
    Récupère le prix d'essence pour une région spécifique
    """
    if prices_dict is None:
        prices_dict = scrape_essence_quebec()
    
    if not prices_dict:
        return None
    
    region_lower = region_name.lower().strip()
    
    for region, price in prices_dict.items():
        if region_lower in region.lower() or region.lower() in region_lower:
            return price
    
    return None


def save_prices_to_file(filename="prices_essence.json"):
    """
    Scrape et sauvegarde les prix dans un fichier JSON
    """
    print("Scraping EssenceQuébec...")
    prices = scrape_essence_quebec()
    
    if prices:
        filepath = Path(__file__).parent / filename
        with filepath.open('w', encoding='utf-8') as f:
            json.dump(prices, f, ensure_ascii=False, indent=2)
        print(f"✓ Prices saved to {filename}")
        print(f"Régions trouvées: {len(prices)}")
        for region, price in list(prices.items())[:5]:
            print(f"  - {region}: {price}")
        return prices
    else:
        print("✗ Erreur lors du scraping (utilisant les prix par défaut)")
        return None


if __name__ == "__main__":
    prices = save_prices_to_file()
    
    if prices:
        print("\n--- Test de recherche par région ---")
        test_regions = ["Montréal", "Gatineau", "Laval", "Trois-Rivières", "Québec"]
        for region in test_regions:
            price = get_price_for_region(region, prices)
            print(f"{region}: {price}")

