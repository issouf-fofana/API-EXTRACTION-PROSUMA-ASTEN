#!/usr/bin/env python3
"""
Extracteur API Prosuma RPOS - Mouvements de Stock
Récupère les mouvements de stock via l'API stock_move
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
from utils import load_shop_config, build_network_path, create_network_folder, SafeStreamHandler, set_log_file_permissions

# Désactiver les warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Mapping des types de mouvements de stock
STOCK_MOVE_TYPES = {
    0: 'Défaut',
    3: 'Déstockage',
    5: 'Annulation',
    6: 'Dégustation gratuite',
    7: 'Dégustation payante',
    8: 'Cadeau client',
    9: 'Remplacement article défectueux',
    10: 'Casse',
    11: 'Article abîmé',
    12: 'Article volé',
    13: 'Casse livraison',
    14: 'Démonstration',
    16: 'Retour entrepôt',
    17: 'S.A.V.',
    21: 'Régularisation',
    25: 'Frais généraux',
    26: 'Inventaire manuel',
    27: 'Arrivage manuel',
    28: 'Cession inter-rayon'
}

class ProsumaAPIMouvementStockExtractor:
    def __init__(self):
        """Initialise l'extracteur avec la configuration"""
        # Déterminer le chemin racine du projet
        current_file = os.path.abspath(__file__)
        project_root = os.path.dirname(os.path.dirname(current_file))
        
        # Essayer de charger le fichier config.env depuis la racine du projet
        config_path = os.path.join(project_root, 'config.env')
        
        # Vérifier si le fichier existe
        if not os.path.exists(config_path):
            # Essayer aussi depuis le répertoire courant du script
            script_dir = os.path.dirname(current_file)
            local_config = os.path.join(script_dir, 'config.env')
            if os.path.exists(local_config):
                config_path = local_config
            else:
                raise FileNotFoundError(
                    f"Fichier config.env introuvable. Cherché dans:\n"
                    f"  - {config_path}\n"
                    f"  - {local_config}\n"
                    f"Veuillez créer le fichier config.env à la racine du projet."
                )
        
        # Charger les variables d'environnement
        load_dotenv(config_path)
        print(f"📁 Fichier config.env chargé depuis: {config_path}")
        
        self.username = os.getenv('PROSUMA_USER')
        self.password = os.getenv('PROSUMA_PASSWORD')
        
        if not self.username or not self.password:
            raise ValueError(
                f"PROSUMA_USER et PROSUMA_PASSWORD doivent être configurés dans config.env\n"
                f"Fichier utilisé: {config_path}\n"
                f"PROSUMA_USER trouvé: {'Oui' if self.username else 'Non'}\n"
                f"PROSUMA_PASSWORD trouvé: {'Oui' if self.password else 'Non'}"
            )
        
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

        print(f"Extracteur API Mouvements de Stock Prosuma initialisé pour {self.username}")
        print(f"Magasins configurés: {self.shop_codes}")
        print(f"Période: {self.start_date.strftime('%Y-%m-%d')} à {self.end_date.strftime('%Y-%m-%d')}")

    def setup_logging(self):
        """Configure le logging avec fichier sur le réseau"""
        log_path = self.get_log_network_path()
        if log_path:
            log_file = os.path.join(log_path, 'prosuma_api_mouvement_stock.log')
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(log_file, encoding='utf-8'),
                    SafeStreamHandler()
                ]
            )
            # Définir les permissions du fichier de log
            set_log_file_permissions(log_file)
        else:
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[SafeStreamHandler()]
            )

    def setup_dates(self):
        """Configure les dates de début et fin pour l'extraction"""
        # Récupérer les variables d'environnement pour les dates
        use_default = os.getenv('USE_DEFAULT_DATES', 'true').lower() == 'true'
        custom_start = os.getenv('CUSTOM_START_DATE')
        custom_end = os.getenv('CUSTOM_END_DATE')
        
        if not use_default and custom_start and custom_end:
            # Utiliser les dates personnalisées fournies
            self.start_date = datetime.strptime(custom_start, '%Y-%m-%d')
            self.end_date = datetime.strptime(custom_end, '%Y-%m-%d')
            print(f"Dates personnalisées: {custom_start} à {custom_end}")
        else:
            # Par défaut: hier à aujourd'hui
            today = datetime.now()
            yesterday = today - timedelta(days=1)
            self.start_date = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
            self.end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    def get_log_network_path(self):
        """Retourne le chemin du dossier de logs sur le réseau"""
        try:
            network_path = build_network_path(self.network_folder_base, 'MOUVEMENT_STOCK')
            log_path = os.path.join(network_path, 'LOG')
            create_network_folder(log_path)
            return log_path
        except Exception as e:
            print(f"⚠️ Impossible de créer le dossier de logs: {e}")
            return None
    
    def get_network_path_for_shop(self, shop_code):
        """Retourne le chemin du dossier réseau pour un magasin"""
        try:
            network_path = build_network_path(self.network_folder_base, 'MOUVEMENT_STOCK')
            create_network_folder(network_path)
            return network_path
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"❌ Erreur lors de la création du dossier réseau: {e}")
            return None
    
    def test_api_connection(self, base_url):
        """Teste la connexion à l'API"""
        try:
            response = self.session.get(f"{base_url}/api/user/", timeout=30)
            if response.status_code == 401:
                logger = logging.getLogger(__name__)
                logger.error(f"❌ Erreur de connexion API {base_url}: 401 Unauthorized")
                logger.error(f"❌ Erreur d'authentification - Vérifiez PROSUMA_USER et PROSUMA_PASSWORD dans config.env")
                return False
            response.raise_for_status()
            logger = logging.getLogger(__name__)
            logger.info(f"✅ Connexion API réussie: {base_url}")
            return True
        except requests.exceptions.RequestException as e:
            logger = logging.getLogger(__name__)
            logger.error(f"❌ Erreur de connexion API {base_url}: {e}")
            return False
    
    def get_shop_info(self, base_url, shop_code):
        """Récupère les informations d'un magasin"""
        try:
            response = self.session.get(
                f"{base_url}/api/shop/",
                params={'reference': shop_code},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('results'):
                shop = data['results'][0]
                logger = logging.getLogger(__name__)
                logger.info(f"✅ Magasin {shop_code} trouvé: {shop.get('name', 'N/A')}")
                return shop
            return None
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"❌ Erreur lors de la récupération du magasin: {e}")
            return None
    
    def _flatten_value(self, value, max_length=1000):
        """Convertit une valeur en chaîne formatée pour le CSV"""
        if value is None or value == '':
            return ''
        elif isinstance(value, bool):
            return 'Oui' if value else 'Non'
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            # Nettoyer et limiter la longueur
            cleaned = value.strip().replace('\n', ' ').replace('\r', ' ')
            return cleaned[:max_length] if len(cleaned) > max_length else cleaned
        elif isinstance(value, dict):
            # Pour les dictionnaires, retourner une version compacte
            try:
                return json.dumps(value, ensure_ascii=False)[:max_length]
            except:
                return str(value)[:max_length]
        elif isinstance(value, list):
            # Pour les listes, retourner une version compacte
            if len(value) == 0:
                return ''
            try:
                return json.dumps(value, ensure_ascii=False)[:max_length]
            except:
                return str(value)[:max_length]
        else:
            return str(value)[:max_length]
    
    def _get_all_fields_from_stock_moves(self, stock_moves):
        """Détecte dynamiquement tous les champs présents dans les mouvements de stock
        
        Args:
            stock_moves: Liste des mouvements de stock
            
        Returns:
            Liste des noms de champs uniques
        """
        all_fields = set()
        
        # Toujours inclure les champs importants en premier
        important_fields_always = [
            'shop_code', 'shop_name', 'date', 'id', 'quantity',
            'previous_quantity', 'last_quantity',
            'product_id', 'product_ean', 'product_label_1',
            'product_selling_price', 'product_buying_price',
            'stock_move_type', 'stock_move_type_label',
            'comment', 'name',
            'created_at', 'updated_at', 'deleted_at'
        ]
        
        for field in important_fields_always:
            all_fields.add(field)
        
        # Parcourir tous les mouvements pour détecter les champs
        for move in stock_moves:
            for key in move.keys():
                # Ignorer les champs trop complexes ou les relations FK
                if key not in ['extras'] and not key.endswith('_id'):
                    all_fields.add(key)
        
        # Convertir en liste triée
        fields_list = sorted(list(all_fields))
        
        # S'assurer que les champs importants sont en premier
        ordered_fields = []
        for field in important_fields_always:
            if field in fields_list:
                ordered_fields.append(field)
                fields_list.remove(field)
        
        # Ajouter le reste des champs
        ordered_fields.extend(fields_list)
        
        return ordered_fields
    
    def count_total_records(self, base_url, shop_id, page_size=1000):
        """Compte le nombre total d'enregistrements disponibles"""
        try:
            url = f"{base_url}/api/stock_move/"
            params = {
                'shop': shop_id,
                'page_size': page_size,
                'page': 1
            }
            
            # Ajouter les paramètres de date si disponibles (utiliser date_0 et date_1)
            # S'assurer que date_0 commence à 00:00:00 et date_1 finit à 23:59:59
            if hasattr(self, 'start_date') and hasattr(self, 'end_date'):
                # Créer une copie des dates pour ajuster les heures
                start_with_time = self.start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_with_time = self.end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                params['date_0'] = start_with_time.strftime('%Y-%m-%dT%H:%M:%S')
                params['date_1'] = end_with_time.strftime('%Y-%m-%dT%H:%M:%S')
            
            logger = logging.getLogger(__name__)
            logger.info(f"🔍 URL appelée: {url}")
            logger.info(f"🔍 Paramètres: {params}")
            
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, dict) and 'results' in data:
                    # Si c'est une réponse paginée
                    results_count = len(data.get('results', []))
                    total_count = data.get('count', 0)
                    
                    # Si count est 0 mais qu'il y a des résultats, utiliser le nombre de résultats
                    if total_count == 0 and results_count > 0:
                        logger.warning(f"⚠️ L'API retourne count=0 mais {results_count} résultats - utilisation du nombre de résultats")
                        total_count = results_count
                    
                    logger.info(f"✅ Comptage réussi: {total_count} enregistrements (page 1: {results_count} résultats)")
                    return total_count
                elif isinstance(data, list):
                    # Si c'est directement une liste
                    total_count = len(data)
                    logger.info(f"✅ Comptage réussi: {total_count} enregistrements (liste directe)")
                    return total_count
                else:
                    total_count = data.get('count', 0)
                    logger.info(f"✅ Comptage réussi: {total_count} enregistrements")
                    return total_count
            else:
                logger.error(f"❌ Erreur lors du comptage: {response.status_code}")
                logger.error(f"❌ Réponse: {response.text[:500]}")
                return 0
                
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"❌ Erreur lors du comptage: {e}")
            return 0

    def get_stock_moves(self, base_url, shop_id, page_size=1000):
        """Récupère les données avec pagination complète"""
        logger = logging.getLogger(__name__)
        
        # D'abord, compter le nombre total d'enregistrements
        logger.info("🔍 Comptage du nombre total d'enregistrements...")
        total_records = self.count_total_records(base_url, shop_id, page_size)
        
        # Si total_records est 0, vérifier quand même s'il y a des résultats
        if total_records == 0:
            logger.info("🔍 Vérification directe des résultats (count=0 mais peut-être des résultats)...")
            url = f"{base_url}/api/stock_move/"
            params = {
                'shop': shop_id,
                'page_size': 100,
                'page': 1
            }
            if hasattr(self, 'start_date') and hasattr(self, 'end_date'):
                # Créer une copie des dates pour ajuster les heures
                start_with_time = self.start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_with_time = self.end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                params['date_0'] = start_with_time.strftime('%Y-%m-%dT%H:%M:%S')
                params['date_1'] = end_with_time.strftime('%Y-%m-%dT%H:%M:%S')
            
            try:
                response = self.session.get(url, params=params, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, dict) and 'results' in data:
                        results = data.get('results', [])
                        if len(results) > 0:
                            logger.info(f"✅ {len(results)} résultats trouvés malgré count=0 - extraction avec pagination")
                            total_records = max(len(results) * 10, 1000)  # Estimation pour pagination
                            logger.info(f"📊 Estimation pour pagination: {total_records} enregistrements maximum")
                        else:
                            logger.warning("⚠️ Aucun enregistrement trouvé")
                            return []
                    elif isinstance(data, list) and len(data) > 0:
                        logger.info(f"✅ {len(data)} résultats trouvés (liste directe) - extraction des données")
                        total_records = len(data)
                    else:
                        logger.warning("⚠️ Aucun enregistrement trouvé")
                        return []
                else:
                    logger.warning("⚠️ Aucun enregistrement trouvé")
                    return []
            except Exception as e:
                logger.error(f"❌ Erreur lors de la vérification: {e}")
                import traceback
                logger.error(f"❌ Traceback: {traceback.format_exc()}")
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
                url = f"{base_url}/api/stock_move/"
                params = {
                    'shop': shop_id,
                    'page_size': page_size,
                    'page': page
                }
                
                # Ajouter les paramètres de date si disponibles
                # S'assurer que date_0 commence à 00:00:00 et date_1 finit à 23:59:59
                if hasattr(self, 'start_date') and hasattr(self, 'end_date'):
                    start_with_time = self.start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                    end_with_time = self.end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                    params['date_0'] = start_with_time.strftime('%Y-%m-%dT%H:%M:%S')
                    params['date_1'] = end_with_time.strftime('%Y-%m-%dT%H:%M:%S')
                
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
                    
                    # Si on est à la dernière page calculée, on arrête
                    if page >= total_pages:
                        logger.info(f"  ✅ Dernière page calculée atteinte (page {page}/{total_pages})")
                        # Si on a une estimation (total_records > 1000), continuer jusqu'à ce qu'on n'ait plus de résultats
                        if total_records > 1000 and len(items) > 0:
                            logger.info(f"  🔄 Continuation de la pagination (estimation)...")
                            page += 1
                            continue
                        break
                    
                    # Continuer avec la page suivante
                    page += 1
                else:
                    logger.error(f"❌ Erreur lors de la récupération des données: {response.status_code}")
                    logger.error(f"❌ URL: {url}")
                    logger.error(f"❌ Paramètres: {params}")
                    logger.error(f"❌ Réponse: {response.text[:500]}")
                    # Continuer avec la page suivante en cas d'erreur temporaire
                    if response.status_code == 500 or response.status_code == 503:
                        logger.warning(f"⚠️ Erreur serveur, tentative de continuer...")
                        page += 1
                        continue
                    break
                    
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des données: {e}")
            import traceback
            logger.error(f"❌ Traceback complet:\n{traceback.format_exc()}")
        
        # Afficher le résumé final
        logger.info("=" * 60)
        logger.info(f"✅ RÉSUMÉ EXTRACTION - MAGASIN {shop_id}")
        logger.info("=" * 60)
        logger.info(f"📊 Enregistrements trouvés: {total_records:,}")
        logger.info(f"📥 Enregistrements extraits: {len(all_data):,}")
        logger.info(f"📈 Taux de réussite: {(len(all_data)/total_records*100):.1f}%" if total_records > 0 else "📈 Taux de réussite: 0%")
        logger.info("=" * 60)
        
        return all_data
    
    def export_to_csv(self, stock_moves, shop_code, shop_name):
        """Exporte les mouvements de stock vers un fichier CSV"""
        logger = logging.getLogger(__name__)
        
        if not stock_moves:
            logger.warning(f"Aucun mouvement à exporter pour le magasin {shop_code}")
            return None
        
        # Créer le dossier réseau
        network_path = self.get_network_path_for_shop(shop_code)
        if not network_path:
            logger.error(f"Impossible de créer le dossier réseau pour le magasin {shop_code}")
            return None
        
        # Créer un fichier temporaire local
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{shop_code}_{timestamp}_Mouvements de stocks.csv'
        local_filepath = os.path.join(self.base_dir, filename)
        
        # Détecter dynamiquement tous les champs disponibles
        fieldnames = self._get_all_fields_from_stock_moves(stock_moves)
        
        logger.info(f"📋 Champs détectés dans l'API: {len(fieldnames)} champs")
        logger.info(f"   Champs: {', '.join(fieldnames[:10])}{'...' if len(fieldnames) > 10 else ''}")
        
        try:
            # Créer le fichier CSV local
            with open(local_filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
                writer.writeheader()
                
                for move in stock_moves:
                    # Préparer les données pour l'export avec tous les champs détectés
                    row = {}
                    for field in fieldnames:
                        if field == 'shop_code':
                            row[field] = shop_code
                        elif field == 'shop_name':
                            row[field] = shop_name
                        elif field == 'stock_move_type_label':
                            # Ajouter le libellé du type de mouvement
                            move_type = move.get('stock_move_type', 0)
                            row[field] = STOCK_MOVE_TYPES.get(move_type, f'Type {move_type}')
                        else:
                            # Récupérer la valeur et la formater
                            value = move.get(field, '')
                            row[field] = self._flatten_value(value)
                    
                    writer.writerow(row)
            
            logger.info(f"✅ Fichier CSV créé localement: {local_filepath}")
            logger.info(f"   {len(stock_moves)} mouvements exportés")
            logger.info(f"   {len(fieldnames)} colonnes par mouvement")
            
            # Copier vers le réseau et supprimer le fichier local
            network_filepath = os.path.join(network_path, filename)
            shutil.copy2(local_filepath, network_filepath)
            logger.info(f"✅ Fichier copié sur le réseau: {network_filepath}")
            
            # Copier également vers le dossier ASTEN si le magasin est dans le mapping
            self.copy_to_asten_folder(local_filepath, filename, shop_code)
            
            # Supprimer le fichier local
            os.remove(local_filepath)
            logger.info(f"🗑️ Fichier local supprimé")
            
            return network_filepath
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'export CSV: {e}")
            return None
    
    def get_asten_folder_name(self, shop_code, shop_name):
        """Détermine le nom du dossier ASTEN pour un magasin
        
        Cherche d'abord un dossier existant qui correspond au magasin.
        Si aucun dossier n'existe, retourne un nom généré à partir du nom du magasin.
        
        Args:
            shop_code: Code du magasin
            shop_name: Nom du magasin
            
        Returns:
            Nom du dossier ASTEN ou None si aucun dossier trouvé/créable
        """
        logger = logging.getLogger(__name__)
        
        try:
            asten_base_path = r"\\10.0.70.169\share\ASTEN\GESTION DES INCONUS MAG\MAG ASTEN"
            
            # Vérifier si le dossier ASTEN existe
            if not os.path.exists(asten_base_path):
                logger.warning(f"⚠️ Dossier ASTEN introuvable: {asten_base_path}")
                return None
            
            # Lister les dossiers existants dans ASTEN
            existing_folders = []
            try:
                existing_folders = [f for f in os.listdir(asten_base_path) 
                                  if os.path.isdir(os.path.join(asten_base_path, f))]
            except Exception as e:
                logger.warning(f"⚠️ Impossible de lister les dossiers ASTEN: {e}")
            
            # Nettoyer le nom du magasin pour la recherche
            shop_name_clean = shop_name.upper().strip()
            
            # Créer des variantes de recherche
            search_terms = []
            
            # Variante 1: Nom complet
            search_terms.append(shop_name_clean)
            
            # Variante 2: Mots clés principaux
            # Ex: "SUPER U VALLON" -> ["SUPER", "U", "VALLON"]
            words = shop_name_clean.split()
            search_terms.extend(words)
            
            # Variante 3: Derniers mots (souvent le lieu)
            if len(words) >= 2:
                search_terms.append(' '.join(words[-2:]))
            if len(words) >= 1:
                search_terms.append(words[-1])
            
            # Variante 4: Premiers mots (souvent la marque)
            if len(words) >= 2:
                search_terms.append(' '.join(words[:2]))
            
            # Chercher un dossier existant qui correspond
            for folder in existing_folders:
                folder_upper = folder.upper()
                
                # Correspondance exacte
                if folder_upper == shop_name_clean:
                    logger.info(f"📁 Dossier ASTEN trouvé (exact): {folder}")
                    return folder
                
                # Correspondance partielle (le nom du dossier contient un terme de recherche)
                for term in search_terms:
                    if len(term) >= 3 and term in folder_upper:
                        logger.info(f"📁 Dossier ASTEN trouvé (partiel): {folder} (recherche: {term})")
                        return folder
                
                # Correspondance inverse (un terme de recherche contient le nom du dossier)
                for term in search_terms:
                    if len(folder_upper) >= 3 and folder_upper in term:
                        logger.info(f"📁 Dossier ASTEN trouvé (inverse): {folder} (recherche: {term})")
                        return folder
            
            # Aucun dossier existant trouvé, générer un nom
            # Utiliser le nom du magasin en supprimant les caractères problématiques
            generated_name = shop_name_clean
            
            # Remplacer les caractères invalides pour un nom de dossier Windows
            invalid_chars = '<>:"/\\|?*'
            for char in invalid_chars:
                generated_name = generated_name.replace(char, '')
            
            # Limiter la longueur (Windows a une limite de 255 caractères)
            if len(generated_name) > 50:
                # Garder les mots importants (premiers et derniers)
                words = generated_name.split()
                if len(words) > 2:
                    generated_name = f"{words[0]} {words[-1]}"
                else:
                    generated_name = generated_name[:50]
            
            logger.info(f"📁 Aucun dossier ASTEN existant trouvé, création avec nom: {generated_name}")
            return generated_name
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la détermination du dossier ASTEN: {e}")
            return None
    
    def copy_to_asten_folder(self, local_filepath, filename, shop_code):
        """Copie le fichier vers le dossier ASTEN correspondant au magasin
        
        Args:
            local_filepath: Chemin du fichier local à copier
            filename: Nom du fichier
            shop_code: Code du magasin
        """
        logger = logging.getLogger(__name__)
        
        try:
            # Récupérer le nom du magasin depuis la config
            shop_info = self.shop_config.get(shop_code)
            if not shop_info:
                logger.warning(f"⚠️ Informations du magasin {shop_code} introuvables dans la config")
                return
            
            shop_name = shop_info.get('name', f'MAGASIN_{shop_code}')
            
            # Déterminer le nom du dossier ASTEN
            asten_folder_name = self.get_asten_folder_name(shop_code, shop_name)
            
            if not asten_folder_name:
                logger.warning(f"⚠️ Impossible de déterminer le dossier ASTEN pour {shop_code} - copie ignorée")
                return
            
            # Construire le chemin vers le dossier ASTEN
            asten_base_path = r"\\10.0.70.169\share\ASTEN\GESTION DES INCONUS MAG\MAG ASTEN"
            asten_shop_path = os.path.join(asten_base_path, asten_folder_name)
            asten_mouv_stock_path = os.path.join(asten_shop_path, "MOUV STOCK")
            
            # Créer les dossiers s'ils n'existent pas
            if not os.path.exists(asten_shop_path):
                os.makedirs(asten_shop_path)
                logger.info(f"📁 Dossier magasin créé: {asten_shop_path}")
            
            if not os.path.exists(asten_mouv_stock_path):
                os.makedirs(asten_mouv_stock_path)
                logger.info(f"📁 Dossier 'MOUV STOCK' créé: {asten_mouv_stock_path}")
            
            # Copier le fichier vers ASTEN
            asten_filepath = os.path.join(asten_mouv_stock_path, filename)
            shutil.copy2(local_filepath, asten_filepath)
            logger.info(f"✅ Fichier copié vers ASTEN: {asten_filepath}")
            
        except Exception as e:
            logger.warning(f"⚠️ Erreur lors de la copie vers ASTEN: {e}")
            logger.warning(f"⚠️ Le fichier principal a été créé avec succès, seule la copie ASTEN a échoué")

    def extract_shop(self, shop_code):
        """Extrait les mouvements de stock pour un magasin spécifique"""
        logger = logging.getLogger(__name__)
        
        shop_info = self.shop_config.get(shop_code)
        if not shop_info:
            logger.error(f"Configuration manquante pour le magasin {shop_code}")
            return False
        
        base_url = shop_info['url']
        shop_name = shop_info['name']
        
        logger.info(f"==================================================")
        logger.info(f"EXTRACTION MOUVEMENTS DE STOCK MAGASIN {shop_code}")
        logger.info(f"==================================================")
        logger.info(f"URL serveur: {base_url}")
        logger.info(f"Nom magasin: {shop_name}")
        
        # Test de connexion
        if not self.test_api_connection(base_url):
            logger.error(f"❌ Impossible de se connecter au serveur {base_url}")
            logger.warning(f"⚠️ Le magasin {shop_code} ({shop_name}) sera ignoré et le script continuera avec les autres magasins")
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
        
        # Récupérer les mouvements de stock
        logger.info(f"Récupération des mouvements de stock pour le magasin {shop_code}...")
        stock_moves = self.get_stock_moves(base_url, shop_id)
        
        if not stock_moves:
            logger.info(f"ℹ️ Aucun mouvement de stock pour le magasin {shop_code} pour la période sélectionnée")
            logger.info(f"   (C'est normal s'il n'y a pas eu de mouvements ce jour-là)")
            return True
        
        # Exporter vers CSV
        logger.info("=" * 60)
        logger.info(f"💾 EXPORT CSV - MAGASIN {shop_code}")
        logger.info("=" * 60)
        csv_file = self.export_to_csv(stock_moves, shop_code, shop_name)
        if csv_file:
            logger.info("=" * 60)
            logger.info(f"✅ MAGASIN {shop_code} TRAITÉ AVEC SUCCÈS")
            logger.info("=" * 60)
            logger.info(f"📁 Fichier sur le réseau: {csv_file}")
            logger.info(f"📊 Lignes exportées: {len(stock_moves):,}")
            logger.info("=" * 60)
            return True
        else:
            logger.error(f"❌ Erreur lors de l'export pour le magasin {shop_code}")
            return False

    def extract_all(self):
        """Extrait les mouvements de stock pour tous les magasins configurés"""
        logger = logging.getLogger(__name__)
        
        logger.info("=" * 60)
        logger.info("DÉBUT DE L'EXTRACTION API PROSUMA - MOUVEMENTS DE STOCK")
        logger.info("=" * 60)
        
        # Créer le dossier réseau au début
        network_path = self.get_network_path_for_shop("MOUVEMENT_STOCK")
        if network_path:
            logger.info(f"✅ Dossier réseau créé: {network_path}")
        else:
            logger.warning("⚠️ Impossible de créer le dossier réseau")
        
        successful_shops = 0
        failed_shops = []
        
        for shop_code in self.shop_codes:
            try:
                success = self.extract_shop(shop_code)
                if success:
                    successful_shops += 1
                else:
                    shop_name = self.shop_config.get(shop_code, {}).get('name', 'Inconnu')
                    failed_shops.append({'code': shop_code, 'name': shop_name})
            except Exception as e:
                logger.error(f"❌ Erreur inattendue lors de l'extraction du magasin {shop_code}: {e}")
                shop_name = self.shop_config.get(shop_code, {}).get('name', 'Inconnu')
                failed_shops.append({'code': shop_code, 'name': shop_name})
        
        # Résumé final
        logger.info("=" * 60)
        logger.info("RÉSUMÉ DE L'EXTRACTION")
        logger.info("=" * 60)
        logger.info(f"✅ Magasins traités avec succès: {successful_shops}/{len(self.shop_codes)}")
        logger.info(f"❌ Magasins en échec: {len(failed_shops)}/{len(self.shop_codes)}")
        
        if failed_shops:
            logger.warning("=" * 60)
            logger.warning("⚠️⚠️⚠️ EXTRACTION PARTIELLEMENT RÉUSSIE ⚠️⚠️⚠️")
            logger.warning("=" * 60)
            logger.warning("")
            logger.warning("📋📋📋 LISTE DES MAGASINS EN ÉCHEC 📋📋📋")
            logger.warning("=" * 60)
            for shop in failed_shops:
                logger.warning(f"   ❌ Code magasin: {shop['code']} - Nom: {shop['name']}")
            logger.warning("=" * 60)
            logger.warning("")
        else:
            logger.info("=" * 60)
            logger.info("🎉🎉🎉 EXTRACTION COMPLÉTÉE AVEC SUCCÈS 🎉🎉🎉")
            logger.info("=" * 60)

def main():
    """Fonction principale"""
    try:
        extractor = ProsumaAPIMouvementStockExtractor()
        extractor.extract_all()
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        return 1
    return 0

if __name__ == "__main__":
    exit(main())

