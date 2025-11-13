#!/usr/bin/env python3
"""
Extracteur API Prosuma RPOS - Articles avec prix promo (Version simplifiée)
"""

import requests
import os
import csv
import json
import logging
from datetime import datetime
import urllib3
from dotenv import load_dotenv
import sys

# Ajouter le chemin du répertoire parent pour l'importation de utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import load_shop_config, build_network_path, create_network_folder, SafeStreamHandler

# Désactiver les warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ProsumaAPIArticlePromoExtractor:
    def __init__(self):
        """Initialise l'extracteur avec la configuration"""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        load_dotenv(os.path.join(project_root, 'config.env'))

        self.base_dir = os.path.dirname(__file__)
        self.api_name = "ARTICLE_PROMO"
        
        # Configuration du dossier de logs
        log_base_dir = os.getenv('LOG_FOLDER_BASE')
        if not log_base_dir:
            print("❌ Erreur: LOG_FOLDER_BASE n'est pas configuré dans config.env")
            sys.exit(1)
        
        self.log_dir = build_network_path(log_base_dir, "LOG")
        create_network_folder(self.log_dir)
        
        # Configuration du logging
        log_file = os.path.join(self.log_dir, f'api_article_promo_{datetime.now().strftime("%Y%m%d")}.log')
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)

        self.shops = load_shop_config(os.path.dirname(self.base_dir))
        if not self.shops:
            self.logger.error("❌ Aucun magasin configuré ou fichier magasins.json introuvable.")
            sys.exit(1)

        self.prosuma_user = os.getenv('PROSUMA_USER')
        self.prosuma_password = os.getenv('PROSUMA_PASSWORD')
        self.verify_ssl = False  # Désactiver la vérification SSL pour les serveurs Prosuma
        self.timeout = int(os.getenv('API_TIMEOUT', 30))

        if not self.prosuma_user or not self.prosuma_password:
            self.logger.error("❌ PROSUMA_USER et PROSUMA_PASSWORD doivent être configurés dans config.env")
            sys.exit(1)
        
        self.logger.info(f"Extracteur API Articles avec prix promo Prosuma initialisé pour {self.prosuma_user}")
        self.logger.info(f"Magasins configurés: {[s for s in self.shops.keys()]}")

    def get_network_path_for_shop(self, api_folder_name):
        """Construit le chemin réseau pour un dossier d'API spécifique."""
        network_folder_base = os.getenv('DOWNLOAD_FOLDER_BASE')
        if not network_folder_base:
            self.logger.error("❌ DOWNLOAD_FOLDER_BASE n'est pas configuré dans config.env")
            return None
        return build_network_path(network_folder_base, api_folder_name)

    def _make_api_request(self, url, params=None):
        """Effectue une requête API avec gestion des erreurs et réessais."""
        headers = {'Content-Type': 'application/json'}
        auth = (self.prosuma_user, self.prosuma_password)
        
        try:
            response = requests.get(url, headers=headers, params=params, auth=auth, 
                                    verify=self.verify_ssl, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"❌ Erreur lors de la requête à {url}: {e}")
            return None

    def get_shop_info(self, base_url, shop_code):
        """Récupère les informations détaillées d'un magasin par son code."""
        url = f"{base_url}/api/shop/"
        params = {'code': shop_code}
        response_data = self._make_api_request(url, params)
        if response_data and 'results' in response_data:
            for shop in response_data['results']:
                if shop.get('code') == shop_code:
                    return shop
        return None

    def get_articles_with_promo(self, base_url, shop_id):
        """Récupère tous les articles avec prix promo pour un magasin donné."""
        all_articles = []
        page = 1
        
        self.logger.info("=" * 60)
        self.logger.info("INFORMATIONS D'EXTRACTION")
        self.logger.info("=" * 60)

        while True:
            url = f"{base_url}/api/product/"
            params = {
                'page': page,
                'page_size': 1000,
                'shop': shop_id,
                'has_promo_price': 'true'
            }
            
            response_data = self._make_api_request(url, params)

            if response_data is None:
                self.logger.error(f"❌ Échec de la récupération des articles avec prix promo pour la page {page}.")
                break

            results = response_data.get('results', [])
            if not results:
                self.logger.info(f"   ✅ Dernière page atteinte (page {page})")
                break

            all_articles.extend(results)
            total_articles = response_data.get('count', len(all_articles))
            
            self.logger.info(f"   Page {page}: {len(results)} articles avec prix promo récupérés (total: {len(all_articles)})")

            if response_data.get('next') is None:
                self.logger.info(f"   ✅ Dernière page atteinte (page {page})")
                break
            page += 1
        
        self.logger.info("=" * 60)
        self.logger.info("RÉSUMÉ EXTRACTION")
        self.logger.info("=" * 60)
        self.logger.info(f"Articles avec prix promo trouvés: {total_articles:,}")
        self.logger.info(f"Articles avec prix promo extraits: {len(all_articles):,}")
        if total_articles > 0:
            success_rate = (len(all_articles) / total_articles) * 100
            self.logger.info(f"Taux de réussite: {success_rate:.2f}%")
        else:
            self.logger.info("Taux de réussite: N/A (aucun article trouvé)")
        self.logger.info("=" * 60)

        return all_articles

    def export_to_csv(self, articles, shop_code, shop_name):
        """Exporte les articles avec prix promo vers un fichier CSV."""
        network_path = self.get_network_path_for_shop(self.api_name)
        if not network_path:
            self.logger.error(f"Impossible de créer le dossier réseau pour le magasin {shop_code}")
            return None
        
        # Créer un fichier temporaire local
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'export_article_promo_{shop_code}_{timestamp}.csv'
        local_filepath = os.path.join(self.base_dir, filename)
        
        # En-têtes CSV
        fieldnames = [
            'id', 'name', 'reference', 'barcode', 'category', 'brand', 'supplier',
            'price', 'promo_price', 'promo_start_date', 'promo_end_date',
            'is_active', 'is_available', 'stock_quantity', 'unit', 'weight',
            'volume', 'description', 'short_description', 'ean_codes',
            'shop_code', 'shop_name', 'created_at', 'updated_at', 'deleted_at'
        ]

        try:
            with open(local_filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
                writer.writeheader()
                for article in articles:
                    row = {
                        'id': article.get('id'),
                        'name': article.get('name'),
                        'reference': article.get('reference'),
                        'barcode': article.get('barcode'),
                        'category': article.get('category', {}).get('name') if isinstance(article.get('category'), dict) else article.get('category'),
                        'brand': article.get('brand', {}).get('name') if isinstance(article.get('brand'), dict) else article.get('brand'),
                        'supplier': article.get('supplier', {}).get('name') if isinstance(article.get('supplier'), dict) else article.get('supplier'),
                        'price': article.get('price'),
                        'promo_price': article.get('promo_price'),
                        'promo_start_date': article.get('promo_start_date'),
                        'promo_end_date': article.get('promo_end_date'),
                        'is_active': article.get('is_active'),
                        'is_available': article.get('is_available'),
                        'stock_quantity': article.get('stock_quantity'),
                        'unit': article.get('unit'),
                        'weight': article.get('weight'),
                        'volume': article.get('volume'),
                        'description': article.get('description'),
                        'short_description': article.get('short_description'),
                        'ean_codes': json.dumps(article.get('ean_codes')) if article.get('ean_codes') else '',
                        'shop_code': shop_code,
                        'shop_name': shop_name,
                        'created_at': article.get('created_at'),
                        'updated_at': article.get('updated_at'),
                        'deleted_at': article.get('deleted_at')
                    }
                    writer.writerow(row)
            
            self.logger.info(f"✅ Fichier CSV créé localement: {local_filepath}")
            self.logger.info(f"   {len(articles)} articles avec prix promo exportés")
            self.logger.info(f"   {len(fieldnames)} colonnes par article")
            
            # Copier vers le réseau et supprimer le fichier local
            import shutil
            network_filepath = os.path.join(network_path, filename)
            shutil.copy2(local_filepath, network_filepath)
            self.logger.info(f"✅ Fichier copié sur le réseau: {network_filepath}")
            os.remove(local_filepath)
            self.logger.info(f"🗑️ Fichier local supprimé")
            return network_filepath
        except Exception as e:
            self.logger.error(f"❌ Erreur lors de l'export CSV pour le magasin {shop_code}: {e}")
            return None

    def extract_shop(self, shop_code, shop_info):
        """Extrait les articles avec prix promo pour un magasin spécifique."""
        base_url = shop_info['url']
        shop_name = shop_info['name']
        
        self.logger.info(f"==================================================")
        self.logger.info(f"EXTRACTION ARTICLES AVEC PRIX PROMO MAGASIN {shop_code}")
        self.logger.info(f"==================================================")
        self.logger.info(f"URL serveur: {base_url}")
        self.logger.info(f"Nom magasin: {shop_name}")
        
        # Test de connexion
        if not self._make_api_request(f"{base_url}/api/shop/"):
            self.logger.error(f"❌ Connexion API échouée pour le magasin {shop_code}. Vérifiez l'URL ou les identifiants.")
            return False
        self.logger.info(f"✅ Connexion API réussie: {base_url}")

        # Récupérer l'ID du magasin
        self.logger.info(f"Récupération des informations du magasin {shop_code}...")
        shop_data = self.get_shop_info(base_url, shop_code)
        if not shop_data:
            self.logger.error(f"❌ Magasin {shop_code} non trouvé dans la liste ou erreur API.")
            return False
        shop_id = shop_data.get('id')
        if not shop_id:
            self.logger.error(f"❌ ID du magasin non trouvé")
            return False
        
        # Récupérer les articles avec prix promo
        self.logger.info(f"Récupération des articles avec prix promo pour le magasin {shop_code}...")
        articles = self.get_articles_with_promo(base_url, shop_id)
        
        if not articles:
            self.logger.warning(f"⚠️ Aucun article avec prix promo trouvé pour le magasin {shop_code}")
            return True
        
        self.logger.info(f"✅ {len(articles)} articles avec prix promo récupérés au total pour le magasin {shop_code}")
        
        # Exporter vers CSV
        self.logger.info("=" * 60)
        self.logger.info(f"💾 EXPORT CSV - MAGASIN {shop_code}")
        self.logger.info("=" * 60)
        csv_file = self.export_to_csv(articles, shop_code, shop_name)
        if csv_file:
            self.logger.info("=" * 60)
            self.logger.info(f"✅ MAGASIN {shop_code} TRAITÉ AVEC SUCCÈS")
            self.logger.info("=" * 60)
            self.logger.info(f"📁 Fichier sur le réseau: {csv_file}")
            self.logger.info(f"📊 Lignes exportées: {len(articles):,}")
            self.logger.info("=" * 60)
            return True
        else:
            self.logger.error(f"❌ Erreur lors de l'export pour le magasin {shop_code}")
            return False

    def extract_all(self):
        """Extrait les articles avec prix promo pour tous les magasins configurés"""
        self.logger.info("=" * 60)
        self.logger.info("DÉBUT DE L'EXTRACTION API PROSUMA - ARTICLES AVEC PRIX PROMO")
        self.logger.info("=" * 60)
        
        # Créer le dossier réseau au début
        network_path = self.get_network_path_for_shop(self.api_name)
        if network_path:
            self.logger.info(f"✅ Dossier réseau créé: {network_path}")
        else:
            self.logger.warning("⚠️ Impossible de créer le dossier réseau")

        all_success = True
        for shop_code, shop_info in self.shops.items():
            if not self.extract_shop(shop_code, shop_info):
                all_success = False
        
        if all_success:
            self.logger.info("✅ Toutes les extractions d'articles avec prix promo terminées avec succès.")
        else:
            self.logger.error("❌ Certaines extractions d'articles avec prix promo ont échoué.")

def main():
    """Fonction principale"""
    try:
        extractor = ProsumaAPIArticlePromoExtractor()
        extractor.extract_all()
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")

if __name__ == "__main__":
    main()
