#!/usr/bin/env python3
"""
Extracteur API Prosuma RPOS - Produits non trouvés (Event Line)
Récupère les événements de produits non trouvés via l'API event_line
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

class ProsumaAPIProduitNonTrouveExtractor:
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
        
        # Configuration des dates (hier -> aujourd'hui par défaut)
        self.setup_dates()
        
        # Configuration du logging sera faite dans setup_logging()
        self.setup_logging()
        
        # Session HTTP
        self.session = requests.Session()
        self.session.auth = (self.username, self.password)
        self.session.verify = False

        print(f"Extracteur API Produits Non Trouvés Prosuma initialisé pour {self.username}")
        print(f"Magasins configurés: {self.shop_codes}")
        print(f"Période: {self.start_date.strftime('%Y-%m-%d')} à {self.end_date.strftime('%Y-%m-%d')}")

    def setup_logging(self):
        """Configure le logging avec fichier sur le réseau"""
        log_path = self.get_log_network_path()
        if log_path:
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(os.path.join(log_path, 'prosuma_api_produit_non_trouve.log')),
                    SafeStreamHandler()
                ]
            )
        else:
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler('prosuma_api_produit_non_trouve.log'),
                    SafeStreamHandler()
                ]
            )
        
        global logger
        logger = logging.getLogger(__name__)

    def setup_dates(self):
        """Configure les dates de filtrage (hier -> aujourd'hui par défaut)"""
        # Lire les dates depuis config.env
        date_start_str = os.getenv('DATE_START', '').strip()
        date_end_str = os.getenv('DATE_END', '').strip()
        
        if date_start_str and date_end_str:
            # Utiliser les dates personnalisées
            try:
                # Parser les dates et ajouter les heures appropriées
                start_date_only = datetime.strptime(date_start_str, '%Y-%m-%d')
                end_date_only = datetime.strptime(date_end_str, '%Y-%m-%d')
                
                # Ajouter 00:00:00 pour la date de début et 23:59:59 pour la date de fin
                self.start_date = start_date_only.replace(hour=0, minute=0, second=0, microsecond=0)
                self.end_date = end_date_only.replace(hour=23, minute=59, second=59, microsecond=999999)
                
                print(f"Dates personnalisées: {self.start_date.strftime('%Y-%m-%d %H:%M:%S')} à {self.end_date.strftime('%Y-%m-%d %H:%M:%S')}")
            except ValueError:
                print("Format de date invalide, utilisation des dates par défaut")
                self.setup_default_dates()
        else:
            # Utiliser les dates par défaut (hier -> aujourd'hui)
            self.setup_default_dates()
    
    def setup_default_dates(self):
        """Configure les dates par défaut (hier -> aujourd'hui)"""
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        
        # Ajouter les heures appropriées
        self.start_date = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        self.end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        print(f"Dates par défaut: {self.start_date.strftime('%Y-%m-%d %H:%M:%S')} à {self.end_date.strftime('%Y-%m-%d %H:%M:%S')}")

    def get_network_path_for_shop(self, shop_code):
        """Retourne le chemin réseau pour un magasin spécifique"""
        network_path = build_network_path(self.network_folder_base, "PRODUIT_NON_TROUVE")
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


    def display_extraction_frame(self, shop_code, shop_name, total_items, total_pages, period):
        """Affiche un cadre avec les détails de l'extraction"""
        logger.info("┌" + "─" * 78 + "┐")
        logger.info("│" + " " * 78 + "│")
        logger.info(f"│{'📦 EXTRACTION PRODUITS NON TROUVÉS':^78}│")
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

    
    def count_total_records(self, base_url, shop_id, page_size=1000):
        """Compte le nombre total d'enregistrements disponibles"""
        try:
            url = f"{base_url}/api/product/"
            params = {
                'shop': shop_id,
                'page_size': page_size,
                'page': 1
            }
            
            # Ajouter les paramètres de date si disponibles
            if hasattr(self, 'start_date') and hasattr(self, 'end_date'):
                params['date_0'] = self.start_date.strftime('%Y-%m-%dT%H:%M:%S')
                params['date_1'] = self.end_date.strftime('%Y-%m-%dT%H:%M:%S')
            
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

    def get_event_lines(self, base_url, shop_id, page_size=1000):
        """Récupère les données avec pagination complète"""
        # D'abord, compter le nombre total d'enregistrements
        logger.info("🔍 Comptage du nombre total d'enregistrements...")
        total_records = self.count_total_records(base_url, shop_id, page_size)
        
        if total_records == 0:
            logger.warning("⚠️ Aucun enregistrement trouvé")
            return []
        
        # Afficher le cadre avec le nombre total
        logger.info("=" * 60)
        logger.info(f"📊 INFORMATIONS D'EXTRACTION - MAGASIN {shop_id}")
        logger.info("=" * 60)
        logger.info(f"📊 Total enregistrements disponibles: {total_records:,}")
        logger.info(f"📅 Période: {self.start_date.strftime('%Y-%m-%d %H:%M:%S')} à {self.end_date.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"🏪 Magasin: {shop_id}")
        logger.info("=" * 60)
        
        all_data = []
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
                
                # Ajouter les paramètres de date si disponibles
                if hasattr(self, 'start_date') and hasattr(self, 'end_date'):
                    params['date_0'] = self.start_date.strftime('%Y-%m-%dT%H:%M:%S')
                    params['date_1'] = self.end_date.strftime('%Y-%m-%dT%H:%M:%S')
                
                # Afficher la progression
                progress_percent = (page - 1) * 100 // total_pages if total_pages > 0 else 0
                logger.info(f"📄 Récupération page {page}/{total_pages} ({progress_percent}%) - {len(all_data):,}/{total_records:,} enregistrements...")
                
                response = self.session.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    items = data.get('results', [])
                    
                    if not items:
                        logger.info(f"  ✅ Dernière page atteinte (page {page}) - Aucun enregistrement retourné")
                        break
                    
                    all_data.extend(items)
                    logger.info(f"  ✅ Page {page}: {len(items)} éléments récupérés (total: {len(all_data):,}/{total_records:,})")
                    
                    # Vérifier si on a récupéré tous les enregistrements ou si on est à la dernière page
                    if len(all_data) >= total_records:
                        logger.info(f"  ✅ Tous les enregistrements récupérés (page {page}/{total_pages})")
                        break
                    
                    # Si on est à la dernière page calculée, on arrête
                    if page >= total_pages:
                        logger.info(f"  ✅ Dernière page atteinte (page {page}/{total_pages})")
                        break
                    
                    # Continuer avec la page suivante
                    page += 1
                else:
                    logger.error(f"❌ Erreur lors de la récupération des données: {response.status_code}")
                    # Continuer avec la page suivante en cas d'erreur temporaire
                    if response.status_code == 500 or response.status_code == 503:
                        logger.warning(f"⚠️ Erreur serveur, tentative de continuer...")
                        page += 1
                        continue
                    break
                    
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des données: {e}")
        
        # Afficher le résumé final
        logger.info("=" * 60)
        logger.info(f"✅ RÉSUMÉ EXTRACTION - MAGASIN {shop_id}")
        logger.info("=" * 60)
        logger.info(f"📊 Enregistrements trouvés: {total_records:,}")
        logger.info(f"📥 Enregistrements extraits: {len(all_data):,}")
        logger.info(f"📈 Taux de réussite: {(len(all_data)/total_records*100):.1f}%" if total_records > 0 else "📈 Taux de réussite: 0%")
        logger.info("=" * 60)
        
        return all_data

    def export_to_csv(self, events, shop_code, shop_name):
        """Exporte les événements vers un fichier CSV"""
        if not events:
            logger.warning(f"Aucun événement à exporter pour le magasin {shop_code}")
            return None
        
        # Créer le dossier réseau
        network_path = self.get_network_path_for_shop(shop_code)
        if not network_path:
            logger.error(f"Impossible de créer le dossier réseau pour le magasin {shop_code}")
            return None
        
        # Créer un fichier temporaire local
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'export_produit_non_trouve_{shop_code}_{timestamp}.csv'
        local_filepath = os.path.join(self.base_dir, filename)
        
        # En-têtes CSV selon les vraies colonnes de l'API product_not_found
        fieldnames = [
            'id', 'date', 'term', 'receipt__nb', 'receipt__pos__code',
            'receipt__cashier__code', 'receipt__cashier__id', 'receipt__id',
            'shop_code', 'shop_name'
        ]
        
        try:
            # Créer le fichier CSV local
            with open(local_filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
                writer.writeheader()
                
                for event in events:
                    # Préparer les données pour l'export selon les vraies colonnes
                    row = {
                        'id': event.get('id', ''),
                        'date': event.get('date', ''),
                        'term': event.get('term', ''),
                        'receipt__nb': event.get('receipt__nb', ''),  # Numéro du ticket
                        'receipt__pos__code': event.get('receipt__pos__code', ''),  # Code de la caisse
                        'receipt__cashier__code': event.get('receipt__cashier__code', ''),  # Code du caissier
                        'receipt__cashier__id': event.get('receipt__cashier__id', ''),  # ID du caissier
                        'receipt__id': event.get('receipt__id', ''),  # ID du ticket
                        'shop_code': shop_code,
                        'shop_name': shop_name
                    }
                    writer.writerow(row)
            
            logger.info(f"✅ Fichier CSV créé localement: {local_filepath}")
            logger.info(f"   {len(events)} événements exportés")
            logger.info(f"   {len(fieldnames)} colonnes par événement")
            
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
        """Extrait les événements pour un magasin spécifique"""
        shop_info = self.shop_config.get(shop_code)
        if not shop_info:
            logger.error(f"Configuration manquante pour le magasin {shop_code}")
            return False
        
        base_url = shop_info['url']
        shop_name = shop_info['name']
        
        logger.info(f"==================================================")
        logger.info(f"EXTRACTION PRODUITS NON TROUVÉS MAGASIN {shop_code}")
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
        
        # Récupérer les événements
        logger.info(f"Récupération des événements pour le magasin {shop_code}...")
        events = self.get_event_lines(base_url, shop_id)
        
        if not events:
            logger.warning(f"⚠️ Aucun événement de produit non trouvé pour le magasin {shop_code}")
            return True
        
        # Exporter vers CSV
        logger.info("=" * 60)
        logger.info(f"💾 EXPORT CSV - MAGASIN {shop_code}")
        logger.info("=" * 60)
        csv_file = self.export_to_csv(events, shop_code, shop_name)
        if csv_file:
            logger.info("=" * 60)
            logger.info(f"✅ MAGASIN {shop_code} TRAITÉ AVEC SUCCÈS")
            logger.info("=" * 60)
            logger.info(f"📁 Fichier sur le réseau: {csv_file}")
            logger.info(f"📊 Lignes exportées: {len(events):,}")
            logger.info("=" * 60)
            return True
        else:
            logger.error(f"❌ Erreur lors de l'export pour le magasin {shop_code}")
            return False

    def extract_all(self):
        """Extrait les événements pour tous les magasins configurés"""
        logger.info("=" * 60)
        logger.info("DÉBUT DE L'EXTRACTION API PROSUMA - PRODUITS NON TROUVÉS")
        logger.info("=" * 60)
        
        # Créer le dossier réseau au début
        network_path = self.get_network_path_for_shop("PRODUIT_NON_TROUVE")
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
        extractor = ProsumaAPIProduitNonTrouveExtractor()
        extractor.extract_all()
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")

if __name__ == "__main__":
    main()