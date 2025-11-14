#!/usr/bin/env python3
"""
API Flask pour récupérer les prix d'essence
À intégrer dans timer_app.py
"""

import json
from pathlib import Path
from flask import Blueprint, jsonify

# Blueprint pour les routes essence
essence_bp = Blueprint('essence', __name__, url_prefix='/api')

PRICES_FILE = Path(__file__).parent / "prices_essence.json"

def load_prices():
    """Charge les prix depuis le fichier JSON"""
    if PRICES_FILE.exists():
        try:
            with PRICES_FILE.open('r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def get_region_from_coords(lat, lon):
    """
    Détecte la région québécoise à partir des coordonnées GPS
    Basé sur les limites approximatives des régions
    """
    
    # Régions du Québec (approximations)
    regions = {
        "Montréal": {"lat_range": (45.4, 45.7), "lon_range": (-73.6, -73.5)},
        "Laval": {"lat_range": (45.5, 45.6), "lon_range": (-73.7, -73.5)},
        "Gatineau": {"lat_range": (45.4, 45.5), "lon_range": (-75.8, -75.6)},
        "Trois-Rivières": {"lat_range": (46.3, 46.4), "lon_range": (-72.6, -72.5)},
        "Québec": {"lat_range": (46.8, 46.9), "lon_range": (-71.3, -71.1)},
        "Sherbrooke": {"lat_range": (45.4, 45.5), "lon_range": (-71.9, -71.7)},
        "Estrie": {"lat_range": (45.5, 45.6), "lon_range": (-72.1, -71.8)},
    }
    
    for region, bounds in regions.items():
        lat_min, lat_max = bounds["lat_range"]
        lon_min, lon_max = bounds["lon_range"]
        
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            return region
    
    # Région par défaut (Montréal)
    return "Montréal"


@essence_bp.route('/gas-prices')
def get_gas_prices():
    """
    Retourne tous les prix d'essence disponibles
    """
    prices = load_prices()
    return jsonify(prices)


@essence_bp.route('/gas-price/<region>')
def get_gas_price_for_region(region):
    """
    Retourne le prix d'essence pour une région spécifique
    """
    prices = load_prices()
    
    region_lower = region.lower().strip()
    
    for r, price in prices.items():
        if region_lower in r.lower() or r.lower() in region_lower:
            return jsonify({
                "region": r,
                "price": price,
                "currency": "CAD"
            })
    
    # Si pas trouvé, retourner une erreur
    return jsonify({
        "error": f"Prix non trouvé pour la région: {region}",
        "available_regions": list(prices.keys())
    }), 404


@essence_bp.route('/gas-price-by-coords/<float:lat>/<float:lon>')
def get_gas_price_by_coords(lat, lon):
    """
    Retourne le prix d'essence basé sur les coordonnées GPS
    """
    region = get_region_from_coords(lat, lon)
    prices = load_prices()
    
    for r, price in prices.items():
        if region.lower() in r.lower() or r.lower() in region.lower():
            return jsonify({
                "detected_region": region,
                "region": r,
                "price": price,
                "currency": "CAD",
                "coordinates": {"lat": lat, "lon": lon}
            })
    
    # Si pas trouvé, retourner la région détectée sans prix
    return jsonify({
        "detected_region": region,
        "price": None,
        "error": f"Prix non trouvé pour {region}"
    }), 404
