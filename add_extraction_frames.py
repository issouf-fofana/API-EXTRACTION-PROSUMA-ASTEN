#!/usr/bin/env python3
"""
Script pour ajouter des cadres d'extraction avec pointillés à toutes les APIs
"""

import os
import re

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Configuration des APIs avec leurs titres
APIS_CONFIG = {
    "API_COMMANDE_REASSORT": {
        "file": "api_commande_reassort.py",
        "title": "📦 EXTRACTION COMMANDES RÉASSORT",
        "count_filter": "'is_external': 'true'",
        "method": "get_orders"
    },
    "API_COMMANDE_DIRECTE": {
        "file": "api_commande_directe.py", 
        "title": "📦 EXTRACTION COMMANDES DIRECTES",
        "count_filter": "'is_direct': 'true'",
        "method": "get_orders"
    },
    "API_COMMANDE": {
        "file": "api_commande.py",
        "title": "📦 EXTRACTION COMMANDES FOURNISSEURS",
        "count_filter": "",
        "method": "get_orders"
    },
    "API_PRODUIT_NON_TROUVE": {
        "file": "api_produit_non_trouve.py",
        "title": "📦 EXTRACTION PRODUITS NON TROUVÉS",
        "count_filter": "",
        "method": "get_event_lines"
    },
}

FRAME_FUNCTION = '''
    def display_extraction_frame(self, shop_code, shop_name, total_items, total_pages, period):
        """Affiche un cadre avec les détails de l'extraction"""
        logger.info("┌" + "─" * 78 + "┐")
        logger.info("│" + " " * 78 + "│")
        logger.info(f"│{'{TITLE}':^78}│")
        logger.info("│" + " " * 78 + "│")
        line1 = f"🏪 Magasin: {shop_name} ({shop_code})"
        logger.info("│  " + line1 + " " * (76 - len(line1)) + "│")
        line2 = f"📅 Période: {period}"
        logger.info("│  " + line2 + " " * (76 - len(line2)) + "│")
        line3 = f"📊 Total éléments: {total_items:,}"
        logger.info("│  " + line3 + " " * (76 - len(line3)) + "│")
        line4 = f"📄 Pages à traiter: {total_pages}"
        logger.info("│  " + line4 + " " * (76 - len(line4)) + "│")
        logger.info("│" + " " * 78 + "│")
        logger.info("└" + "─" * 78 + "┘")
'''

def add_frame_to_api(api_folder, config):
    """Ajoute le cadre d'extraction à une API"""
    api_path = os.path.join(PROJECT_ROOT, api_folder, config['file'])
    
    if not os.path.exists(api_path):
        print(f"❌ Fichier non trouvé: {api_path}")
        return False
    
    with open(api_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Vérifier si la fonction existe déjà
    if 'def display_extraction_frame' in content:
        print(f"✅ {api_folder}: Cadre déjà présent")
        return True
    
    # Ajouter la fonction display_extraction_frame juste avant la méthode get_orders/get_event_lines
    frame_func = FRAME_FUNCTION.replace('{TITLE}', config['title'])
    
    # Trouver la méthode et ajouter avant
    pattern = f"    def {config['method']}\\("
    if re.search(pattern, content):
        content = re.sub(pattern, frame_func + '\n' + f"    def {config['method']}(", content, count=1)
        
        with open(api_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ {api_folder}: Cadre ajouté avec succès")
        return True
    else:
        print(f"❌ {api_folder}: Méthode {config['method']} non trouvée")
        return False

def main():
    print("🔧 Ajout des cadres d'extraction à toutes les APIs...")
    print("=" * 60)
    
    success_count = 0
    for api_folder, config in APIS_CONFIG.items():
        if add_frame_to_api(api_folder, config):
            success_count += 1
    
    print("=" * 60)
    print(f"✅ {success_count}/{len(APIS_CONFIG)} APIs mises à jour")

if __name__ == "__main__":
    main()

