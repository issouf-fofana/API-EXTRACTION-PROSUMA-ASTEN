#!/usr/bin/env python3
"""
Extracteur API Prosuma RPOS - Base Articles
Récupère tous les articles/produits via l'API Prosuma avec pagination automatique
"""

import requests
import os
import csv
import json
import logging
import shutil
import platform
from datetime import datetime
from dotenv import load_dotenv
import urllib3
import sys

# Ajouter le répertoire parent au path pour importer utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import load_shop_config, build_network_path, create_network_folder, SafeStreamHandler

# Désactiver les warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ProsumaAPIBaseArticleExtractor:
    def __init__(self):
        """Initialise l'extracteur avec la configuration"""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        load_dotenv(os.path.join(project_root, 'config.env'))
        
        self.username = os.getenv('PROSUMA_USER')
        self.password = os.getenv('PROSUMA_PASSWORD')
        
        if not self.username or not self.password:
            raise ValueError("PROSUMA_USER et PROSUMA_PASSWORD doivent être configurés dans config.env")
        
        # Configuration du dossier de téléchargement
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.network_folder_base = os.getenv('DOWNLOAD_FOLDER_BASE', '\\10.0.70.169\\share\\FOFANA')
        
        # Configuration des magasins
        self.shop_config = load_shop_config(os.path.dirname(self.base_dir))
        self.shop_codes = list(self.shop_config.keys())
        
        # Configuration du logging sera faite dans setup_logging()
        self.setup_logging()
        
        # Configuration de la session
        self.session = requests.Session()
        self.session.auth = (self.username, self.password)
        self.session.verify = False
        
        print(f"Extracteur API Base Articles initialisé pour {self.username}")
        print(f"Magasins configurés: {self.shop_codes}")
        print(f"Note: Extraction de TOUS les articles (sans filtre de date)")

    def setup_logging(self):
        """Configure le système de logging"""
        # Créer le dossier de logs sur le réseau
        log_network_path = self.get_log_network_path()
        if log_network_path:
            log_file = os.path.join(log_network_path, f'api_base_article_{datetime.now().strftime("%Y%m%d")}.log')
        else:
            # Fallback local
            log_file = os.path.join(self.base_dir, f'api_base_article_{datetime.now().strftime("%Y%m%d")}.log')
        
        # Configuration du logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                SafeStreamHandler()
            ]
        )
        
        # Définir les permissions pour permettre à tous les utilisateurs d'écrire
        from utils import set_log_file_permissions
        set_log_file_permissions(log_file)
        
        global logger
        logger = logging.getLogger(__name__)

    def get_network_path_for_shop(self, shop_code):
        """Retourne le chemin réseau pour un magasin spécifique"""
        network_path = build_network_path(self.network_folder_base, "BASE_ARTICLE")
        if create_network_folder(network_path):
            return network_path
        return None
        
    def get_log_network_path(self):
        """Retourne le chemin réseau pour les logs"""
        if not self.network_folder_base:
            return None
        # Chemin: \\10.0.70.169\share\FOFANA\Etats Natacha\SCRIPT\LOG
        base = self.network_folder_base.replace('/', '\\')
        if base.endswith('\\'):
            base = base[:-1]
        log_path = f"{base}\\Etats Natacha\\SCRIPT\\LOG"
        if create_network_folder(log_path):
            return log_path
        return None

    def test_api_connection(self, base_url):
        """Teste la connexion à l'API"""
        try:
            test_url = f"{base_url}/api/user/"
            response = self.session.get(test_url, timeout=10)
            if response.status_code == 200:
                logger.info(f"✅ Connexion API réussie: {base_url}")
                return True
            else:
                logger.error(f"❌ Erreur de connexion API {base_url}: {response.status_code} {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ Erreur de connexion API {base_url}: {e}")
            return False

    def get_shop_info(self, base_url, shop_code):
        """Récupère les informations d'un magasin"""
        try:
            # Essayer d'abord avec l'endpoint direct
            url = f"{base_url}/api/shop/{shop_code}/"
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                shop_data = response.json()
                if isinstance(shop_data, dict) and shop_data.get('reference') == shop_code:
                    logger.info(f"✅ Magasin {shop_code} trouvé: {shop_data.get('name', 'Nom inconnu')}")
                    return shop_data
            
            # Si pas trouvé, chercher dans la liste paginée
            url = f"{base_url}/api/shop/"
            page = 1
            while True:
                params = {'page': page, 'page_size': 100}
                response = self.session.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    shops = data.get('results', [])
                    
                    for shop in shops:
                        if shop.get('reference') == shop_code:
                            logger.info(f"✅ Magasin {shop_code} trouvé: {shop.get('name', 'Nom inconnu')}")
                            return shop
                    
                    if not data.get('next'):
                        break
                    page += 1
                else:
                    break
            
            logger.warning(f"⚠️ Magasin {shop_code} non trouvé dans la liste")
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des informations du magasin: {e}")
            return None

    def count_total_records(self, base_url, shop_id, page_size=1000):
        """Compte le nombre total d'articles disponibles"""
        try:
            url = f"{base_url}/api/product/"
            params = {
                'shop': shop_id,
                'page_size': page_size,
                'page': 1
            }
            
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                total_count = data.get('count', 0)
                return total_count
            else:
                logger.error(f"❌ Erreur lors du comptage: {response.status_code}")
                return 0
                
        except Exception as e:
            logger.error(f"❌ Erreur lors du comptage: {e}")
            return 0

    def get_articles(self, base_url, shop_id, page_size=1000):
        """Récupère les articles avec pagination complète"""
        # D'abord, compter le nombre total d'articles
        logger.info("🔍 Comptage du nombre total d'articles...")
        total_records = self.count_total_records(base_url, shop_id, page_size)
        
        if total_records == 0:
            logger.warning("⚠️ Aucun article trouvé")
            return []
        
        # Afficher le cadre avec le nombre total
        logger.info("=" * 60)
        logger.info(f"📊 INFORMATIONS D'EXTRACTION - MAGASIN {shop_id}")
        logger.info("=" * 60)
        logger.info(f"📊 Total articles disponibles: {total_records:,}")
        logger.info(f"🏪 Magasin: {shop_id}")
        logger.info("=" * 60)
        
        all_articles = []
        page = 1
        total_pages = (total_records + page_size - 1) // page_size  # Calcul du nombre total de pages
        
        try:
            while page <= total_pages:
                url = f"{base_url}/api/product/"
                params = {
                    'shop': shop_id,
                    'page_size': page_size,
                    'page': page
                }
                
                # Afficher la progression
                progress_percent = (page - 1) * 100 // total_pages if total_pages > 0 else 0
                logger.info(f"📄 Récupération page {page}/{total_pages} ({progress_percent}%) - {len(all_articles):,}/{total_records:,} articles...")
                
                response = self.session.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    articles = data.get('results', [])
                    
                    if not articles:
                        logger.info(f"  ✅ Dernière page atteinte (page {page}) - Aucun article retourné")
                        break
                    
                    all_articles.extend(articles)
                    logger.info(f"  ✅ Page {page}: {len(articles)} articles récupérés (total: {len(all_articles):,}/{total_records:,})")
                    
                    # Vérifier si on a récupéré tous les articles ou si on est à la dernière page
                    if len(all_articles) >= total_records:
                        logger.info(f"  ✅ Tous les articles récupérés (page {page}/{total_pages})")
                        break
                    
                    # Si on est à la dernière page calculée, on arrête
                    if page >= total_pages:
                        logger.info(f"  ✅ Dernière page atteinte (page {page}/{total_pages})")
                        break
                    
                    # Continuer avec la page suivante
                    page += 1
                else:
                    logger.error(f"❌ Erreur lors de la récupération des articles: {response.status_code}")
                    # Continuer avec la page suivante en cas d'erreur temporaire
                    if response.status_code == 500 or response.status_code == 503:
                        logger.warning(f"⚠️ Erreur serveur, tentative de continuer...")
                        page += 1
                        continue
                    break
                    
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des articles: {e}")
            # Si on a récupéré des articles, on continue quand même
            if len(all_articles) > 0:
                logger.warning(f"⚠️ Erreur mais {len(all_articles)} articles déjà récupérés, on continue...")
        
        # Afficher le résumé final
        logger.info("=" * 60)
        logger.info(f"✅ RÉSUMÉ EXTRACTION - MAGASIN {shop_id}")
        logger.info("=" * 60)
        logger.info(f"📊 Articles trouvés: {total_records:,}")
        logger.info(f"📥 Articles extraits: {len(all_articles):,}")
        logger.info(f"📈 Taux de réussite: {(len(all_articles)/total_records*100):.1f}%" if total_records > 0 else "📈 Taux de réussite: 0%")
        logger.info("=" * 60)
        
        return all_articles

    def export_to_csv(self, articles, shop_code, shop_name):
        """Exporte les articles vers un fichier CSV"""
        if not articles:
            logger.warning(f"Aucun article à exporter pour le magasin {shop_code}")
            return None
        
        # Créer le dossier réseau
        network_path = self.get_network_path_for_shop(shop_code)
        if not network_path:
            logger.error(f"Impossible de créer le dossier réseau pour le magasin {shop_code}")
            return None
        
        # Créer un fichier temporaire local
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'export_base_article_{shop_code}_{timestamp}.csv'
        local_filepath = os.path.join(self.base_dir, filename)
        
        # En-têtes CSV basés sur les champs disponibles
        fieldnames = [
            'id', 'name', 'reference', 'barcode', 'category', 'brand', 'supplier',
            'price', 'promo_price', 'promo_start', 'promo_end', 'is_promo',
            'stock_quantity', 'min_stock', 'max_stock', 'unit', 'weight',
            'dimensions', 'description', 'notes', 'is_active', 'created_at',
            'updated_at', 'shop_code', 'shop_name'
        ]
        
        try:
            # Créer le fichier CSV local
            with open(local_filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
                writer.writeheader()
                
                for article in articles:
                    # Préparer les données pour l'export
                    row = {
                        'id': article.get('id', ''),
                        'name': article.get('name', ''),
                        'reference': article.get('reference', ''),
                        'barcode': article.get('barcode', ''),
                        'category': article.get('category', {}).get('name', '') if isinstance(article.get('category'), dict) else '',
                        'brand': article.get('brand', {}).get('name', '') if isinstance(article.get('brand'), dict) else '',
                        'supplier': article.get('supplier', {}).get('name', '') if isinstance(article.get('supplier'), dict) else '',
                        'price': article.get('price', ''),
                        'promo_price': article.get('promo_price', ''),
                        'promo_start': article.get('promo_start', ''),
                        'promo_end': article.get('promo_end', ''),
                        'is_promo': article.get('is_promo', ''),
                        'stock_quantity': article.get('stock_quantity', ''),
                        'min_stock': article.get('min_stock', ''),
                        'max_stock': article.get('max_stock', ''),
                        'unit': article.get('unit', ''),
                        'weight': article.get('weight', ''),
                        'dimensions': article.get('dimensions', ''),
                        'description': article.get('description', ''),
                        'notes': article.get('notes', ''),
                        'is_active': article.get('is_active', ''),
                        'created_at': article.get('created_at', ''),
                        'updated_at': article.get('updated_at', ''),
                        'shop_code': shop_code,
                        'shop_name': shop_name
                    }
                    writer.writerow(row)
            
            logger.info(f"✅ Fichier CSV créé localement: {local_filepath}")
            logger.info(f"   {len(articles)} articles de base exportés")
            logger.info(f"   {len(fieldnames)} colonnes par article")
            
            # Copier vers le réseau et supprimer le fichier local
            network_filepath = os.path.join(network_path, filename)
            shutil.copy2(local_filepath, network_filepath)
            logger.info(f"✅ Fichier copié sur le réseau: {network_filepath}")
            
            # Supprimer le fichier local
            os.remove(local_filepath)
            logger.info(f"🗑️ Fichier local supprimé")
            
            return network_filepath
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'export CSV: {e}")
            return None

    def extract_shop(self, shop_code):
        """Extrait les articles pour un magasin spécifique"""
        shop_info = self.shop_config.get(shop_code)
        if not shop_info:
            logger.error(f"Configuration manquante pour le magasin {shop_code}")
            return False
        
        base_url = shop_info['url']
        shop_name = shop_info['name']
        
        logger.info(f"==================================================")
        logger.info(f"EXTRACTION BASE ARTICLES MAGASIN {shop_code}")
        logger.info(f"==================================================")
        logger.info(f"URL serveur: {base_url}")
        logger.info(f"Nom magasin: {shop_name}")
        
        # Test de connexion
        if not self.test_api_connection(base_url):
            logger.error(f"❌ Impossible de se connecter au serveur {base_url}")
            return False
        
        # Récupérer les informations du magasin
        logger.info(f"Récupération des informations du magasin {shop_code}...")
        shop_data = self.get_shop_info(base_url, shop_code)
        if not shop_data:
            logger.error(f"❌ Impossible de récupérer les informations du magasin {shop_code}")
            return False
        
        shop_id = shop_data.get('id')
        if not shop_id:
            logger.error(f"❌ ID du magasin non trouvé")
            return False
        
        # Récupérer les articles
        logger.info(f"Récupération des articles de base pour le magasin {shop_code}...")
        articles = self.get_articles(base_url, shop_id)
        
        if not articles:
            logger.warning(f"⚠️ Aucun article trouvé pour le magasin {shop_code}")
            return True
        
        logger.info(f"✅ {len(articles)} articles de base récupérés au total pour le magasin {shop_code}")
        
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
        """Extrait les articles pour tous les magasins configurés"""
        logger.info("=" * 60)
        logger.info("DÉBUT DE L'EXTRACTION API PROSUMA - BASE ARTICLES")
        logger.info("=" * 60)
        
        # Créer le dossier réseau au début
        network_path = self.get_network_path_for_shop("BASE_ARTICLE")
        if network_path:
            logger.info(f"✅ Dossier réseau créé: {network_path}")
        else:
            logger.warning("⚠️ Impossible de créer le dossier réseau")
        
        successful_shops = 0
        total_shops = len(self.shop_codes)
        
        for shop_code in self.shop_codes:
            try:
                logger.info(f"\n{'='*60}")
                logger.info(f"TRAITEMENT MAGASIN {shop_code}")
                logger.info(f"{'='*60}")
                
                if self.extract_shop(shop_code):
                    successful_shops += 1
                    logger.info(f"✅ Magasin {shop_code} traité avec succès")
                else:
                    logger.error(f"❌ Erreur lors de l'extraction du magasin {shop_code}")
                    
            except Exception as e:
                logger.error(f"❌ Erreur lors de l'extraction du magasin {shop_code}: {e}")
        
        # Résumé final
        logger.info(f"\n{'='*60}")
        logger.info("RÉSUMÉ DE L'EXTRACTION")
        logger.info(f"{'='*60}")
        logger.info(f"Magasins traités avec succès: {successful_shops}/{total_shops}")
        
        if successful_shops == total_shops:
            logger.info("✅ Extraction complètement réussie")
        elif successful_shops > 0:
            logger.warning("⚠️ Extraction partiellement réussie")
        else:
            logger.error("❌ Aucune extraction réussie")

def main():
    """Fonction principale"""
    try:
        extractor = ProsumaAPIBaseArticleExtractor()
        extractor.extract_all()
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")

if __name__ == "__main__":
    main()
