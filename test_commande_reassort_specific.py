#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour extraire les commandes réassort pour des magasins spécifiques
Magasins: 110, 230, 292, 294
"""

import sys
import os
import io

# Configurer stdout/stderr pour UTF-8 sur Windows
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Ajouter le répertoire parent au path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from API_COMMANDE_REASSORT.api_commande_reassort import ProsumaAPICommandeReassortExtractor

# Magasins à tester
test_shops = ['110', '230', '292', '294']

def main():
    """Extrait les commandes réassort pour les magasins spécifiés"""
    try:
        extractor = ProsumaAPICommandeReassortExtractor()
        
        # Filtrer les magasins pour ne garder que ceux à tester
        original_shop_config = extractor.shop_config.copy()
        extractor.shop_config = {code: info for code, info in original_shop_config.items() if code in test_shops}
        extractor.shop_codes = list(extractor.shop_config.keys())
        
        if not extractor.shop_config:
            print(f"❌ Aucun des magasins {test_shops} n'est configuré dans magasins.json")
            print(f"   Magasins disponibles: {list(original_shop_config.keys())}")
            return
        
        print("=" * 60)
        print("TEST EXTRACTION - COMMANDES RÉASSORT")
        print("=" * 60)
        print(f"✅ Magasins à tester: {list(extractor.shop_config.keys())}")
        print(f"📅 Période: {extractor.start_date.strftime('%Y-%m-%d')} à {extractor.end_date.strftime('%Y-%m-%d')}")
        if extractor.status_filter:
            print(f"🔍 Filtre: {extractor.status_filter}")
        print("=" * 60)
        print()
        
        # Extraire pour chaque magasin
        for shop_code in test_shops:
            if shop_code in extractor.shop_config:
                print(f"\n{'='*60}")
                print(f"TEST MAGASIN {shop_code}")
                print(f"{'='*60}")
                extractor.extract_shop(shop_code)
            else:
                print(f"⚠️ Magasin {shop_code} non trouvé dans la configuration")
        
        print("\n" + "=" * 60)
        print("✅ TEST TERMINÉ")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

