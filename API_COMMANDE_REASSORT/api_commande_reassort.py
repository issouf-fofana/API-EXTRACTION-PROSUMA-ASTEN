#!/usr/bin/env python3
"""
Extracteur API Prosuma RPOS - Commandes Réassort
Récupère les commandes réassort via l'API Prosuma avec pagination automatique
"""

import requests
import os
import csv
import json
import logging
import shutil
from datetime import datetime, timedelta
from dotenv import load_dotenv
import urllib3
import sys

# Ajouter le répertoire parent au path pour importer utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import load_shop_config, build_network_path, create_network_folder, SafeStreamHandler

# Désactiver les warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ProsumaAPICommandeReassortExtractor:
    def __init__(self):
        """Initialise l'extracteur avec la configuration"""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        load_dotenv(os.path.join(project_root, 'config.env'))
        
        self.username = os.getenv('PROSUMA_USER')
        self.password = os.getenv('PROSUMA_PASSWORD')
        self.status_filter = os.getenv('STATUT_COMMANDE', '')
        
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
        
        # Configuration de la session
        self.session = requests.Session()
        self.session.auth = (self.username, self.password)
        self.session.verify = False
        
        print(f"Extracteur API Commandes Réassort initialisé pour {self.username}")
        print(f"Magasins configurés: {self.shop_codes}")
        print(f"Période: {self.start_date.strftime('%Y-%m-%d')} à {self.end_date.strftime('%Y-%m-%d')}")
        if self.status_filter:
            print(f"Filtre de statut: {self.status_filter}")

    def setup_logging(self):
        """Configure le système de logging"""
        # Créer le dossier de logs sur le réseau
        log_network_path = self.get_log_network_path()
        if log_network_path:
            log_file = os.path.join(log_network_path, f'api_commande_reassort_{datetime.now().strftime("%Y%m%d")}.log')
        else:
            # Fallback local
            log_file = os.path.join(self.base_dir, f'api_commande_reassort_{datetime.now().strftime("%Y%m%d")}.log')
        
        # Configuration du logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                SafeStreamHandler()
            ]
        )
        
        global logger
        logger = logging.getLogger(__name__)

    def setup_dates(self):
        """Configure les dates d'extraction"""
        # Vérifier si des dates personnalisées sont fournies via les variables d'environnement
        start_date_str = os.getenv('DATE_START')
        end_date_str = os.getenv('DATE_END')
        
        if start_date_str and end_date_str:
            try:
                # Parser les dates
                start_date_only = datetime.strptime(start_date_str, '%Y-%m-%d')
                end_date_only = datetime.strptime(end_date_str, '%Y-%m-%d')
                
                # Ajouter les heures appropriées
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

    def get_shop_folder_name(self, shop_code):
        """Retourne le nom du dossier pour un magasin spécifique basé sur le mapping"""
        shop_info = self.shop_config.get(shop_code)
        if not shop_info:
            return None
        
        shop_name = shop_info.get('name', '')
        
        # Mapping des noms de magasins vers les noms de dossiers
        folder_mapping = {
            'HYPER CASINO PRIMA': 'PRIMA',
            'CASINO MANDARINE RIVIERA 4': 'SOL BENI',  # Le dossier reste SOL BENI mais le magasin est CASINO MANDARINE RIVIERA 4
            'MANDARINE KOUMASSI': 'CKM',  # Le dossier reste CKM mais le magasin est MANDARINE KOUMASSI
            'CASH IVOIRE U 7 DECEMBRE': 'CUV7DEC',
            'MANDARINE GOLF': 'MANDARINE GOLF',
            'CASINO ALLABRA': 'CASINO ALLABRA',
            'SUPER U VALLON': 'SUPER U VALLON',
            'CASH IVOIRE U M\'BADON': 'MBADON',
            # Ajouter d'autres mappings si nécessaire
        }
        
        # Chercher le mapping exact
        if shop_name in folder_mapping:
            return folder_mapping[shop_name]
        
        # Si pas de mapping exact, utiliser le nom du magasin tel quel
        # (pour les autres magasins qui n'ont pas encore de dossier)
        return shop_name
    
    def get_network_path_for_shop(self, shop_code):
        """Retourne le chemin réseau pour un magasin spécifique dans ASTEN"""
        try:
            # Chemin de base: \\10.0.70.169\share\FOFANA\Etats Natacha\Commande\PRESENTATION_COMMANDE\ASTEN
            base = self.network_folder_base.replace('/', '\\')
            if base.endswith('\\'):
                base = base[:-1]
            
            asten_path = f"{base}\\Etats Natacha\\Commande\\PRESENTATION_COMMANDE\\ASTEN"
            
            # Obtenir le nom du dossier pour ce magasin
            folder_name = self.get_shop_folder_name(shop_code)
            if not folder_name:
                logger.warning(f"⚠️ Impossible de déterminer le nom du dossier pour le magasin {shop_code}")
                return None
            
            # Chemin complet: ASTEN\{NOM_DOSSIER}
            network_path = os.path.join(asten_path, folder_name)
            logger.debug(f"Chemin réseau calculé pour {shop_code}: {network_path}")
            
            # Créer le dossier s'il n'existe pas
            if create_network_folder(network_path):
                # Vérifier que le dossier existe vraiment
                if os.path.exists(network_path):
                    logger.debug(f"✅ Dossier réseau vérifié: {network_path}")
                    return network_path
                else:
                    logger.warning(f"⚠️ Le dossier réseau n'existe pas après création: {network_path}")
                    return None
            else:
                logger.warning(f"⚠️ Impossible de créer le dossier réseau: {network_path}")
                return None
        except Exception as e:
            logger.error(f"❌ Erreur lors de la création du chemin réseau pour {shop_code}: {e}")
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
        """Compte le nombre total de commandes réassort disponibles"""
        try:
            url = f"{base_url}/api/supplier_order/"
            params = {
                'shop': shop_id,
                'page_size': page_size,
                'page': 1,
                'is_external': 'true',
                'date_0': self.start_date.strftime('%Y-%m-%dT00:00:00'),
                'date_1': self.end_date.strftime('%Y-%m-%dT23:59:59')
            }
            if self.status_filter and self.status_filter.lower() == 'en attente de livraison':
                params['is_awaiting_delivery'] = 'true'
            
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

    def get_orders(self, base_url, shop_id, page_size=1000):
        """Récupère les commandes réassort avec pagination complète"""
        # D'abord, compter le nombre total de commandes
        logger.info("🔍 Comptage du nombre total de commandes réassort...")
        total_records = self.count_total_records(base_url, shop_id, page_size)
        
        if total_records == 0:
            logger.warning("⚠️ Aucune commande réassort trouvée")
            return []
        
        # Afficher le cadre avec le nombre total
        logger.info("=" * 60)
        logger.info(f"📊 INFORMATIONS D'EXTRACTION - MAGASIN {shop_id}")
        logger.info("=" * 60)
        logger.info(f"📊 Total commandes réassort disponibles: {total_records:,}")
        logger.info(f"📅 Période: {self.start_date.strftime('%Y-%m-%d %H:%M:%S')} à {self.end_date.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"🏪 Magasin: {shop_id}")
        logger.info("=" * 60)
        
        try:
            url = f"{base_url}/api/supplier_order/"
            params = {
                'shop': shop_id,
                'page_size': page_size,
                'is_external': 'true',
                'date_0': self.start_date.strftime('%Y-%m-%dT00:00:00'),
                'date_1': self.end_date.strftime('%Y-%m-%dT23:59:59')
            }
            if self.status_filter and self.status_filter.lower() == 'en attente de livraison':
                params['is_awaiting_delivery'] = 'true'
                logger.info(f"Filtre API: is_awaiting_delivery=true")
            
            all_orders = []
            page = 1
            total_pages = (total_records + page_size - 1) // page_size
            
            while page <= total_pages:
                # Afficher la progression
                progress_percent = (page - 1) * 100 // total_pages if total_pages > 0 else 0
                logger.info(f"📄 Récupération page {page}/{total_pages} ({progress_percent}%) - {len(all_orders):,}/{total_records:,} commandes...")
                
                params['page'] = page
                
                response = self.session.get(url, params=params, timeout=60)
                response.raise_for_status()
                data = response.json()
                
                orders_on_page = data.get('results', [])
                all_orders.extend(orders_on_page)
                
                logger.info(f"  ✅ Page {page}: {len(orders_on_page)} commandes réassort récupérées (total: {len(all_orders):,}/{total_records:,})")
                
                # Vérifier s'il y a une page suivante
                if not data.get('next'):
                    logger.info(f"  ✅ Dernière page atteinte (page {page})")
                    break
                
                page += 1
            
            # Filtrage post-récupération si nécessaire (seulement pour les filtres autres que "en attente de livraison")
            # Le filtre "en attente de livraison" est déjà appliqué via le paramètre API is_awaiting_delivery
            if self.status_filter and self.status_filter.lower() != 'en attente de livraison':
                logger.info(f"Filtrage post-récupération pour le statut: '{self.status_filter}'")
                original_count = len(all_orders)
                all_orders = [order for order in all_orders 
                              if (order.get('status_display') or order.get('status', '')).lower() == self.status_filter.lower()]
                filtered_count = len(all_orders)
                logger.info(f"Filtrage: {original_count} -> {filtered_count} commandes")
            
            # Vérifier que le filtre "en attente de livraison" fonctionne correctement
            if self.status_filter and self.status_filter.lower() == 'en attente de livraison':
                # Vérifier que toutes les commandes sont bien en attente de livraison
                # Le filtre API devrait déjà avoir filtré, mais on vérifie quand même
                original_count = len(all_orders)
                all_orders = [order for order in all_orders 
                              if order.get('is_awaiting_delivery', False) or 
                                 (order.get('status_display', '').lower() in ['en attente de livraison', 'awaiting delivery'])]
                filtered_count = len(all_orders)
                if original_count != filtered_count:
                    logger.warning(f"⚠️ Le filtre API n'a pas fonctionné correctement. Filtrage manuel: {original_count} -> {filtered_count} commandes")
                else:
                    logger.info(f"✅ Filtre 'en attente de livraison' appliqué: {filtered_count} commandes")

            # Afficher le résumé final
            logger.info("=" * 60)
            if len(all_orders) > 0:
                logger.info(f"✅ RÉSUMÉ EXTRACTION - MAGASIN {shop_id} - SUCCÈS")
            else:
                logger.warning(f"⚠️ RÉSUMÉ EXTRACTION - MAGASIN {shop_id} - AUCUNE DONNÉE")
            logger.info("=" * 60)
            logger.info(f"📊 Commandes trouvées: {total_records:,}")
            logger.info(f"📥 Commandes extraites: {len(all_orders):,}")
            if total_records > 0:
                success_rate = (len(all_orders)/total_records*100)
                if success_rate == 100:
                    logger.info(f"📈 Taux de réussite: {success_rate:.1f}% ✅")
                elif success_rate >= 50:
                    logger.info(f"📈 Taux de réussite: {success_rate:.1f}% ⚠️")
                else:
                    logger.warning(f"📈 Taux de réussite: {success_rate:.1f}% ❌")
            else:
                logger.warning(f"📈 Taux de réussite: 0% ❌")
            logger.info("=" * 60)
            
            if len(all_orders) > 0:
                logger.info(f"✅ {len(all_orders)} commandes réassort récupérées au total")
            else:
                logger.warning(f"⚠️ Aucune commande réassort récupérée")
            return all_orders
            
        except Exception as e:
            logger.error(f"❌ ERREUR lors de la récupération des commandes réassort: {e}")
            logger.error(f"❌ EXTRACTION ÉCHOUÉE pour le magasin {shop_id}")
            return []

    def export_to_csv(self, orders, shop_code, shop_name):
        """Exporte les commandes réassort vers un fichier CSV"""
        if not orders:
            logger.warning(f"⚠️ Aucune commande réassort à exporter pour le magasin {shop_code}")
            return None
        
        # Créer le dossier local EXPORT
        local_export_dir = os.path.join(self.base_dir, 'EXPORT')
        try:
            os.makedirs(local_export_dir, exist_ok=True)
            logger.info(f"✅ Dossier local EXPORT créé/vérifié: {local_export_dir}")
        except Exception as e:
            logger.warning(f"⚠️ Impossible de créer le dossier local EXPORT: {e}")
            local_export_dir = self.base_dir  # Fallback vers le dossier de base
        
        # Créer le dossier réseau
        network_path = self.get_network_path_for_shop(shop_code)
        if not network_path:
            logger.error(f"❌ Impossible de créer le dossier réseau pour le magasin {shop_code}")
            logger.error(f"   Le fichier sera uniquement sauvegardé localement dans: {local_export_dir}")
        else:
            logger.info(f"✅ Dossier réseau trouvé/créé: {network_path}")
        
        # Créer un fichier temporaire local dans EXPORT
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'export_commande_reassort_{shop_code}_{timestamp}.csv'
        local_filepath = os.path.join(local_export_dir, filename)
        
        # En-têtes CSV exacts demandés par l'utilisateur
        fieldnames = [
            "id",
            "Magasin", 
            "Code communication",
            "Référence commande",
            "Référence commande externe",
            "Référence pré commande",
            "Configuration commande externe",
            "Date commande",
            "Date livraison",
            "Date validation",
            "Date de début de validation",
            "Date de fin de validation",
            "Statut",
            "Créée par",
            "Validée par",
            "Fournisseur",
            "Nom",
            "Prénom",
            "Titre",
            "Adresse 1",
            "Adresse 2",
            "Adresse 3",
            "Code postal",
            "Ville",
            "Pays",
            "Téléphone 1",
            "Téléphone 2",
            "Fax",
            "Email",
            "Entreprise",
            "Numéro T.V.A. intra.",
            "A.P.E.",
            "SIRET",
            "SIREN",
            "Historique"
        ]
        
        try:
            # Créer le fichier CSV local
            with open(local_filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
                writer.writeheader()
                
                for order in orders:
                    # Préparer les données pour l'export avec mapping complet
                    row = {
                        "id": order.get('id', ''),
                        "Magasin": shop_code,  # Utiliser le code du magasin
                        "Code communication": order.get('code_com', ''),
                        "Référence commande": order.get('reference', ''),
                        "Référence commande externe": order.get('external_reference', ''),
                        "Référence pré commande": order.get('pre_order_code_com', ''),
                        "Configuration commande externe": order.get('external_order_config', ''),
                        "Date commande": self.format_date(order.get('date', '')),
                        "Date livraison": self.format_date(order.get('delivery_date', '')),
                        "Date validation": self.format_date(order.get('validation_date', '')),
                        "Date de début de validation": self.format_date(order.get('start_date', '')),
                        "Date de fin de validation": self.format_date(order.get('end_date', '')),
                        "Statut": order.get('status_display', order.get('status', '')),
                        "Créée par": order.get('created_by', ''),
                        "Validée par": order.get('validated_by', ''),
                        "Fournisseur": order.get('supplier', {}).get('name', '') if isinstance(order.get('supplier'), dict) else '',
                        "Nom": order.get('last_name', ''),
                        "Prénom": order.get('first_name', ''),
                        "Titre": order.get('title', {}).get('display_name', '') if isinstance(order.get('title'), dict) else '',
                        "Adresse 1": order.get('address_1', ''),
                        "Adresse 2": order.get('address_2', ''),
                        "Adresse 3": order.get('address_3', ''),
                        "Code postal": order.get('postal_code', ''),
                        "Ville": order.get('city', ''),
                        "Pays": order.get('country', {}).get('display_name', '') if isinstance(order.get('country'), dict) else '',
                        "Téléphone 1": order.get('phone_1', ''),
                        "Téléphone 2": order.get('phone_2', ''),
                        "Fax": order.get('fax', ''),
                        "Email": order.get('email', ''),
                        "Entreprise": order.get('company_name', ''),
                        "Numéro T.V.A. intra.": order.get('vat_number', ''),
                        "A.P.E.": order.get('ape_code', ''),
                        "SIRET": order.get('siret_number', ''),
                        "SIREN": order.get('siren_number', ''),
                        "Historique": order.get('history', '')
                    }
                    writer.writerow(row)
            
            logger.info(f"✅ Fichier CSV créé localement: {local_filepath}")
            logger.info(f"   📊 {len(orders)} commandes réassort exportées")
            logger.info(f"   📋 {len(fieldnames)} colonnes par commande")
            
            # Copier vers le réseau si le chemin réseau est disponible
            if network_path:
                network_filepath = os.path.join(network_path, filename)
                try:
                    # Vérifier que le dossier réseau existe
                    if not os.path.exists(network_path):
                        logger.warning(f"⚠️ Le dossier réseau n'existe pas: {network_path}")
                        logger.info(f"   Tentative de création...")
                        if create_network_folder(network_path):
                            logger.info(f"   ✅ Dossier créé avec succès")
                        else:
                            logger.error(f"   ❌ Impossible de créer le dossier")
                            logger.info(f"📁 Fichier conservé uniquement localement: {local_filepath}")
                            return local_filepath
                    
                    # Copier le fichier
                    shutil.copy2(local_filepath, network_filepath)
                    
                    # Vérifier que la copie a réussi
                    if os.path.exists(network_filepath):
                        file_size = os.path.getsize(network_filepath)
                        logger.info(f"✅✅✅ FICHIER COPIÉ SUR LE RÉSEAU AVEC SUCCÈS ✅✅✅")
                        logger.info(f"   📁 Chemin réseau: {network_filepath}")
                        logger.info(f"   📊 Taille: {file_size:,} octets")
                    else:
                        logger.error(f"❌❌❌ LE FICHIER N'EXISTE PAS APRÈS LA COPIE ❌❌❌")
                        logger.error(f"   Chemin attendu: {network_filepath}")
                        logger.info(f"📁 Fichier conservé uniquement localement: {local_filepath}")
                        return local_filepath
                        
                except PermissionError as e:
                    logger.error(f"❌ Erreur de permission lors de la copie sur le réseau: {e}")
                    logger.info(f"📁 Fichier conservé uniquement localement: {local_filepath}")
                    return local_filepath
                except Exception as e:
                    logger.error(f"❌ Erreur lors de la copie sur le réseau: {e}")
                    logger.info(f"📁 Fichier conservé uniquement localement: {local_filepath}")
                    return local_filepath
            else:
                logger.warning(f"⚠️ Pas de chemin réseau disponible, fichier conservé uniquement localement")
                return local_filepath
            
            # Ne pas supprimer le fichier local, le garder dans EXPORT
            logger.info(f"📁 Fichier local conservé dans EXPORT: {local_filepath}")
            
            return network_filepath if network_path and os.path.exists(os.path.join(network_path, filename)) else local_filepath
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'export CSV: {e}")
            return None

    def format_date(self, date_value):
        """Formate une date pour l'affichage"""
        if not date_value:
            return ''
        
        try:
            if 'T' in str(date_value):
                # Format ISO avec heure
                dt = datetime.fromisoformat(str(date_value).replace('Z', '+00:00'))
                return dt.strftime('%d/%m/%Y %H:%M:%S')
            elif len(str(date_value)) == 10:
                # Format YYYY-MM-DD
                dt = datetime.strptime(str(date_value), '%Y-%m-%d')
                return dt.strftime('%d/%m/%Y')
            else:
                return str(date_value)
        except:
            return str(date_value)

    def extract_shop(self, shop_code):
        """Extrait les commandes réassort pour un magasin spécifique"""
        shop_info = self.shop_config.get(shop_code)
        if not shop_info:
            logger.error(f"❌ Configuration manquante pour le magasin {shop_code}")
            return False
        
        base_url = shop_info['url']
        shop_name = shop_info['name']
        
        logger.info(f"==================================================")
        logger.info(f"🚀 EXTRACTION COMMANDES RÉASSORT MAGASIN {shop_code}")
        logger.info(f"==================================================")
        logger.info(f"🌐 URL serveur: {base_url}")
        logger.info(f"🏪 Nom magasin: {shop_name}")
        
        # Test de connexion
        if not self.test_api_connection(base_url):
            logger.error(f"❌❌❌ IMPOSSIBLE DE SE CONNECTER AU SERVEUR ❌❌❌")
            logger.error(f"   Serveur: {base_url}")
            logger.error(f"   Magasin {shop_code}: ÉCHEC")
            return False
        
        # Récupérer les informations du magasin
        logger.info(f"🔍 Récupération des informations du magasin {shop_code}...")
        shop_data = self.get_shop_info(base_url, shop_code)
        if not shop_data:
            logger.error(f"❌❌❌ IMPOSSIBLE DE RÉCUPÉRER LES INFORMATIONS DU MAGASIN ❌❌❌")
            logger.error(f"   Magasin {shop_code}: ÉCHEC")
            return False
        
        shop_id = shop_data.get('id')
        if not shop_id:
            logger.error(f"❌❌❌ ID DU MAGASIN NON TROUVÉ ❌❌❌")
            logger.error(f"   Magasin {shop_code}: ÉCHEC")
            return False
        
        # Récupérer les commandes réassort
        logger.info(f"📥 Récupération des commandes réassort pour le magasin {shop_code}...")
        orders = self.get_orders(base_url, shop_id)
        
        if not orders:
            logger.warning(f"⚠️⚠️⚠️ AUCUNE COMMANDE RÉASSORT TROUVÉE ⚠️⚠️⚠️")
            logger.warning(f"   Magasin {shop_code}: Aucune donnée")
            return True
        
        logger.info(f"✅ {len(orders)} commandes réassort récupérées au total pour le magasin {shop_code}")
        
        # Exporter vers CSV
        logger.info("=" * 60)
        logger.info(f"💾 EXPORT CSV - MAGASIN {shop_code}")
        logger.info("=" * 60)
        csv_file = self.export_to_csv(orders, shop_code, shop_name)
        if csv_file:
            logger.info("=" * 60)
            logger.info(f"✅✅✅ MAGASIN {shop_code} TRAITÉ AVEC SUCCÈS ✅✅✅")
            logger.info("=" * 60)
            logger.info(f"📁 Fichier: {csv_file}")
            logger.info(f"📊 Lignes exportées: {len(orders):,}")
            logger.info("=" * 60)
            return True
        else:
            logger.error(f"❌❌❌ ERREUR LORS DE L'EXPORT ❌❌❌")
            logger.error(f"   Magasin {shop_code}: ÉCHEC")
            return False

    def extract_all(self):
        """Extrait les commandes réassort pour tous les magasins configurés"""
        logger.info("=" * 60)
        logger.info("DÉBUT DE L'EXTRACTION API PROSUMA - COMMANDES RÉASSORT")
        logger.info("=" * 60)
        
        # Créer le dossier local EXPORT
        local_export_dir = os.path.join(self.base_dir, 'EXPORT')
        try:
            os.makedirs(local_export_dir, exist_ok=True)
            logger.info(f"✅ Dossier local EXPORT créé/vérifié: {local_export_dir}")
        except Exception as e:
            logger.warning(f"⚠️ Impossible de créer le dossier local EXPORT: {e}")
        
        # Créer tous les dossiers réseau pour chaque magasin au début
        logger.info("=" * 60)
        logger.info("CRÉATION DES DOSSIERS RÉSEAU")
        logger.info("=" * 60)
        base = self.network_folder_base.replace('/', '\\')
        if base.endswith('\\'):
            base = base[:-1]
        asten_path = f"{base}\\Etats Natacha\\Commande\\PRESENTATION_COMMANDE\\ASTEN"
        
        # Créer le dossier ASTEN s'il n'existe pas
        if create_network_folder(asten_path):
            logger.info(f"✅ Dossier ASTEN créé/vérifié: {asten_path}")
        else:
            logger.warning(f"⚠️ Impossible de créer le dossier ASTEN: {asten_path}")
        
        # Créer les dossiers pour chaque magasin
        created_folders = []
        for shop_code in self.shop_codes:
            folder_name = self.get_shop_folder_name(shop_code)
            if folder_name:
                shop_folder_path = os.path.join(asten_path, folder_name)
                if create_network_folder(shop_folder_path):
                    created_folders.append(folder_name)
                    logger.info(f"✅ Dossier créé/vérifié: {folder_name}")
                else:
                    logger.warning(f"⚠️ Impossible de créer le dossier: {folder_name}")
        
        logger.info(f"✅ {len(created_folders)} dossiers créés/vérifiés sur {len(self.shop_codes)} magasins")
        logger.info("=" * 60)
        
        successful_shops = 0
        total_shops = len(self.shop_codes)
        
        for shop_code in self.shop_codes:
            try:
                logger.info(f"\n{'='*60}")
                logger.info(f"🔄 TRAITEMENT MAGASIN {shop_code}")
                logger.info(f"{'='*60}")
                
                if self.extract_shop(shop_code):
                    successful_shops += 1
                    logger.info(f"✅✅✅ MAGASIN {shop_code} TRAITÉ AVEC SUCCÈS ✅✅✅")
                else:
                    logger.error(f"❌❌❌ MAGASIN {shop_code} ÉCHEC ❌❌❌")
                    
            except Exception as e:
                logger.error(f"❌❌❌ ERREUR LORS DE L'EXTRACTION DU MAGASIN {shop_code} ❌❌❌")
                logger.error(f"   Erreur: {e}")
        
        # Résumé final
        logger.info(f"\n{'='*60}")
        logger.info("📊📊📊 RÉSUMÉ FINAL DE L'EXTRACTION 📊📊📊")
        logger.info(f"{'='*60}")
        logger.info(f"✅ Magasins traités avec succès: {successful_shops}/{total_shops}")
        logger.info(f"❌ Magasins en échec: {total_shops - successful_shops}/{total_shops}")
        
        if successful_shops == total_shops:
            logger.info("=" * 60)
            logger.info("✅✅✅ EXTRACTION COMPLÈTEMENT RÉUSSIE ✅✅✅")
            logger.info("=" * 60)
        elif successful_shops > 0:
            logger.warning("=" * 60)
            logger.warning("⚠️⚠️⚠️ EXTRACTION PARTIELLEMENT RÉUSSIE ⚠️⚠️⚠️")
            logger.warning("=" * 60)
        else:
            logger.error("=" * 60)
            logger.error("❌❌❌ AUCUNE EXTRACTION RÉUSSIE ❌❌❌")
            logger.error("=" * 60)

def main():
    """Fonction principale"""
    try:
        extractor = ProsumaAPICommandeReassortExtractor()
        extractor.extract_all()
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")

if __name__ == "__main__":
    main()
