#!/usr/bin/env python3
"""
Extracteur API Prosuma RPOS - Articles avec prix promo
Récupère les articles avec prix promotionnels via l'API Prosuma avec pagination automatique
"""

import requests
import os
import csv
import json
import logging
from datetime import datetime, timedelta
import urllib3
from dotenv import load_dotenv
import sys

# Ajouter le chemin du répertoire parent pour l'importation de utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import load_shop_config, build_network_path, create_network_folder, SafeStreamHandler

# Désactiver les warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration du logging
def setup_logging(log_dir, api_name):
    log_file = os.path.join(log_dir, f"{api_name.lower().replace(' ', '_')}.log")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

class ProsumaAPIArticlePromoExtractor:
    def __init__(self):
        """Initialise l'extracteur avec la configuration"""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        load_dotenv(os.path.join(project_root, 'config.env'))

        self.base_dir = os.path.dirname(__file__)
        self.api_name = "ARTICLE_PROMO"
        
        # Configuration du dossier de logs
        log_base_dir = os.getenv('DOWNLOAD_FOLDER_BASE')
        if not log_base_dir:
            print("❌ Erreur: DOWNLOAD_FOLDER_BASE n'est pas configuré dans config.env")
            sys.exit(1)
        
        self.log_dir = build_network_path(log_base_dir, "LOG")
        create_network_folder(self.log_dir)
        
        global logger
        logger = setup_logging(self.log_dir, self.api_name)

        self.shops = load_shop_config(os.path.dirname(self.base_dir))
        if not self.shops:
            logger.error("❌ Aucun magasin configuré ou fichier magasins.json introuvable.")
            sys.exit(1)

        self.prosuma_user = os.getenv('PROSUMA_USER')
        self.prosuma_password = os.getenv('PROSUMA_PASSWORD')
        self.verify_ssl = False  # Désactiver la vérification SSL pour les serveurs Prosuma
        self.timeout = int(os.getenv('API_TIMEOUT', 30))
        self.max_retries = int(os.getenv('MAX_RETRIES', 3))
        self.page_size = int(os.getenv('PAGE_SIZE', 1000))

        if not self.prosuma_user or not self.prosuma_password:
            logger.error("❌ PROSUMA_USER et PROSUMA_PASSWORD doivent être configurés dans config.env")
            sys.exit(1)
        
        logger.info(f"Extracteur API Articles avec prix promo Prosuma initialisé pour {self.prosuma_user}")
        logger.info(f"Magasins configurés: {[s['code'] for s in self.shops]}")

    def get_network_path_for_shop(self, api_folder_name):
        """Construit le chemin réseau pour un dossier d'API spécifique."""
        network_folder_base = os.getenv('DOWNLOAD_FOLDER_BASE')
        if not network_folder_base:
            logger.error("❌ DOWNLOAD_FOLDER_BASE n'est pas configuré dans config.env")
            return None
        return build_network_path(network_folder_base, api_folder_name)

    def _make_api_request(self, url, params=None):
        """Effectue une requête API avec gestion des erreurs et réessais."""
        headers = {'Content-Type': 'application/json'}
        auth = (self.prosuma_user, self.prosuma_password)
        
        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, headers=headers, params=params, auth=auth, 
                                        verify=self.verify_ssl, timeout=self.timeout)
                response.raise_for_status()  # Lève une exception pour les codes d'état HTTP 4xx/5xx
                return response.json()
            except requests.exceptions.Timeout:
                logger.warning(f"⏳ Tentative {attempt + 1}/{self.max_retries}: Délai d'attente dépassé pour {url}")
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"🔌 Tentative {attempt + 1}/{self.max_retries}: Erreur de connexion pour {url}: {e}")
            except requests.exceptions.HTTPError as e:
                logger.error(f"❌ Erreur HTTP pour {url}: {e.response.status_code} - {e.response.text}")
                return None
            except Exception as e:
                logger.error(f"❌ Erreur inattendue lors de la requête à {url}: {e}")
                return None
            if attempt < self.max_retries - 1:
                import time
                time.sleep(2 ** attempt) # Attente exponentielle

        logger.error(f"❌ Échec de la requête après {self.max_retries} tentatives pour {url}")
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
        """Récupère tous les articles avec prix promo pour un magasin donné avec pagination."""
        all_articles = []
        page = 1
        
        # D'abord, récupérer le total d'articles avec prix promo
        url = f"{base_url}/api/product/"
        params = {
            'page': 1,
            'page_size': self.page_size,
            'shop': shop_id,
            'has_promo_price': 'true' # Filtre pour les articles avec prix promo
        }
        
        first_response = self._make_api_request(url, params)
        if first_response is None:
            logger.error("❌ Échec de la récupération du nombre total d'articles avec prix promo.")
            return []
        
        total_articles = first_response.get('count', 0)
        total_pages = (total_articles + self.page_size - 1) // self.page_size if total_articles > 0 else 0
        
        logger.info("=" * 60)
        logger.info("INFORMATIONS D'EXTRACTION")
        logger.info("=" * 60)
        logger.info(f"Total articles avec prix promo disponibles: {total_articles:,}")
        logger.info(f"Nombre de pages à récupérer: {total_pages}")
        logger.info("=" * 60)

        # Traiter la première page déjà récupérée
        if first_response:
            results = first_response.get('results', [])
            if results:
                all_articles.extend(results)
                logger.info(f"   Page 1: {len(results)} articles avec prix promo récupérés (total: {len(all_articles):,}/{total_articles:,})")
        
        # Continuer avec les pages suivantes
        page = 2
        while page <= total_pages:
            url = f"{base_url}/api/product/"
            params = {
                'page': page,
                'page_size': self.page_size,
                'shop': shop_id,
                'has_promo_price': 'true' # Filtre pour les articles avec prix promo
            }
            
            response_data = self._make_api_request(url, params)

            if response_data is None:
                logger.error(f"❌ Échec de la récupération des articles avec prix promo pour la page {page}.")
                # Continuer avec la page suivante en cas d'erreur
                page += 1
                continue

            results = response_data.get('results', [])
            if not results:
                logger.info(f"   ✅ Dernière page atteinte (page {page}) - Aucun enregistrement retourné")
                break

            all_articles.extend(results)
            
            progress_percent = (page - 1) * 100 // total_pages if total_pages > 0 else 0
            logger.info(f"   Page {page}/{total_pages} ({progress_percent}%): {len(results)} articles avec prix promo récupérés (total: {len(all_articles):,}/{total_articles:,})")

            # Vérifier si on a récupéré tous les articles ou si on est à la dernière page
            if len(all_articles) >= total_articles:
                logger.info(f"   ✅ Tous les articles récupérés (page {page}/{total_pages})")
                break
            
            # Si on est à la dernière page calculée, on arrête
            if page >= total_pages:
                logger.info(f"   ✅ Dernière page atteinte (page {page}/{total_pages})")
                break
            
            page += 1
        
        logger.info("=" * 60)
        logger.info("RÉSUMÉ EXTRACTION")
        logger.info("=" * 60)
        logger.info(f"Articles avec prix promo trouvés: {total_articles:,}")
        logger.info(f"Articles avec prix promo extraits: {len(all_articles):,}")
        if total_articles > 0:
            success_rate = (len(all_articles) / total_articles) * 100
            logger.info(f"Taux de réussite: {success_rate:.2f}%")
        else:
            logger.info("Taux de réussite: N/A (aucun article trouvé)")
        logger.info("=" * 60)

        return all_articles

    def export_to_csv(self, articles, shop_code, shop_name):
        """Exporte les articles avec prix promo vers un fichier CSV."""
        network_path = self.get_network_path_for_shop(self.api_name)
        if not network_path:
            logger.error(f"Impossible de créer le dossier réseau pour le magasin {shop_code}")
            return None
        
        # Créer un fichier temporaire local
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'export_article_promo_{shop_code}_{timestamp}.csv'
        local_filepath = os.path.join(self.base_dir, filename)
        
        # En-têtes CSV basés sur les champs disponibles et spécifiques aux promos
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
            
            logger.info(f"✅ Fichier CSV créé localement: {local_filepath}")
            logger.info(f"   {len(articles)} articles avec prix promo exportés")
            logger.info(f"   {len(fieldnames)} colonnes par article")
            
            # Copier vers le réseau et supprimer le fichier local
            import shutil
            network_filepath = os.path.join(network_path, filename)
            shutil.copy2(local_filepath, network_filepath)
            logger.info(f"✅ Fichier copié sur le réseau: {network_filepath}")
            os.remove(local_filepath)
            logger.info(f"🗑️ Fichier local supprimé")
            return network_filepath
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'export CSV pour le magasin {shop_code}: {e}")
            return None

    def extract_shop(self, shop_code, shop_info):
        """Extrait les articles avec prix promo pour un magasin spécifique."""
        base_url = shop_info['url']
        shop_name = shop_info['name']
        
        logger.info(f"==================================================")
        logger.info(f"EXTRACTION ARTICLES AVEC PRIX PROMO MAGASIN {shop_code}")
        logger.info(f"==================================================")
        logger.info(f"URL serveur: {base_url}")
        logger.info(f"Nom magasin: {shop_name}")
        
        # Test de connexion
        if not self._make_api_request(f"{base_url}/api/shop/"):
            logger.error(f"❌ Connexion API échouée pour le magasin {shop_code}. Vérifiez l'URL ou les identifiants.")
            return False
        logger.info(f"✅ Connexion API réussie: {base_url}")

        # Récupérer l'ID du magasin
        logger.info(f"Récupération des informations du magasin {shop_code}...")
        shop_data = self.get_shop_info(base_url, shop_code)
        if not shop_data:
            logger.error(f"❌ Magasin {shop_code} non trouvé dans la liste ou erreur API.")
            return False
        shop_id = shop_data.get('id')
        if not shop_id:
            logger.error(f"❌ ID du magasin non trouvé")
            return False
        
        # Récupérer les articles avec prix promo
        logger.info(f"Récupération des articles avec prix promo pour le magasin {shop_code}...")
        articles = self.get_articles_with_promo(base_url, shop_id)
        
        if not articles:
            logger.warning(f"⚠️ Aucun article avec prix promo trouvé pour le magasin {shop_code}")
            return True
        
        logger.info(f"✅ {len(articles)} articles avec prix promo récupérés au total pour le magasin {shop_code}")
        
        # Exporter vers CSV
        logger.info("=" * 60)
        logger.info(f"💾 EXPORT CSV - MAGASIN {shop_code}")
        logger.info("=" * 60)
        csv_file = self.export_to_csv(articles, shop_code, shop_name)
        if csv_file:
            logger.info("=" * 60)
            logger.info(f"✅ MAGASIN {shop_code} TRAITÉ AVEC SUCCÈS")
            logger.info("=" * 60)
            logger.info(f"📁 Fichier sur le réseau: {csv_file}")
            logger.info(f"📊 Lignes exportées: {len(articles):,}")
            logger.info("=" * 60)
            return True
        else:
            logger.error(f"❌ Erreur lors de l'export pour le magasin {shop_code}")
            return False

    def extract_all(self):
        """Extrait les articles avec prix promo pour tous les magasins configurés"""
        logger.info("=" * 60)
        logger.info("DÉBUT DE L'EXTRACTION API PROSUMA - ARTICLES AVEC PRIX PROMO")
        logger.info("=" * 60)
        
        # Créer le dossier réseau au début
        network_path = self.get_network_path_for_shop(self.api_name)
        if network_path:
            logger.info(f"✅ Dossier réseau créé: {network_path}")
        else:
            logger.warning("⚠️ Impossible de créer le dossier réseau")

        all_success = True
        for shop_code, shop_info in self.shops.items():
            if not self.extract_shop(shop_code, shop_info):
                all_success = False
        
        if all_success:
            logger.info("✅ Toutes les extractions d'articles avec prix promo terminées avec succès.")
        else:
            logger.error("❌ Certaines extractions d'articles avec prix promo ont échoué.")

def main():
    """Fonction principale"""
    try:
        extractor = ProsumaAPIArticlePromoExtractor()
        extractor.extract_all()
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")

if __name__ == "__main__":
    main()
