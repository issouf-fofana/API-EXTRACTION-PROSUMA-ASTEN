#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extracteur API Prosuma RPOS - STATS_VENTE
Récupère les données via l'API product_line
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
import io
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configurer stdout/stderr pour UTF-8 sur Windows
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Ajouter le répertoire parent au path pour importer utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import load_shop_config, build_network_path, create_network_folder, SafeStreamHandler

# Désactiver les warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ProsumaAPIStatsventeExtractor:
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
        
        # Configuration des dates (hier -> aujourd'hui par défaut)
        self.setup_dates()
        
        # Configuration du logging sera faite dans setup_logging()
        self.setup_logging()
        
        # Session HTTP
        self.session = requests.Session()
        self.session.auth = (self.username, self.password)
        self.session.verify = False

        print(f"Extracteur API initialisé pour {self.username}")
        print(f"Magasins configurés: {self.shop_codes}")
        print(f"Période: {self.start_date.strftime('%Y-%m-%d')} à {self.end_date.strftime('%Y-%m-%d')}")

    def setup_logging(self):
        """Configure le logging avec fichier sur le réseau"""
        # Désactiver tous les handlers existants pour éviter les conflits
        root_logger = logging.getLogger()
        root_logger.handlers = []
        
        log_path = self.get_log_network_path()
        if log_path:
            log_file = os.path.join(log_path, f'prosuma_api_stats_vente.log')
        else:
            log_file = f'prosuma_api_stats_vente.log'
        
        # Créer les handlers
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        stream_handler = SafeStreamHandler()
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        stream_handler.setFormatter(formatter)
        
        # Configurer le logger root
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(stream_handler)
        
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
        network_path = build_network_path(self.network_folder_base, "STATS_VENTE")
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
        """Compte le nombre total d'enregistrements disponibles"""
        try:
            url = f"{base_url}/api/product_line/"
            params = {
                'shop': shop_id,
                'page_size': page_size,
                'page': 1,
                'date_0': self.start_date.strftime('%Y-%m-%dT%H:%M:%S'),
                'date_1': self.end_date.strftime('%Y-%m-%dT%H:%M:%S')
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

    def get_data(self, base_url, shop_id, page_size=1000):
        """Récupère les données avec pagination complète et enrichissement"""
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
                url = f"{base_url}/api/product_line/"
                params = {
                    'shop': shop_id,
                    'page_size': page_size,
                    'page': page,
                    'date_0': self.start_date.strftime('%Y-%m-%dT%H:%M:%S'),
                    'date_1': self.end_date.strftime('%Y-%m-%dT%H:%M:%S')
                }
                
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
                    
                    # Enrichir les données avec les informations des tickets et produits
                    enriched_items = self.enrich_data(items, base_url)
                    all_data.extend(enriched_items)
                    
                    # Afficher la progression détaillée
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

    def _fetch_ticket_info(self, receipt_id, base_url):
        """Récupère les informations d'un ticket"""
        try:
            ticket_url = f"{base_url}/api/receipt/{receipt_id}/"
            ticket_response = self.session.get(ticket_url, timeout=10)
            if ticket_response.status_code == 200:
                ticket_data = ticket_response.json()
                return {
                    'ticket_number': ticket_data.get('number', ''),
                    'ticket_date': ticket_data.get('created_at', '')
                }
        except Exception as e:
            logger.debug(f"Impossible de récupérer les infos du ticket {receipt_id}: {e}")
        return None
    
    def _fetch_product_info(self, product_id, base_url):
        """Récupère les informations d'un produit"""
        try:
            product_url = f"{base_url}/api/product/{product_id}/"
            product_response = self.session.get(product_url, timeout=10)
            if product_response.status_code == 200:
                product_data = product_response.json()
                return {
                    'product_name': product_data.get('name', ''),
                    'product_barcode': product_data.get('barcode', '')
                }
        except Exception as e:
            logger.debug(f"Impossible de récupérer les infos du produit {product_id}: {e}")
        return None
    
    def _extract_id(self, value):
        """Extrait l'ID d'une valeur qui peut être un ID simple ou un objet dictionnaire"""
        if value is None:
            return None
        if isinstance(value, dict):
            # Si c'est un dictionnaire, extraire l'ID (généralement 'id' ou l'URL)
            return value.get('id') or value.get('url', '').rstrip('/').split('/')[-1] if value.get('url') else None
        # Si c'est déjà un ID (string, int, etc.), le retourner tel quel
        return value
    
    def enrich_data(self, items, base_url):
        """Enrichit les données avec les informations des tickets et produits en parallèle"""
        if not items:
            return items
        
        enriched_items = items.copy()
        
        # Créer un mapping item -> IDs pour pouvoir enrichir correctement
        item_receipt_map = {}  # item_index -> receipt_id
        item_product_map = {}  # item_index -> product_id
        
        # Collecter tous les IDs uniques pour éviter les doublons
        receipt_ids = set()
        product_ids = set()
        
        for idx, item in enumerate(items):
            receipt_value = item.get('receipt')
            product_value = item.get('product')
            
            receipt_id = self._extract_id(receipt_value)
            product_id = self._extract_id(product_value)
            
            if receipt_id:
                receipt_ids.add(receipt_id)
                item_receipt_map[idx] = receipt_id
            
            if product_id:
                product_ids.add(product_id)
                item_product_map[idx] = product_id
        
        # Créer des dictionnaires pour stocker les résultats
        ticket_cache = {}
        product_cache = {}
        
        # Utiliser ThreadPoolExecutor pour les requêtes parallèles
        max_workers = min(20, len(receipt_ids) + len(product_ids))  # Limiter à 20 threads max
        
        if receipt_ids or product_ids:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Soumettre toutes les tâches
                future_to_receipt = {
                    executor.submit(self._fetch_ticket_info, receipt_id, base_url): receipt_id 
                    for receipt_id in receipt_ids
                }
                future_to_product = {
                    executor.submit(self._fetch_product_info, product_id, base_url): product_id 
                    for product_id in product_ids
                }
                
                # Récupérer les résultats des tickets
                for future in as_completed(future_to_receipt):
                    receipt_id = future_to_receipt[future]
                    try:
                        ticket_info = future.result()
                        if ticket_info:
                            ticket_cache[receipt_id] = ticket_info
                    except Exception as e:
                        logger.debug(f"Erreur lors de la récupération du ticket {receipt_id}: {e}")
                
                # Récupérer les résultats des produits
                for future in as_completed(future_to_product):
                    product_id = future_to_product[future]
                    try:
                        product_info = future.result()
                        if product_info:
                            product_cache[product_id] = product_info
                    except Exception as e:
                        logger.debug(f"Erreur lors de la récupération du produit {product_id}: {e}")
        
        # Enrichir les items avec les données en cache
        for idx, item in enumerate(enriched_items):
            # Enrichir avec les informations du ticket
            if idx in item_receipt_map:
                receipt_id = item_receipt_map[idx]
                if receipt_id in ticket_cache:
                    ticket_info = ticket_cache[receipt_id]
                    item['ticket_number'] = ticket_info.get('ticket_number', '')
                    item['ticket_date'] = ticket_info.get('ticket_date', '')
            
            # Enrichir avec les informations du produit
            if idx in item_product_map:
                product_id = item_product_map[idx]
                if product_id in product_cache:
                    product_info = product_cache[product_id]
                    item['product_name'] = product_info.get('product_name', '')
                    item['product_barcode'] = product_info.get('product_barcode', '')
        
        return enriched_items

    def export_to_csv(self, data, shop_code, shop_name):
        """Exporte les données vers un fichier CSV"""
        if not data:
            logger.warning(f"Aucune donnée à exporter pour le magasin {shop_code}")
            return None
        
        # Créer le dossier réseau
        network_path = self.get_network_path_for_shop(shop_code)
        if not network_path:
            logger.error(f"Impossible de créer le dossier réseau pour le magasin {shop_code}")
            return None
        
        # Créer un fichier temporaire local
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'export_stats_vente_{shop_code}_{timestamp}.csv'
        local_filepath = os.path.join(self.base_dir, filename)
        
        # En-têtes CSV selon la documentation API product_line
        fieldnames = [
            'id', 'Magasin', 'Ticket', 'Numéro Ticket', 'Date', 'Date Ticket', 
            'Quantité', 'Prix original', 'Prix vente', 'Motif', 'EAN', 
            'EAN D.L.V. / variante / N° de lot', 'EAN saisi', 'Label 1',
            'Nom Produit', 'Code Barre Produit', 'Prix d\'achat', 'Remise', 
            'Taux T.V.A.', 'Total T.T.C.', 'Total H.T.', 'Total T.V.A.', 
            'Points', 'Pesé manuellement', 'Article scanné', 'Quantité retournée', 
            'Numéro de série', 'Vendeur', 'Département'
        ]
        
        try:
            # Créer le fichier CSV local avec séparateur point-virgule
            with open(local_filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
                writer.writeheader()
                
                for item in data:
                    # Extraire le numéro de ticket si c'est un dictionnaire
                    receipt_info = item.get('receipt', '')
                    ticket_number = ''
                    ticket_date = ''
                    
                    if isinstance(receipt_info, dict):
                        ticket_number = receipt_info.get('nb', '')
                        ticket_date = receipt_info.get('date', '')
                    elif isinstance(receipt_info, str):
                        ticket_number = receipt_info
                    
                    # Préparer les données pour l'export selon la documentation API product_line
                    row = {
                        'id': item.get('id', ''),
                        'Magasin': shop_code,
                        'Ticket': ticket_number,
                        'Numéro Ticket': item.get('ticket_number', ''),
                        'Date': item.get('date', ''),
                        'Date Ticket': ticket_date or item.get('ticket_date', ''),
                        'Quantité': item.get('quantity', ''),
                        'Prix original': item.get('original_price', ''),
                        'Prix vente': item.get('selling_price', ''),
                        'Motif': item.get('motive_text', ''),
                        'EAN': item.get('ean', ''),
                        'EAN D.L.V. / variante / N° de lot': item.get('input_ean', ''),
                        'EAN saisi': item.get('input_ean', ''),
                        'Label 1': item.get('label_1', ''),
                        'Nom Produit': item.get('product_name', ''),
                        'Code Barre Produit': item.get('product_barcode', ''),
                        'Prix d\'achat': item.get('buying_price', ''),
                        'Remise': item.get('discount', ''),
                        'Taux T.V.A.': item.get('vat_rate', ''),
                        'Total T.T.C.': item.get('total_incl_tax', ''),
                        'Total H.T.': item.get('total_excl_tax', ''),
                        'Total T.V.A.': item.get('total_vat', ''),
                        'Points': item.get('points', ''),
                        'Pesé manuellement': 'Oui' if item.get('manual_weight', False) else 'Non',
                        'Article scanné': 'Oui' if item.get('scanned', False) else 'Non',
                        'Quantité retournée': item.get('returned_quantity', ''),
                        'Numéro de série': item.get('serial_number', ''),
                        'Vendeur': item.get('seller', ''),
                        'Département': item.get('department', '')
                    }
                    writer.writerow(row)
            
            logger.info(f"✅ Fichier CSV créé localement: {local_filepath}")
            logger.info(f"   {len(data)} éléments exportés")
            logger.info(f"   {len(fieldnames)} colonnes par élément")
            
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
        """Extrait les données pour un magasin spécifique"""
        shop_info = self.shop_config.get(shop_code)
        if not shop_info:
            logger.error(f"Configuration manquante pour le magasin {shop_code}")
            return False
        
        base_url = shop_info['url']
        shop_name = shop_info['name']
        
        logger.info(f"==================================================")
        logger.info(f"EXTRACTION STATS_VENTE MAGASIN {shop_code}")
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
        
        # Vérifier que shop_data est un dictionnaire
        if not isinstance(shop_data, dict):
            logger.error(f"❌ Format de données du magasin invalide: {type(shop_data)}")
            return False
        
        shop_id = shop_data.get('id')
        if not shop_id:
            logger.error(f"❌ ID du magasin non trouvé")
            return False
        
        # Récupérer les données
        logger.info(f"Récupération des données pour le magasin {shop_code}...")
        data = self.get_data(base_url, shop_id)
        
        if not data:
            logger.warning(f"⚠️ Aucune donnée trouvée pour le magasin {shop_code}")
            return True
        
        logger.info(f"✅ {len(data)} éléments récupérés au total pour le magasin {shop_code}")
        
        # Exporter vers CSV
        logger.info("=" * 60)
        logger.info(f"💾 EXPORT CSV - MAGASIN {shop_code}")
        logger.info("=" * 60)
        csv_file = self.export_to_csv(data, shop_code, shop_name)
        if csv_file:
            logger.info("=" * 60)
            logger.info(f"✅ MAGASIN {shop_code} TRAITÉ AVEC SUCCÈS")
            logger.info("=" * 60)
            logger.info(f"📁 Fichier sur le réseau: {csv_file}")
            logger.info(f"📊 Lignes exportées: {len(data):,}")
            logger.info("=" * 60)
            return True
        else:
            logger.error(f"❌ Erreur lors de l'export pour le magasin {shop_code}")
            return False

    def extract_all(self):
        """Extrait les données pour tous les magasins configurés"""
        logger.info("=" * 60)
        logger.info("DÉBUT DE L'EXTRACTION API PROSUMA - STATS_VENTE")
        logger.info("=" * 60)
        
                # Créer le dossier réseau au début
        network_path = self.get_network_path_for_shop("STATS_VENTE")
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
        extractor = ProsumaAPIStatsventeExtractor()
        extractor.extract_all()
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")

if __name__ == "__main__":
    main()
