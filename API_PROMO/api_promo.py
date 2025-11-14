#!/usr/bin/env python3
"""
Extracteur API Prosuma RPOS - Promotions
Récupère toutes les promotions via l'API Prosuma avec pagination automatique
"""

import requests
import os
import csv
import json
import logging
import shutil
import platform
from datetime import datetime, timedelta
from dotenv import load_dotenv
import urllib3
import sys

# Ajouter le répertoire parent au path pour importer utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import load_shop_config, build_network_path, create_network_folder, SafeStreamHandler

# Désactiver les warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ProsumaAPIPromoExtractor:
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
        self.network_folder_base = os.getenv('DOWNLOAD_FOLDER_BASE', '\\\\10.0.70.169\\\\share\\\\FOFANA')
        
        # Configuration des magasins
        self.shop_config = load_shop_config(os.path.dirname(self.base_dir))
        self.shop_codes = list(self.shop_config.keys())
        
        # Configuration du logging sera faite dans setup_logging()
        self.setup_logging()
        
        # Session HTTP
        self.session = requests.Session()
        self.session.auth = (self.username, self.password)
        self.session.verify = False

        logger.info(f"Extracteur API Promotions Prosuma initialisé pour {self.username}")
        logger.info(f"Magasins configurés: {self.shop_codes}")

    def setup_logging(self):
        """Configure le logging avec fichier sur le réseau"""
        log_path = self.get_log_network_path()
        if log_path:
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(os.path.join(log_path, 'prosuma_api_promo.log')),
                    SafeStreamHandler()
                ]
            )
        else:
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler('prosuma_api_promo.log'),
                    SafeStreamHandler()
                ]
            )
        
        global logger
        logger = logging.getLogger(__name__)

    def get_network_path_for_shop(self, shop_code):
        """Retourne le chemin réseau pour un magasin spécifique"""
        network_path = build_network_path(self.network_folder_base, "PROMO")
        if create_network_folder(network_path):
            return network_path
        return None
        
    def get_log_network_path(self):
        """Retourne le chemin réseau pour les logs"""
        if not self.network_folder_base:
            return None
        # Chemin: \\\\10.0.70.169\\share\\FOFANA\\Etats Natacha\\SCRIPT\\LOG
        base = self.network_folder_base.replace('/', '\\\\')
        if base.endswith('\\\\'):
            base = base[:-1]
        log_path = f"{base}\\\\Etats Natacha\\\\SCRIPT\\\\LOG"
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
                logger.error(f"❌ Erreur de connexion API {base_url}: {response.status_code} {response.reason}")
                return False
        except Exception as e:
            logger.error(f"❌ Erreur de connexion API {base_url}: {e}")
            return False

    def get_shop_info(self, base_url, shop_code):
        """Récupère les informations du magasin"""
        try:
            url = f"{base_url}/api/shop/"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Gérer la structure paginée
                if isinstance(data, dict) and 'results' in data:
                    shops = data['results']
                elif isinstance(data, list):
                    shops = data
                else:
                    logger.error(f"❌ Format de réponse invalide: {type(data)}")
                    return None
                
                for shop in shops:
                    if str(shop.get('reference')) == str(shop_code):
                        logger.info(f"✅ Magasin {shop_code} trouvé: {shop.get('name', 'N/A')}")
                        return shop
                
                logger.warning(f"⚠️ Magasin {shop_code} non trouvé dans la liste")
                return None
            else:
                logger.error(f"❌ Erreur lors de la récupération des magasins: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des informations du magasin: {e}")
            return None

    
    def count_total_records(self, base_url, shop_id, page_size=1000):
        """Compte le nombre total de promotions disponibles"""
        try:
            url = f"{base_url}/api/promotion/"
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

    def get_promotions(self, base_url, shop_id, page_size=1000):
        """Récupère toutes les promotions avec pagination complète"""
        all_promotions = []
        page = 1
        
        try:
            # D'abord, récupérer le total de promotions
            url = f"{base_url}/api/promotion/"
            params = {
                'shop': shop_id,
                'page_size': page_size,
                'page': 1
            }
            
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"❌ Erreur lors de la récupération des promotions: {response.status_code}")
                return []
            
            first_data = response.json()
            total_records = first_data.get('count', 0)
            total_pages = (total_records + page_size - 1) // page_size if total_records > 0 else 0
            
            logger.info("=" * 60)
            logger.info("INFORMATIONS D'EXTRACTION")
            logger.info("=" * 60)
            logger.info(f"Total promotions disponibles: {total_records:,}")
            logger.info(f"Nombre de pages à récupérer: {total_pages}")
            logger.info("=" * 60)
            
            # Traiter la première page déjà récupérée
            promotions = first_data.get('results', [])
            if promotions:
                all_promotions.extend(promotions)
                logger.info(f"  ✅ Page 1: {len(promotions)} promotions récupérées (total: {len(all_promotions):,}/{total_records:,})")
            
            # Continuer avec les pages suivantes
            page = 2
            while page <= total_pages:
                params = {
                    'shop': shop_id,
                    'page_size': page_size,
                    'page': page
                }
                
                progress_percent = (page - 1) * 100 // total_pages if total_pages > 0 else 0
                logger.info(f"📄 Récupération page {page}/{total_pages} ({progress_percent}%) - {len(all_promotions):,}/{total_records:,} promotions...")
                
                response = self.session.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    promotions = data.get('results', [])
                    
                    if not promotions:
                        logger.info(f"  ✅ Dernière page atteinte (page {page}) - Aucune promotion retournée")
                        break
                    
                    all_promotions.extend(promotions)
                    logger.info(f"  ✅ Page {page}: {len(promotions)} promotions récupérées (total: {len(all_promotions):,}/{total_records:,})")
                    
                    # Vérifier si on a récupéré toutes les promotions ou si on est à la dernière page
                    if len(all_promotions) >= total_records:
                        logger.info(f"  ✅ Toutes les promotions récupérées (page {page}/{total_pages})")
                        break
                    
                    # Si on est à la dernière page calculée, on arrête
                    if page >= total_pages:
                        logger.info(f"  ✅ Dernière page atteinte (page {page}/{total_pages})")
                        break
                    
                    page += 1
                else:
                    logger.error(f"❌ Erreur lors de la récupération des promotions: {response.status_code}")
                    # Continuer avec la page suivante en cas d'erreur temporaire
                    if response.status_code == 500 or response.status_code == 503:
                        logger.warning(f"⚠️ Erreur serveur, tentative de continuer...")
                        page += 1
                        continue
                    break
                    
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des promotions: {e}")
        
        # Afficher le résumé final
        logger.info("=" * 60)
        logger.info("RÉSUMÉ EXTRACTION")
        logger.info("=" * 60)
        logger.info(f"Promotions trouvées: {total_records:,}")
        logger.info(f"Promotions extraites: {len(all_promotions):,}")
        if total_records > 0:
            success_rate = (len(all_promotions) / total_records) * 100
            logger.info(f"Taux de réussite: {success_rate:.2f}%")
        else:
            logger.info("Taux de réussite: N/A (aucune promotion trouvée)")
        logger.info("=" * 60)
        
        return all_promotions

    def export_to_csv(self, promotions, shop_code, shop_name):
        """Exporte les promotions vers un fichier CSV"""
        if not promotions:
            logger.warning(f"Aucune promotion à exporter pour le magasin {shop_code}")
            return None
        
        # Créer le dossier réseau
        network_path = self.get_network_path_for_shop(shop_code)
        if not network_path:
            logger.error(f"Impossible de créer le dossier réseau pour le magasin {shop_code}")
            return None
        
        # Créer un fichier temporaire local
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'export_promo_{shop_code}_{timestamp}.csv'
        local_filepath = os.path.join(self.base_dir, filename)
        
        # En-têtes CSV basés sur les champs disponibles
        fieldnames = [
            'id', 'name', 'description', 'start_date', 'end_date', 'discount_type',
            'discount_value', 'is_active', 'created_at', 'updated_at', 'shop_code', 'shop_name'
        ]
        
        try:
            # Créer le fichier CSV local
            with open(local_filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
                writer.writeheader()
                
                for promotion in promotions:
                    # Préparer les données pour l'export
                    row = {
                        'id': promotion.get('id', ''),
                        'name': promotion.get('name', ''),
                        'description': promotion.get('description', ''),
                        'start_date': promotion.get('start_date', ''),
                        'end_date': promotion.get('end_date', ''),
                        'discount_type': promotion.get('discount_type', ''),
                        'discount_value': promotion.get('discount_value', ''),
                        'is_active': promotion.get('is_active', ''),
                        'created_at': promotion.get('created_at', ''),
                        'updated_at': promotion.get('updated_at', ''),
                        'shop_code': shop_code,
                        'shop_name': shop_name
                    }
                    writer.writerow(row)
            
            logger.info(f"✅ Fichier CSV créé localement: {local_filepath}")
            logger.info(f"   {len(promotions)} promotions exportées")
            logger.info(f"   {len(fieldnames)} colonnes par promotion")
            
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
        """Extrait les promotions pour un magasin spécifique"""
        shop_info = self.shop_config.get(shop_code)
        if not shop_info:
            logger.error(f"Configuration manquante pour le magasin {shop_code}")
            return False
        
        base_url = shop_info['url']
        shop_name = shop_info['name']
        
        logger.info(f"==================================================")
        logger.info(f"EXTRACTION PROMOTIONS MAGASIN {shop_code}")
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
        
        # Récupérer les promotions
        logger.info(f"Récupération des promotions pour le magasin {shop_code}...")
        promotions = self.get_promotions(base_url, shop_id)
        
        if not promotions:
            logger.warning(f"⚠️ Aucune promotion trouvée pour le magasin {shop_code}")
            return True
        
        logger.info(f"✅ {len(promotions)} promotions récupérées au total pour le magasin {shop_code}")
        
        # Exporter vers CSV
        csv_file = self.export_to_csv(promotions, shop_code, shop_name)
        if csv_file:
            logger.info(f"✅ Magasin {shop_code} traité avec succès - Fichier sur le réseau: {csv_file}")
            return True
        else:
            logger.error(f"❌ Erreur lors de l'export pour le magasin {shop_code}")
            return False

    def extract_all(self):
        """Extrait les promotions pour tous les magasins configurés"""
        logger.info("=" * 60)
        logger.info("DÉBUT DE L'EXTRACTION API PROSUMA - PROMOTIONS")
        logger.info("=" * 60)
        
        # Créer le dossier réseau au début
        network_path = self.get_network_path_for_shop("PROMO")
        if network_path:
            logger.info(f"✅ Dossier réseau créé: {network_path}")
        else:
            logger.warning("⚠️ Impossible de créer le dossier réseau")
        
        successful_shops = 0
        total_shops = len(self.shop_codes)
        
        for shop_code in self.shop_codes:
            try:
                if self.extract_shop(shop_code):
                    successful_shops += 1
            except Exception as e:
                logger.error(f"❌ Erreur lors de l'extraction du magasin {shop_code}: {e}")
        
        # Résumé
        logger.info("=" * 60)
        logger.info("RÉSUMÉ DE L'EXTRACTION")
        logger.info("=" * 60)
        logger.info(f"Magasins traités avec succès: {successful_shops}/{total_shops}")
        
        if successful_shops == total_shops:
            logger.info("✅ Extraction complètement réussie")
        elif successful_shops > 0:
            logger.warning(f"⚠️ Extraction partiellement réussie ({successful_shops}/{total_shops})")
        else:
            logger.error("❌ Aucune extraction réussie")

def main():
    """Fonction principale"""
    try:
        extractor = ProsumaAPIPromoExtractor()
        extractor.extract_all()
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")

if __name__ == "__main__":
    main()