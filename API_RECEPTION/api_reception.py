#!/usr/bin/env python3
"""
Extracteur API Prosuma RPOS - RECEPTION
Récupère les données via l'API delivery
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

class ProsumaAPIReceptionExtractor:
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
        log_path = self.get_log_network_path()
        if log_path:
            log_file = os.path.join(log_path, f'prosuma_api_reception.log')
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(log_file, encoding='utf-8'),
                    SafeStreamHandler()
                ]
            )
        else:
            log_file = f'prosuma_api_reception.log'
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

    def setup_dates(self):
        """Configure les dates de filtrage (hier -> aujourd'hui par défaut)"""
        # Lire les dates depuis config.env
        date_start_str = os.getenv('DATE_START', '').strip()
        date_end_str = os.getenv('DATE_END', '').strip()
        
        if date_start_str and date_end_str:
            # Utiliser les dates personnalisées
            try:
                self.start_date = datetime.strptime(date_start_str, '%Y-%m-%d')
                self.end_date = datetime.strptime(date_end_str, '%Y-%m-%d')
                print(f"Dates personnalisées: {self.start_date.strftime('%Y-%m-%d')} à {self.end_date.strftime('%Y-%m-%d')}")
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
        
        self.start_date = yesterday
        self.end_date = today
        
        print(f"Dates par défaut: {self.start_date.strftime('%Y-%m-%d')} à {self.end_date.strftime('%Y-%m-%d')}")

    def get_network_path_for_shop(self, shop_code):
        """Retourne le chemin réseau pour un magasin spécifique"""
        network_path = build_network_path(self.network_folder_base, "RECEPTION")
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
    
    def get_order_info(self, base_url, order_id):
        """Récupère les informations complètes d'une commande via l'API /api/supplier_order/{id}/"""
        if not order_id:
            return None
        
        try:
            # Essayer d'abord avec l'endpoint direct
            url = f"{base_url}/api/supplier_order/{order_id}/"
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                order_data = response.json()
                if isinstance(order_data, dict):
                    return order_data
            
            return None
            
        except Exception as e:
            logger.debug(f"⚠️ Erreur lors de la récupération de la commande {order_id}: {e}")
            return None
    
    def get_supplier_info(self, base_url, supplier_id):
        """Récupère les informations complètes d'un fournisseur via l'API /api/supplier/{id}/"""
        if not supplier_id:
            return None
        
        try:
            # Essayer d'abord avec l'endpoint direct
            url = f"{base_url}/api/supplier/{supplier_id}/"
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                supplier_data = response.json()
                if isinstance(supplier_data, dict):
                    return supplier_data
            
            return None
            
        except Exception as e:
            logger.debug(f"⚠️ Erreur lors de la récupération du fournisseur {supplier_id}: {e}")
            return None
    
    def enrich_deliveries_with_order_info(self, base_url, deliveries):
        """Enrichit les réceptions avec les informations complètes de la commande (is_direct, is_central)"""
        if not deliveries:
            return deliveries
        
        logger.info(f"🔍 Enrichissement des réceptions avec les informations des commandes...")
        
        # Collecter tous les IDs de commandes uniques
        order_ids = set()
        for delivery in deliveries:
            order = delivery.get('order')
            if isinstance(order, dict):
                order_id = order.get('id')
                if order_id:
                    order_ids.add(order_id)
            elif isinstance(order, str):
                # Si order est une URL, extraire l'ID
                if order.endswith('/'):
                    order = order[:-1]
                order_id = order.split('/')[-1]
                if order_id:
                    order_ids.add(order_id)
        
        logger.info(f"   📊 {len(order_ids)} commande(s) unique(s) à récupérer")
        
        # Créer un cache pour les informations des commandes
        order_cache = {}
        supplier_cache = {}
        
        for order_id in order_ids:
            order_info = self.get_order_info(base_url, order_id)
            if order_info:
                order_cache[order_id] = order_info
                
                # Récupérer aussi les informations du fournisseur si disponible
                supplier = order_info.get('supplier', {})
                supplier_id = None
                
                if isinstance(supplier, dict):
                    supplier_id = supplier.get('id')
                elif isinstance(supplier, str):
                    if supplier.endswith('/'):
                        supplier = supplier[:-1]
                    supplier_id = supplier.split('/')[-1]
                
                if supplier_id and supplier_id not in supplier_cache:
                    supplier_info = self.get_supplier_info(base_url, supplier_id)
                    if supplier_info:
                        supplier_cache[supplier_id] = supplier_info
        
        logger.info(f"   ✅ {len(order_cache)} commande(s) récupérée(s)")
        logger.info(f"   ✅ {len(supplier_cache)} fournisseur(s) récupéré(s)")
        
        # Enrichir les réceptions avec les informations de la commande
        enriched_count = 0
        for delivery in deliveries:
            order = delivery.get('order')
            order_id = None
            
            if isinstance(order, dict):
                order_id = order.get('id')
            elif isinstance(order, str):
                if order.endswith('/'):
                    order = order[:-1]
                order_id = order.split('/')[-1]
            
            if order_id and order_id in order_cache:
                order_info = order_cache[order_id]
                
                # Pour les réceptions : is_central=True = commande directe, is_central=False = commande réassort
                # Enrichir le supplier dans order avec is_central
                supplier = order_info.get('supplier', {})
                supplier_id = None
                
                if isinstance(supplier, dict):
                    supplier_id = supplier.get('id')
                elif isinstance(supplier, str):
                    if supplier.endswith('/'):
                        supplier = supplier[:-1]
                    supplier_id = supplier.split('/')[-1]
                
                if supplier_id and supplier_id in supplier_cache:
                    supplier_info = supplier_cache[supplier_id]
                    supplier_is_central = supplier_info.get('is_central', False)
                    
                    # Enrichir l'objet order dans la réception
                    if isinstance(delivery.get('order'), dict):
                        if isinstance(delivery.get('order', {}).get('supplier'), dict):
                            delivery['order']['supplier']['is_central'] = supplier_is_central
                    
                    # Pour les réceptions : is_central=True = commande directe, is_central=False = commande réassort
                    # supplier.is_central=True = fournisseur central (réassort)
                    # supplier.is_central=False = fournisseur non central (direct)
                    # Donc pour la réception : is_central = NOT supplier.is_central
                    delivery['is_central'] = not supplier_is_central
                
                # Ajouter aussi is_direct si disponible dans order_info
                if 'is_direct' in order_info:
                    delivery['is_direct'] = order_info.get('is_direct')
                    if isinstance(delivery.get('order'), dict):
                        delivery['order']['is_direct'] = order_info.get('is_direct')
                
                enriched_count += 1
        
        logger.info(f"   ✅ {enriched_count} réception(s) enrichie(s) avec is_direct/is_central")
        return deliveries

    
    def count_total_records(self, base_url, shop_id, page_size=1000):
        """Compte le nombre total d'enregistrements disponibles (réceptions de commandes directes)"""
        try:
            url = f"{base_url}/api/delivery/"
            params = {
                'shop': shop_id,
                'page_size': page_size,
                'page': 1,
                'is_central': 'true'  # Filtrer pour les réceptions de commandes directes (is_central=true = commande directe)
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

    def get_data(self, base_url, shop_id, page_size=1000):
        """Récupère les réceptions de commandes directes avec pagination complète"""
        # D'abord, compter le nombre total d'enregistrements
        logger.info("🔍 Comptage du nombre total de réceptions de commandes directes...")
        total_records = self.count_total_records(base_url, shop_id, page_size)
        
        if total_records == 0:
            logger.warning("⚠️ Aucune réception de commande directe trouvée")
            return []
        
        # Afficher le cadre avec le nombre total
        logger.info("=" * 60)
        logger.info(f"📊 INFORMATIONS D'EXTRACTION - MAGASIN {shop_id}")
        logger.info("=" * 60)
        logger.info(f"📊 Total réceptions de commandes directes disponibles: {total_records:,}")
        logger.info(f"📅 Période: {self.start_date.strftime('%Y-%m-%d %H:%M:%S')} à {self.end_date.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"🏪 Magasin: {shop_id}")
        logger.info("=" * 60)
        
        all_data = []
        page = 1
        total_pages = (total_records + page_size - 1) // page_size  # Calcul du nombre total de pages
        
        logger.info(f"🔍 Filtres API appliqués:")
        logger.info(f"   - is_central: true (réceptions de commandes directes)")
        
        try:
            while page <= total_pages:
                url = f"{base_url}/api/delivery/"
                params = {
                    'shop': shop_id,
                    'page_size': page_size,
                    'page': page,
                    'is_central': 'true'  # Filtrer pour les réceptions de commandes directes (is_central=true = commande directe)
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
                    logger.info(f"  ✅ Page {page}: {len(items)} réceptions récupérées (total: {len(all_data):,}/{total_records:,})")
                    
                    # Vérifier si on a récupéré tous les enregistrements ou si on est à la dernière page
                    if len(all_data) >= total_records:
                        logger.info(f"  ✅ Toutes les réceptions récupérées (page {page}/{total_pages})")
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
        
        # Enrichir les réceptions avec les informations de la commande (order) pour obtenir is_direct et is_central
        if all_data:
            logger.info(f"🔍 Enrichissement des réceptions avec les informations des commandes...")
            all_data = self.enrich_deliveries_with_order_info(base_url, all_data)
        
        # Filtre de sécurité supplémentaire : vérifier que les réceptions sont bien des commandes directes
        original_count = len(all_data)
        filtered_data = []
        reassort_excluded = 0
        
        if all_data:
            # Analyser la première réception pour voir la structure après enrichissement
            first_delivery = all_data[0]
            has_is_central = 'is_central' in first_delivery
            has_is_direct = 'is_direct' in first_delivery
            
            # Vérifier aussi dans order si les champs ne sont pas directement dans delivery
            if not has_is_central and not has_is_direct:
                order = first_delivery.get('order', {})
                if isinstance(order, dict):
                    has_is_central = 'is_central' in order or (isinstance(order.get('supplier'), dict) and 'is_central' in order.get('supplier', {}))
                    has_is_direct = 'is_direct' in order
            
            logger.info(f"🔍 Analyse des champs API (après enrichissement):")
            logger.info(f"   - is_central présent: {'✅ OUI' if has_is_central else '❌ NON'}")
            logger.info(f"   - is_direct présent: {'✅ OUI' if has_is_direct else '❌ NON'}")
            
            if has_is_central:
                # Filtre de sécurité : vérifier is_central=True (commande directe)
                # is_central=True = commande directe
                # is_central=False = commande réassort
                for delivery in all_data:
                    is_central = delivery.get('is_central', None)
                    
                    # Si pas dans delivery, chercher dans order
                    if is_central is None:
                        order = delivery.get('order', {})
                        if isinstance(order, dict):
                            is_central = order.get('is_central', None)
                            if is_central is None:
                                supplier = order.get('supplier', {})
                                if isinstance(supplier, dict):
                                    is_central = supplier.get('is_central', None)
                    
                    if is_central is not None:
                        if is_central:  # is_central=True = commande directe
                            filtered_data.append(delivery)
                        else:
                            reassort_excluded += 1
                            logger.debug(f"❌ Réception réassort exclue par filtre de sécurité: {delivery.get('delivery_number', delivery.get('id', 'N/A'))} (is_central=False)")
                    else:
                        # Si is_central n'est pas défini, on garde (le filtre API is_central=true a déjà filtré)
                        filtered_data.append(delivery)
            elif has_is_direct:
                # Filtre de sécurité : vérifier is_direct=True (commande directe)
                for delivery in all_data:
                    is_direct = delivery.get('is_direct', None)
                    
                    # Si pas dans delivery, chercher dans order
                    if is_direct is None:
                        order = delivery.get('order', {})
                        if isinstance(order, dict):
                            is_direct = order.get('is_direct', None)
                    
                    if is_direct is not None:
                        if is_direct:  # is_direct=True = commande directe
                            filtered_data.append(delivery)
                        else:
                            reassort_excluded += 1
                            logger.debug(f"❌ Réception réassort exclue par filtre de sécurité: {delivery.get('delivery_number', delivery.get('id', 'N/A'))} (is_direct=False)")
                    else:
                        # Si is_direct n'est pas défini, on garde (le filtre API is_direct=true a déjà filtré)
                        filtered_data.append(delivery)
            else:
                # Les champs n'existent toujours pas après enrichissement
                logger.warning(f"⚠️⚠️⚠️ ATTENTION: Les champs is_central et is_direct n'existent toujours pas après enrichissement ⚠️⚠️⚠️")
                logger.warning(f"   On fait confiance au filtre API (is_central=true)")
                logger.warning(f"   Toutes les {original_count} réceptions sont acceptées comme commandes directes")
                filtered_data = all_data.copy()
        
        all_data = filtered_data
        filtered_count = len(all_data)
        
        if reassort_excluded > 0:
            logger.warning(f"⚠️ {reassort_excluded} réception(s) réassort exclue(s) par le filtre de sécurité")
        
        # Afficher le résumé final
        logger.info("=" * 60)
        logger.info(f"✅ RÉSUMÉ EXTRACTION - MAGASIN {shop_id}")
        logger.info("=" * 60)
        logger.info(f"📊 Réceptions de commandes directes trouvées: {total_records:,}")
        logger.info(f"📥 Réceptions extraites (après filtre de sécurité): {filtered_count:,}")
        if total_records > 0:
            logger.info(f"📈 Taux de réussite: {(filtered_count/total_records*100):.1f}%")
        logger.info("=" * 60)
        
        return all_data

    def _flatten_value(self, value, max_length=1000):
        """Convertit une valeur complexe (dict, list) en chaîne JSON formatée pour le CSV."""
        if value is None:
            return ''
        elif isinstance(value, bool):
            return 'Oui' if value else 'Non'
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            # Nettoyer les retours à la ligne et caractères spéciaux
            cleaned = value.replace('\n', ' ').replace('\r', ' ').replace(';', ',')
            if len(cleaned) > max_length:
                return cleaned[:max_length] + '...'
            return cleaned
        elif isinstance(value, dict):
            # Pour les dictionnaires, créer une représentation plus lisible
            try:
                json_str = json.dumps(value, ensure_ascii=False, indent=None)
                if len(json_str) > max_length:
                    return json_str[:max_length] + '...'
                return json_str
            except (TypeError, ValueError):
                return str(value)
        elif isinstance(value, list):
            # Pour les listes, créer une représentation plus lisible
            if not value:
                return ''
            try:
                # Si c'est une liste de dictionnaires, extraire les champs importants
                if value and isinstance(value[0], dict):
                    # Extraire les champs clés de chaque élément
                    simplified = []
                    for item in value[:10]:  # Limiter à 10 éléments
                        if isinstance(item, dict):
                            # Extraire les champs les plus importants
                            item_str = {}
                            for key in ['id', 'name', 'reference', 'quantity', 'price', 'barcode', 'ean']:
                                if key in item:
                                    item_str[key] = item[key]
                            if item_str:
                                simplified.append(item_str)
                    if simplified:
                        json_str = json.dumps(simplified, ensure_ascii=False, indent=None)
                        if len(json_str) > max_length:
                            return json_str[:max_length] + '...'
                        return json_str
                
                # Sinon, convertir en JSON simple
                json_str = json.dumps(value, ensure_ascii=False, indent=None)
                if len(json_str) > max_length:
                    return json_str[:max_length] + '...'
                return json_str
            except (TypeError, ValueError):
                return str(value)
        else:
            return str(value)
    
    def _flatten_nested_object(self, obj, prefix='', max_depth=3, top_level_keys=None):
        """Aplatit un objet imbriqué en dictionnaire plat avec préfixes.
        
        Args:
            obj: L'objet dictionnaire à aplatir
            prefix: Préfixe à ajouter aux noms de champs
            max_depth: Profondeur maximale d'aplatissement
            top_level_keys: Set des clés de niveau supérieur pour éviter les doublons
        """
        if not isinstance(obj, dict) or max_depth <= 0:
            return {}
        
        if top_level_keys is None:
            top_level_keys = set()
        
        flattened = {}
        for key, value in obj.items():
            # Si c'est un champ de niveau supérieur et qu'on n'a pas de préfixe, on le garde tel quel
            # Sinon, on ajoute un préfixe pour éviter les conflits
            if prefix:
                field_name = f"{prefix}_{key}"
            else:
                # Si c'est un champ de niveau supérieur, on le garde tel quel
                # Sinon, on ajoute un préfixe basé sur la clé parente
                field_name = key
            
            if isinstance(value, dict):
                # Récursivement aplatir les dictionnaires imbriqués
                nested = self._flatten_nested_object(value, field_name, max_depth - 1, top_level_keys)
                flattened.update(nested)
                
                # Ajouter aussi les champs les plus importants directement avec des noms clairs
                # Toujours utiliser un préfixe pour éviter les conflits avec les champs de niveau supérieur
                important_fields = {
                    'id': f"{field_name}_id",
                    'name': f"{field_name}_name",
                    'reference': f"{field_name}_reference",
                    'code': f"{field_name}_code",
                    'email': f"{field_name}_email",
                    'phone': f"{field_name}_phone",
                    'address': f"{field_name}_address",
                    'is_central': f"{field_name}_is_central",
                    'is_direct': f"{field_name}_is_direct",
                    'status': f"{field_name}_status",
                    'status_display': f"{field_name}_status_display",
                    'date': f"{field_name}_date",
                    'delivery_date': f"{field_name}_delivery_date",
                    'delivery_number': f"{field_name}_delivery_number",
                    'validation_date': f"{field_name}_validation_date",
                    'created_at': f"{field_name}_created_at",
                    'updated_at': f"{field_name}_updated_at",
                    'validated_by': f"{field_name}_validated_by",
                    'validated': f"{field_name}_validated",
                    'total': f"{field_name}_total",
                    'total_ht': f"{field_name}_total_ht",
                    'total_ttc': f"{field_name}_total_ttc",
                    'quantity': f"{field_name}_quantity"
                }
                
                for field_key, flat_name in important_fields.items():
                    if field_key in value:
                        # Vérifier que le nom de champ aplati ne crée pas de doublon avec un champ de niveau supérieur
                        if flat_name not in top_level_keys:
                            flattened[flat_name] = value.get(field_key)
            elif isinstance(value, list) and value:
                if isinstance(value[0], dict):
                    # Pour les listes de dictionnaires, extraire les champs importants du premier élément
                    count_field = f"{field_name}_count"
                    if count_field not in top_level_keys:
                        flattened[count_field] = len(value)
                    if value:
                        first_item = value[0]
                        # Extraire les champs importants du premier élément
                        for field_key in ['id', 'name', 'reference', 'quantity', 'price', 'barcode', 'ean']:
                            if field_key in first_item:
                                first_field_name = f"{field_name}_first_{field_key}"
                                if first_field_name not in top_level_keys:
                                    flattened[first_field_name] = first_item.get(field_key)
                else:
                    # Liste de valeurs simples - seulement si le champ n'existe pas déjà au niveau supérieur
                    if field_name not in top_level_keys or prefix:
                        flattened[field_name] = ', '.join(str(v) for v in value[:10])  # Limiter à 10 éléments
            else:
                # Pour les valeurs simples, seulement ajouter si le champ n'existe pas déjà au niveau supérieur
                # ou si on a un préfixe (ce qui signifie qu'on est dans un objet imbriqué)
                if field_name not in top_level_keys or prefix:
                    flattened[field_name] = value
        
        return flattened
    
    def _get_all_fields_from_data(self, data):
        """Détecte tous les champs disponibles dans les données, y compris les champs aplatis des objets imbriqués."""
        all_fields = set()
        flattened_fields = set()
        
        # Liste des champs importants à toujours inclure (même s'ils ne sont pas détectés)
        # Basée sur la documentation API /api/delivery/
        important_fields_always = [
            # Champs de base (selon doc API)
            'id',                           # uuid
            'name',                         # nom affiché
            'delivery_number',              # N° de bon livraison
            'date',                         # Date (obligatoire)
            'validation_date',             # Date validation
            'validated',                    # Validé (boolean)
            'delivery_type',                # Type de réception (1=réception, 2=retour fournisseur)
            'is_central',                   # Is central
            'created_at',                   # Date creation
            'updated_at',                   # Date modification
            'deleted_at',                   # Date suppression
            # Champs quantités et prix (selon doc API)
            'total_quantity',               # Total quantity
            'smart_quantity',               # Smart quantity
            'total_buying_price_excl_tax_perf',  # Total buying price excl tax perf
            'total_buying_price_incl_tax', # Total buying price incl tax
            'total_buying_price_excl_tax', # Total buying price excl tax
            # Champs commande
            'order_reference',              # Réf. Commande (extrait de order)
            'order_external_reference',     # Réf. externe (extrait de order)
            'order_status',                 # Statut Commande
            # Champs supplémentaires
            'delivery_date',                # Date de livraison (alias)
            'reception_date',               # Date de réception (alias)
            'created_by',                   # Créée par
            'validated_by',                 # Validée par
            # Champs shop (aplatis)
            'shop_id',
            'shop_name',
            'shop_reference',
            'shop_email',
            'shop_url',
            'shop_is_warehouse',
            'shop_gps',
            # Champs supplier (aplatis)
            'supplier_id',
            'supplier_name',
            'supplier_code',
            'supplier_email',
            'supplier_url',
            'supplier_delivery_time_days',
            # Champs supplémentaires de la doc
            'is_order_finalized',          # Is order finalized
            'has_production_batch',         # Has production batch
            'pda_uri',                      # Pda uri
            'training',                     # Training
            'origin_delivery'              # Réception d'origine
        ]
        
        for item in data:
            if isinstance(item, dict):
                # Ajouter les champs directs
                all_fields.update(item.keys())
                
                # Aplatir les objets imbriqués pour détecter tous les champs possibles
                flattened = self._flatten_nested_object(item, max_depth=2)
                flattened_fields.update(flattened.keys())
        
        # Combiner les champs directs et aplatis, en éliminant les doublons
        # Priorité aux champs directs (si un champ existe à la fois en direct et en aplati, on garde le direct)
        combined_fields = sorted(list(all_fields | flattened_fields))
        
        # Ajouter les champs importants s'ils ne sont pas déjà présents
        for important_field in important_fields_always:
            if important_field not in combined_fields:
                combined_fields.append(important_field)
        
        # Vérifier et supprimer les doublons explicites
        seen = set()
        unique_fields = []
        for field in combined_fields:
            if field not in seen:
                seen.add(field)
                unique_fields.append(field)
        
        return unique_fields

def export_to_csv(self, data, shop_code, shop_name):
        """Exporte les données vers un fichier CSV avec formatage amélioré"""
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
        filename = f'export_reception_{shop_code}_{timestamp}.csv'
        local_filepath = os.path.join(self.base_dir, filename)
        
        # Détecter tous les champs disponibles (y compris les champs aplatis)
        api_fields = self._get_all_fields_from_data(data)
        
        # S'assurer qu'il n'y a pas de doublons dans les fieldnames
        fieldnames_set = set(api_fields)
        if len(fieldnames_set) != len(api_fields):
            logger.warning(f"⚠️ Doublons détectés dans les champs API: {len(api_fields)} champs, {len(fieldnames_set)} uniques")
            api_fields = sorted(list(fieldnames_set))
        
        logger.info(f"📋 Champs détectés dans l'API: {len(api_fields)} champs uniques")
        logger.info(f"   Champs: {', '.join(api_fields[:15])}{'...' if len(api_fields) > 15 else ''}")
        
        # Construire la liste des en-têtes: d'abord les champs API, puis shop_code et shop_name
        # Vérifier que shop_code et shop_name ne sont pas déjà dans api_fields
        final_fieldnames = api_fields.copy()
        if 'shop_code' not in final_fieldnames:
            final_fieldnames.append('shop_code')
        if 'shop_name' not in final_fieldnames:
            final_fieldnames.append('shop_name')
        
        fieldnames = final_fieldnames
        
        try:
            # Créer le fichier CSV local
            with open(local_filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
                writer.writeheader()
                
                for item in data:
                    row = {}
                    
                    # Aplatir l'item pour extraire tous les champs (y compris les objets imbriqués)
                    # Passer les clés de niveau supérieur pour éviter les doublons
                    top_level_keys = set(item.keys()) if isinstance(item, dict) else set()
                    flattened_item = self._flatten_nested_object(item, max_depth=3, top_level_keys=top_level_keys)
                    
                    # Fusionner l'item original avec l'item aplati
                    # Les champs directs ont priorité sur les champs aplatis
                    merged_item = {**flattened_item, **item}
                    
                    # Extraire manuellement les champs importants pour s'assurer qu'ils sont bien présents
                    # Numéro de bon de livraison
                    if 'delivery_number' not in merged_item:
                        merged_item['delivery_number'] = item.get('delivery_number', item.get('number', ''))
                    
                    # Extraire les informations de la commande (order)
                    order = item.get('order', {})
                    if not order or (isinstance(order, str) and not order.strip()):
                        order = {}
                    
                    # Référence commande (depuis order)
                    if 'order_reference' not in merged_item:
                        if isinstance(order, dict) and order:
                            merged_item['order_reference'] = order.get('reference', order.get('code_com', ''))
                        else:
                            merged_item['order_reference'] = ''
                    
                    # Référence externe (depuis order)
                    if 'order_external_reference' not in merged_item:
                        if isinstance(order, dict) and order:
                            merged_item['order_external_reference'] = order.get('external_reference', '')
                        else:
                            merged_item['order_external_reference'] = ''
                    
                    # Statut commande (depuis order)
                    if 'order_status' not in merged_item:
                        if isinstance(order, dict) and order:
                            merged_item['order_status'] = order.get('status_display', order.get('status', ''))
                        else:
                            # Si pas de commande, utiliser le statut de la réception elle-même
                            merged_item['order_status'] = item.get('order_status', 'Pas de commande associée')
                    
                    # Aplatir les objets shop et supplier pour éviter les JSON bruts
                    # Shop
                    shop = item.get('shop', {})
                    if isinstance(shop, dict) and shop:
                        if 'shop_id' not in merged_item:
                            merged_item['shop_id'] = shop.get('id', '')
                        if 'shop_name' not in merged_item:
                            merged_item['shop_name'] = shop.get('name', '')
                        if 'shop_reference' not in merged_item:
                            merged_item['shop_reference'] = shop.get('reference', '')
                        if 'shop_email' not in merged_item:
                            merged_item['shop_email'] = shop.get('email', '')
                        if 'shop_url' not in merged_item:
                            merged_item['shop_url'] = shop.get('url', '')
                        if 'shop_is_warehouse' not in merged_item:
                            merged_item['shop_is_warehouse'] = 'Oui' if shop.get('is_warehouse', False) else 'Non'
                        if 'shop_gps' not in merged_item:
                            merged_item['shop_gps'] = shop.get('gps', '')
                    
                    # Supplier
                    supplier = item.get('supplier', {})
                    if isinstance(supplier, dict) and supplier:
                        if 'supplier_id' not in merged_item:
                            merged_item['supplier_id'] = supplier.get('id', '')
                        if 'supplier_name' not in merged_item:
                            merged_item['supplier_name'] = supplier.get('name', '')
                        if 'supplier_code' not in merged_item:
                            merged_item['supplier_code'] = supplier.get('code', '')
                        if 'supplier_email' not in merged_item:
                            merged_item['supplier_email'] = supplier.get('email', '')
                        if 'supplier_url' not in merged_item:
                            merged_item['supplier_url'] = supplier.get('url', '')
                        if 'supplier_delivery_time_days' not in merged_item:
                            merged_item['supplier_delivery_time_days'] = supplier.get('delivery_time_days', '')
                    
                    # Date de livraison
                    if 'delivery_date' not in merged_item:
                        merged_item['delivery_date'] = item.get('delivery_date', item.get('date', ''))
                    
                    # Date de réception
                    if 'reception_date' not in merged_item:
                        merged_item['reception_date'] = item.get('created_at', item.get('date', ''))
                    
                    # Date de validation
                    if 'validation_date' not in merged_item:
                        merged_item['validation_date'] = item.get('validation_date', item.get('validated_at', ''))
                    
                    # Créée par
                    if 'created_by' not in merged_item:
                        merged_item['created_by'] = item.get('created_by', item.get('created_by_name', ''))
                    
                    # Validé par
                    if 'validated_by' not in merged_item:
                        merged_item['validated_by'] = item.get('validated_by', item.get('validated_by_name', ''))
                    
                    # Validé (Oui/Non)
                    if 'validated' not in merged_item:
                        validated = item.get('validated', item.get('is_validated', False))
                        merged_item['validated'] = 'Oui' if validated else 'Non'
                    
                    # Date (date principale de la réception) - obligatoire selon doc
                    if 'date' not in merged_item:
                        merged_item['date'] = item.get('date', item.get('delivery_date', item.get('created_at', '')))
                    
                    # Champs selon documentation API /api/delivery/
                    # name (nom affiché)
                    if 'name' not in merged_item:
                        merged_item['name'] = item.get('name', '')
                    
                    # delivery_type (1=réception, 2=retour fournisseur)
                    if 'delivery_type' not in merged_item:
                        delivery_type = item.get('delivery_type', '')
                        if delivery_type == 1:
                            merged_item['delivery_type'] = 'Réception'
                        elif delivery_type == 2:
                            merged_item['delivery_type'] = 'Retour fournisseur'
                        else:
                            merged_item['delivery_type'] = str(delivery_type) if delivery_type else ''
                    
                    # total_quantity (Total quantity)
                    if 'total_quantity' not in merged_item:
                        merged_item['total_quantity'] = item.get('total_quantity', '')
                    
                    # smart_quantity (Smart quantity)
                    if 'smart_quantity' not in merged_item:
                        merged_item['smart_quantity'] = item.get('smart_quantity', '')
                    
                    # total_buying_price_excl_tax_perf
                    if 'total_buying_price_excl_tax_perf' not in merged_item:
                        merged_item['total_buying_price_excl_tax_perf'] = item.get('total_buying_price_excl_tax_perf', '')
                    
                    # total_buying_price_incl_tax
                    if 'total_buying_price_incl_tax' not in merged_item:
                        merged_item['total_buying_price_incl_tax'] = item.get('total_buying_price_incl_tax', '')
                    
                    # total_buying_price_excl_tax
                    if 'total_buying_price_excl_tax' not in merged_item:
                        merged_item['total_buying_price_excl_tax'] = item.get('total_buying_price_excl_tax', '')
                    
                    # is_central (selon doc)
                    if 'is_central' not in merged_item:
                        is_central = item.get('is_central', False)
                        merged_item['is_central'] = 'Oui' if is_central else 'Non'
                    
                    # is_order_finalized
                    if 'is_order_finalized' not in merged_item:
                        is_finalized = item.get('is_order_finalized', False)
                        merged_item['is_order_finalized'] = 'Oui' if is_finalized else 'Non'
                    
                    # has_production_batch
                    if 'has_production_batch' not in merged_item:
                        has_batch = item.get('has_production_batch', False)
                        merged_item['has_production_batch'] = 'Oui' if has_batch else 'Non'
                    
                    # training
                    if 'training' not in merged_item:
                        training = item.get('training', False)
                        merged_item['training'] = 'Oui' if training else 'Non'
                    
                    # Ajouter tous les champs détectés
                    for field in api_fields:
                        if field in merged_item:
                            row[field] = self._flatten_value(merged_item[field])
                        else:
                            row[field] = ''
                    
                    # Ajouter les champs supplémentaires
                    row['shop_code'] = shop_code
                    row['shop_name'] = shop_name
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
        logger.info(f"EXTRACTION RECEPTION MAGASIN {shop_code}")
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
        logger.info("DÉBUT DE L'EXTRACTION API PROSUMA - RECEPTION")
        logger.info("=" * 60)
        
                # Créer le dossier réseau au début
        network_path = self.get_network_path_for_shop("RECEPTION")
        if network_path:
            logger.info(f"✅ Dossier réseau créé: {network_path}")
        else:
            logger.warning("⚠️ Impossible de créer le dossier réseau")
        
        successful_shops = 0
        total_shops = len(self.shop_codes)
        failed_shops = []  # Liste des magasins en échec avec leur nom
        
        for shop_code in self.shop_codes:
            try:
                if self.extract_shop(shop_code):
                    successful_shops += 1
                else:
                    # Extraction échouée
                    shop_name = self.shop_config.get(shop_code, {}).get('name', 'Nom inconnu')
                    failed_shops.append((shop_code, shop_name))
            except Exception as e:
                # Erreur lors de l'extraction
                shop_name = self.shop_config.get(shop_code, {}).get('name', 'Nom inconnu')
                failed_shops.append((shop_code, shop_name))
                logger.error(f"❌ Erreur lors de l'extraction du magasin {shop_code}: {e}")
        
        # Résumé
        logger.info("=" * 60)
        logger.info("📊📊📊 RÉSUMÉ FINAL DE L'EXTRACTION 📊📊📊")
        logger.info("=" * 60)
        logger.info(f"✅ Magasins traités avec succès: {successful_shops}/{total_shops}")
        logger.info(f"❌ Magasins en échec: {len(failed_shops)}/{total_shops}")
        
        # Afficher les magasins en erreur s'il y en a
        if failed_shops:
            logger.warning("=" * 60)
            logger.warning("⚠️⚠️⚠️ EXTRACTION PARTIELLEMENT RÉUSSIE ⚠️⚠️⚠️")
            logger.warning("=" * 60)
            logger.warning("")
            logger.warning("📋📋📋 LISTE DES MAGASINS EN ÉCHEC 📋📋📋")
            logger.warning("=" * 60)
            for shop_code, shop_name in failed_shops:
                logger.warning(f"   ❌ Code magasin: {shop_code} - Nom: {shop_name}")
            logger.warning("=" * 60)
            logger.warning("")
        elif successful_shops == total_shops:
            logger.info("=" * 60)
            logger.info("✅✅✅ EXTRACTION COMPLÈTEMENT RÉUSSIE ✅✅✅")
            logger.info("=" * 60)
        else:
            logger.error("=" * 60)
            logger.error("❌❌❌ AUCUNE EXTRACTION RÉUSSIE ❌❌❌")
            logger.error("=" * 60)

def main():
    """Fonction principale"""
    try:
        extractor = ProsumaAPIReceptionExtractor()
        extractor.extract_all()
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")

if __name__ == "__main__":
    main()
