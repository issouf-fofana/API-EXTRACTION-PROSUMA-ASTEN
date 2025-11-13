#!/usr/bin/env python3
"""
Exploration de l'API Prosuma pour découvrir tous les endpoints disponibles
"""

import requests
import os
import json
from dotenv import load_dotenv
import urllib3

# Désactiver les warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def explore_api_endpoints():
    """Explore l'API pour découvrir les endpoints disponibles"""
    load_dotenv('config.env')
    
    username = os.getenv('PROSUMA_USER')
    password = os.getenv('PROSUMA_PASSWORD')
    base_url = "https://pos3-prod-prosuma.prosuma.pos"
    api_url = f"{base_url}/api"
    
    if not username or not password:
        print("❌ PROSUMA_USER ou PROSUMA_PASSWORD non configuré dans config.env")
        return
    
    print(f"🔍 Exploration de l'API Prosuma - Endpoints disponibles")
    print(f"👤 Utilisateur: {username}")
    print(f"🌐 URL: {base_url}")
    print("=" * 60)
    
    session = requests.Session()
    session.auth = (username, password)
    session.verify = False
    
    try:
        # Essayer de récupérer la documentation de l'API ou la liste des endpoints
        print("🔍 Recherche de la documentation API...")
        
        # Endpoints communs pour la documentation
        doc_endpoints = [
            "",
            "docs/",
            "swagger/",
            "redoc/",
            "schema/",
            "openapi.json",
            "swagger.json",
            "api-docs/",
            "endpoints/",
            "list/",
            "help/"
        ]
        
        for doc_endpoint in doc_endpoints:
            try:
                response = session.get(f"{api_url}/{doc_endpoint}", timeout=5)
                if response.status_code == 200:
                    print(f"✅ Documentation trouvée: /{doc_endpoint}")
                    if 'swagger' in response.text.lower() or 'openapi' in response.text.lower():
                        print("   📋 Format Swagger/OpenAPI détecté")
                    break
            except:
                continue
        
        # Tester des endpoints connus et chercher des patterns
        print(f"\n🔍 Test d'endpoints connus...")
        
        known_endpoints = [
            "user/",
            "shop/",
            "supplier_order/",
            "product/",
            "promotion/",
            "event_line/",
            "external_order/",
            "delivery/",
            "delivery_return/",
            "supplier_pre_order/",
            "inventory/",
            "category/",
            "brand/",
            "supplier/",
            "customer/",
            "sale/",
            "transaction/",
            "ticket/",
            "cashier/",
            "shift/",
            "report/",
            "export/",
            "import/",
            "backup/",
            "log/",
            "audit/",
            "notification/",
            "alert/",
            "setting/",
            "config/"
        ]
        
        working_endpoints = []
        for endpoint in known_endpoints:
            try:
                response = session.get(f"{api_url}/{endpoint}", params={'page_size': 1}, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, dict) and ('results' in data or 'count' in data):
                        count = data.get('count', 0)
                        working_endpoints.append((endpoint, count))
                        print(f"✅ /{endpoint} - {count} éléments")
                    elif isinstance(data, list):
                        working_endpoints.append((endpoint, len(data)))
                        print(f"✅ /{endpoint} - {len(data)} éléments")
            except:
                pass
        
        print(f"\n📊 Résumé des endpoints fonctionnels:")
        for endpoint, count in working_endpoints:
            print(f"   - /{endpoint}: {count} éléments")
        
        # Chercher des endpoints liés aux stocks dans les données existantes
        print(f"\n🔍 Recherche d'informations sur les stocks dans les endpoints existants...")
        
        # Tester l'endpoint product pour voir s'il contient des infos de stock
        try:
            response = session.get(f"{api_url}/product/", params={'page_size': 1}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'results' in data and data['results']:
                    product = data['results'][0]
                    print(f"📦 Informations de stock dans /product/:")
                    stock_fields = [k for k in product.keys() if 'stock' in k.lower() or 'quantity' in k.lower() or 'inventory' in k.lower()]
                    if stock_fields:
                        for field in stock_fields:
                            print(f"   - {field}: {product.get(field, 'N/A')}")
                    else:
                        print("   ❌ Aucun champ de stock trouvé dans /product/")
        except Exception as e:
            print(f"❌ Erreur lors de l'exploration de /product/: {e}")
        
        # Tester l'endpoint inventory pour voir s'il contient des mouvements
        try:
            response = session.get(f"{api_url}/inventory/", params={'page_size': 1}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'results' in data and data['results']:
                    inventory = data['results'][0]
                    print(f"📋 Informations dans /inventory/:")
                    print(f"   - Clés disponibles: {list(inventory.keys())}")
        except Exception as e:
            print(f"❌ Erreur lors de l'exploration de /inventory/: {e}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de connexion: {e}")
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")

if __name__ == "__main__":
    explore_api_endpoints()








