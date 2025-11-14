#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour vérifier les champs is_direct et is_external dans l'API
"""

import sys
import os
import io
import json
import requests
from dotenv import load_dotenv
import urllib3

# Configurer stdout/stderr pour UTF-8 sur Windows
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Désactiver les warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Ajouter le répertoire parent au path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils import load_shop_config

def test_api_fields():
    """Teste les champs de l'API supplier_order"""
    
    # Charger la configuration
    project_root = os.path.dirname(os.path.abspath(__file__))
    load_dotenv(os.path.join(project_root, 'config.env'))
    
    username = os.getenv('PROSUMA_USER')
    password = os.getenv('PROSUMA_PASSWORD')
    
    if not username or not password:
        print("❌ PROSUMA_USER et PROSUMA_PASSWORD doivent être configurés dans config.env")
        return
    
    # Charger la configuration des magasins
    shop_config = load_shop_config(project_root)
    
    # Prendre le premier magasin disponible pour le test
    if not shop_config:
        print("❌ Aucun magasin configuré")
        return
    
    shop_code = list(shop_config.keys())[0]
    shop_info = shop_config[shop_code]
    base_url = shop_info['url']
    shop_name = shop_info['name']
    
    print("=" * 80)
    print("TEST DES CHAMPS DE L'API SUPPLIER_ORDER")
    print("=" * 80)
    print(f"Magasin de test: {shop_name} ({shop_code})")
    print(f"URL: {base_url}")
    print("=" * 80)
    print()
    
    # Créer une session
    session = requests.Session()
    session.auth = (username, password)
    session.verify = False
    
    # Test 1: Récupérer les informations du magasin
    print("📋 TEST 1: Récupération des informations du magasin...")
    try:
        shop_url = f"{base_url}/api/shop/{shop_code}/"
        response = session.get(shop_url, timeout=30)
        if response.status_code == 200:
            shop_data = response.json()
            shop_id = shop_data.get('id')
            print(f"✅ Magasin trouvé: ID = {shop_id}")
        else:
            # Essayer avec la liste paginée
            shop_list_url = f"{base_url}/api/shop/"
            response = session.get(shop_list_url, params={'page': 1, 'page_size': 100}, timeout=30)
            if response.status_code == 200:
                data = response.json()
                shops = data.get('results', [])
                for shop in shops:
                    if shop.get('reference') == shop_code:
                        shop_id = shop.get('id')
                        print(f"✅ Magasin trouvé: ID = {shop_id}")
                        break
                else:
                    print(f"❌ Magasin {shop_code} non trouvé")
                    return
            else:
                print(f"❌ Erreur HTTP {response.status_code}")
                return
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return
    
    print()
    
    # Test 2: Récupérer quelques commandes SANS filtre
    print("📋 TEST 2: Récupération de commandes SANS filtre...")
    try:
        url = f"{base_url}/api/supplier_order/"
        params = {
            'shop': shop_id,
            'page_size': 5,  # Prendre seulement 5 commandes pour le test
            'page': 1
        }
        response = session.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            orders = data.get('results', [])
            print(f"✅ {len(orders)} commandes récupérées")
            
            if orders:
                print("\n📊 CHAMPS DISPONIBLES DANS LA PREMIÈRE COMMANDE:")
                print("-" * 80)
                first_order = orders[0]
                print(f"ID: {first_order.get('id', 'N/A')}")
                print(f"Référence: {first_order.get('reference', 'N/A')}")
                
                # Vérifier les champs is_direct et is_external
                print("\n🔍 VÉRIFICATION DES CHAMPS:")
                print("-" * 80)
                
                has_is_direct = 'is_direct' in first_order
                has_is_external = 'is_external' in first_order
                
                print(f"is_direct présent: {'✅ OUI' if has_is_direct else '❌ NON'}")
                if has_is_direct:
                    print(f"  → Valeur: {first_order.get('is_direct')} (type: {type(first_order.get('is_direct')).__name__})")
                
                print(f"is_external présent: {'✅ OUI' if has_is_external else '❌ NON'}")
                if has_is_external:
                    print(f"  → Valeur: {first_order.get('is_external')} (type: {type(first_order.get('is_external')).__name__})")
                
                # Afficher TOUS les champs disponibles
                print("\n📋 TOUS LES CHAMPS DISPONIBLES:")
                print("-" * 80)
                for key in sorted(first_order.keys()):
                    value = first_order[key]
                    value_type = type(value).__name__
                    if isinstance(value, (dict, list)):
                        print(f"  {key}: {value_type} (contenu complexe)")
                    else:
                        print(f"  {key}: {value} ({value_type})")
                
                # Analyser toutes les commandes
                print("\n📊 ANALYSE DE TOUTES LES COMMANDES RÉCUPÉRÉES:")
                print("-" * 80)
                direct_count = 0
                external_count = 0
                for i, order in enumerate(orders, 1):
                    is_direct = order.get('is_direct', None)
                    is_external = order.get('is_external', None)
                    
                    if is_direct is not None:
                        if is_direct:
                            direct_count += 1
                    if is_external is not None:
                        if is_external:
                            external_count += 1
                    
                    print(f"Commande {i} ({order.get('reference', 'N/A')}):")
                    print(f"  is_direct: {is_direct}")
                    print(f"  is_external: {is_external}")
                
                print(f"\n📈 RÉSUMÉ:")
                print(f"  Commandes directes (is_direct=True): {direct_count}/{len(orders)}")
                print(f"  Commandes externes (is_external=True): {external_count}/{len(orders)}")
                
            else:
                print("⚠️ Aucune commande trouvée")
        else:
            print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # Test 3: Tester avec les filtres API
    print("📋 TEST 3: Test avec filtres API...")
    print("-" * 80)
    
    # Test avec is_direct=false
    print("\n🔍 Test avec is_direct=false:")
    try:
        params = {
            'shop': shop_id,
            'page_size': 5,
            'page': 1,
            'is_direct': 'false'
        }
        response = session.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            orders_filtered = data.get('results', [])
            print(f"✅ {len(orders_filtered)} commandes avec is_direct=false")
            if orders_filtered:
                for order in orders_filtered:
                    print(f"  - {order.get('reference', 'N/A')}: is_direct={order.get('is_direct')}, is_external={order.get('is_external')}")
        else:
            print(f"❌ Erreur HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test avec is_external=true
    print("\n🔍 Test avec is_external=true:")
    try:
        params = {
            'shop': shop_id,
            'page_size': 5,
            'page': 1,
            'is_external': 'true'
        }
        response = session.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            orders_filtered = data.get('results', [])
            print(f"✅ {len(orders_filtered)} commandes avec is_external=true")
            if orders_filtered:
                for order in orders_filtered:
                    print(f"  - {order.get('reference', 'N/A')}: is_direct={order.get('is_direct')}, is_external={order.get('is_external')}")
        else:
            print(f"❌ Erreur HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test avec is_direct=true
    print("\n🔍 Test avec is_direct=true:")
    try:
        params = {
            'shop': shop_id,
            'page_size': 5,
            'page': 1,
            'is_direct': 'true'
        }
        response = session.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            orders_filtered = data.get('results', [])
            print(f"✅ {len(orders_filtered)} commandes avec is_direct=true")
            if orders_filtered:
                for order in orders_filtered:
                    print(f"  - {order.get('reference', 'N/A')}: is_direct={order.get('is_direct')}, is_external={order.get('is_external')}")
        else:
            print(f"❌ Erreur HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test combiné: is_external=true ET is_direct=false
    print("\n🔍 Test avec is_external=true ET is_direct=false (réassort):")
    try:
        params = {
            'shop': shop_id,
            'page_size': 5,
            'page': 1,
            'is_external': 'true',
            'is_direct': 'false'
        }
        response = session.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            orders_filtered = data.get('results', [])
            print(f"✅ {len(orders_filtered)} commandes réassort (is_external=true ET is_direct=false)")
            if orders_filtered:
                for order in orders_filtered:
                    print(f"  - {order.get('reference', 'N/A')}: is_direct={order.get('is_direct')}, is_external={order.get('is_external')}")
        else:
            print(f"❌ Erreur HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print()
    print("=" * 80)
    print("TEST TERMINÉ")
    print("=" * 80)

if __name__ == "__main__":
    test_api_fields()

