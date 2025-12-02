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

        print(f"Extracteur API Produits Non Trouvés Prosuma initialisé pour {self.username}")
        print(f"Magasins configurés: {self.shop_codes}")
        print(f"Période: {self.start_date.strftime('%Y-%m-%d')} à {self.end_date.strftime('%Y-%m-%d')}")

    def setup_logging(self):
        """Configure le logging avec fichier sur le réseau"""
        log_path = self.get_log_network_path()
        if log_path:
            log_file = os.path.join(log_path, 'prosuma_api_produit_non_trouve.log')
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(log_file, encoding='utf-8'),
                    SafeStreamHandler()
                ]
            )
        else:
            log_file = 'prosuma_api_produit_non_trouve.log'
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
            response = self.session.get(test_url, timeout=30)
            if response.status_code == 200:
                logger.info(f"✅ Connexion API réussie: {base_url}")
                return True
            else:
                logger.error(f"❌ Erreur de connexion API {base_url}: {response.status_code} {response.reason}")
                if response.status_code == 401:
                    logger.error(f"❌ Erreur d'authentification - Vérifiez PROSUMA_USER et PROSUMA_PASSWORD dans config.env")
                return False
        except Exception as e:
            logger.error(f"❌ Erreur de connexion API {base_url}: {e}")
            return False

    def get_shop_info(self, base_url, shop_code):
        """Récupère les informations du magasin"""
        try:
            url = f"{base_url}/api/shop/"
            response = self.session.get(url, timeout=30)
            
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
            url = f"{base_url}/api/event_line/product_not_found"
            params = {
                'shop': shop_id,  # Ajouter le paramètre shop pour filtrer par magasin
                'page_size': page_size,
                'page': 1
            }
            
            # Ajouter les paramètres de date si disponibles (format ISO avec timezone)
            if hasattr(self, 'start_date') and hasattr(self, 'end_date'):
                params['date_0'] = self.start_date.strftime('%Y-%m-%dT%H:%M:%S+00:00')
                params['date_1'] = self.end_date.strftime('%Y-%m-%dT%H:%M:%S+00:00')
            
            logger.info(f"🔍 URL appelée: {url}")
            logger.info(f"🔍 Paramètres: {params}")
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                # Afficher un aperçu de la réponse pour le débogage
                logger.debug(f"📋 Structure de la réponse: {list(data.keys()) if isinstance(data, dict) else 'Liste'}")
                
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
                # Essayer sans le paramètre shop si l'erreur est 400
                if response.status_code == 400:
                    logger.info("🔄 Tentative sans le paramètre shop...")
                    params_without_shop = {k: v for k, v in params.items() if k != 'shop'}
                    response2 = self.session.get(url, params=params_without_shop, timeout=30)
                    if response2.status_code == 200:
                        data = response2.json()
                        total_count = data.get('count', 0)
                        logger.info(f"✅ Comptage réussi (sans shop): {total_count} enregistrements")
                        return total_count
                return 0
                
        except Exception as e:
            logger.error(f"❌ Erreur lors du comptage: {e}")
            return 0

    def get_event_lines(self, base_url, shop_id, page_size=1000):
        """Récupère les données avec pagination complète"""
        # D'abord, compter le nombre total d'enregistrements
        logger.info("🔍 Comptage du nombre total d'enregistrements...")
        total_records = self.count_total_records(base_url, shop_id, page_size)
        
        # Si total_records est 0, on fait quand même une requête pour vérifier s'il y a des résultats
        # (car l'API peut retourner count=0 mais avoir des résultats)
        if total_records == 0:
            logger.info("🔍 Vérification directe des résultats (count=0 mais peut-être des résultats)...")
            # Faire une requête pour voir s'il y a vraiment des résultats
            url = f"{base_url}/api/event_line/product_not_found"
            params = {
                'shop': shop_id,
                'page_size': 100,
                'page': 1
            }
            if hasattr(self, 'start_date') and hasattr(self, 'end_date'):
                params['date_0'] = self.start_date.strftime('%Y-%m-%dT%H:%M:%S+00:00')
                params['date_1'] = self.end_date.strftime('%Y-%m-%dT%H:%M:%S+00:00')
            
            try:
                response = self.session.get(url, params=params, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, dict) and 'results' in data:
                        results = data.get('results', [])
                        if len(results) > 0:
                            logger.info(f"✅ {len(results)} résultats trouvés malgré count=0 - extraction avec pagination")
                            # Estimer le total en fonction du nombre de résultats et de la page_size
                            # Si on a 100 résultats sur la première page avec page_size=100, il peut y en avoir plus
                            total_records = max(len(results), 1000)  # Estimation conservatrice
                            logger.info(f"📊 Estimation: au moins {len(results)} résultats, extraction avec pagination jusqu'à {total_records}")
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
                url = f"{base_url}/api/event_line/product_not_found"
                params = {
                    'shop': shop_id,  # Ajouter le paramètre shop pour filtrer par magasin
                    'page_size': page_size,
                    'page': page
                }
                
                # Ajouter les paramètres de date si disponibles (format ISO avec timezone)
                if hasattr(self, 'start_date') and hasattr(self, 'end_date'):
                    params['date_0'] = self.start_date.strftime('%Y-%m-%dT%H:%M:%S+00:00')
                    params['date_1'] = self.end_date.strftime('%Y-%m-%dT%H:%M:%S+00:00')
                
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

    def _flatten_value(self, value, max_length=1000):
        """Convertit une valeur complexe en chaîne pour le CSV"""
        if value is None:
            return ''
        elif isinstance(value, bool):
            return 'Oui' if value else 'Non'
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            # Nettoyer les retours à la ligne et autres caractères problématiques
            return value.replace('\n', ' ').replace('\r', ' ').strip()
        elif isinstance(value, dict):
            # Convertir le dictionnaire en JSON compact
            try:
                json_str = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
                if len(json_str) > max_length:
                    return json_str[:max_length] + '...'
                return json_str
            except:
                return str(value)
        elif isinstance(value, list):
            # Si c'est une liste de dictionnaires, simplifier
            if value and isinstance(value[0], dict):
                try:
                    # Prendre seulement les clés principales
                    simplified = []
                    for item in value[:5]:  # Limiter à 5 éléments
                        if isinstance(item, dict):
                            simplified.append({k: v for k, v in list(item.items())[:3]})
                    json_str = json.dumps(simplified, ensure_ascii=False, separators=(',', ':'))
                    if len(json_str) > max_length:
                        return json_str[:max_length] + '...'
                    return json_str
                except:
                    return str(value)
            else:
                return ', '.join(str(v) for v in value[:10])  # Limiter à 10 éléments
        else:
            return str(value)

    def _get_all_fields_from_events(self, events):
        """Détecte dynamiquement tous les champs disponibles dans les événements"""
        all_fields = set()
        
        for event in events:
            if isinstance(event, dict):
                all_fields.update(event.keys())
        
        # Trier et retourner la liste
        field_list = sorted(list(all_fields))
        
        # Ajouter shop_code et shop_name en premier
        important_fields = ['shop_code', 'shop_name']
        for field in important_fields:
            if field in field_list:
                field_list.remove(field)
        
        return important_fields + field_list

    def export_to_csv(self, events, shop_code, shop_name):
        """Exporte les événements vers un fichier CSV directement dans le dossier ASTEN"""
        if not events:
            logger.warning(f"Aucun événement à exporter pour le magasin {shop_code}")
            return None
        
        # Chemin direct vers le dossier ASTEN (racine, pas de dossier par magasin)
        asten_extraction_path = r"\\10.0.70.169\share\ASTEN\GESTION DES INCONUS MAG\MAG ASTEN\EXTRACTIONS\PRODUIT NON TROUVES"
        
        # Créer le dossier s'il n'existe pas
        if not os.path.exists(asten_extraction_path):
            try:
                os.makedirs(asten_extraction_path)
                logger.info(f"📁 Dossier ASTEN créé: {asten_extraction_path}")
            except Exception as e:
                logger.error(f"❌ Impossible de créer le dossier ASTEN: {e}")
                return None
        
        # Créer le nom du fichier
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'export_produit_non_trouve_{shop_code}_{timestamp}.csv'
        final_filepath = os.path.join(asten_extraction_path, filename)
        
        # Détecter dynamiquement tous les champs disponibles
        fieldnames = self._get_all_fields_from_events(events)
        
        logger.info(f"📋 Champs détectés dans l'API: {len(fieldnames)} champs")
        logger.info(f"   Champs: {', '.join(fieldnames[:10])}{'...' if len(fieldnames) > 10 else ''}")
        
        try:
            # Créer le fichier CSV DIRECTEMENT sur le réseau (pas de fichier local)
            with open(final_filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
                writer.writeheader()
                
                for event in events:
                    # Préparer les données pour l'export avec tous les champs détectés
                    row = {}
                    for field in fieldnames:
                        if field == 'shop_code':
                            row[field] = shop_code
                        elif field == 'shop_name':
                            row[field] = shop_name
                        else:
                            # Récupérer la valeur et la formater
                            value = event.get(field, '')
                            row[field] = self._flatten_value(value)
                    
                    writer.writerow(row)
            
            # Vérifier que le fichier a bien été créé
            if os.path.exists(final_filepath):
                file_size = os.path.getsize(final_filepath)
                logger.info(f"✅✅✅ FICHIER CRÉÉ DIRECTEMENT SUR LE RÉSEAU ASTEN ✅✅✅")
                logger.info(f"   📁 Chemin: {final_filepath}")
                logger.info(f"   📊 {len(events)} événements exportés")
                logger.info(f"   📊 Taille: {file_size:,} octets")
                logger.info(f"   📋 {len(fieldnames)} colonnes par événement")
                return final_filepath
            else:
                logger.error(f"❌ Le fichier n'existe pas après création: {final_filepath}")
                return None
            
        except PermissionError as e:
            logger.error(f"❌ Erreur de permission lors de l'écriture: {e}")
            logger.error(f"   Vérifiez les permissions du partage réseau")
            return None
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'export CSV: {e}")
            logger.error(f"   Type: {type(e).__name__}")
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
        
        # Récupérer les événements
        logger.info(f"Récupération des événements pour le magasin {shop_code}...")
        events = self.get_event_lines(base_url, shop_id)
        
        if not events:
            logger.info(f"ℹ️ Aucun événement de produit non trouvé pour le magasin {shop_code} pour la période sélectionnée")
            logger.info(f"   (C'est normal s'il n'y a pas eu de produits non trouvés ce jour-là)")
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
        
        # Vérifier que le dossier ASTEN existe
        asten_extraction_path = r"\\10.0.70.169\share\ASTEN\GESTION DES INCONUS MAG\MAG ASTEN\EXTRACTIONS\PRODUIT NON TROUVES"
        if not os.path.exists(asten_extraction_path):
            try:
                os.makedirs(asten_extraction_path)
                logger.info(f"✅ Dossier ASTEN créé: {asten_extraction_path}")
            except Exception as e:
                logger.warning(f"⚠️ Impossible de créer le dossier ASTEN: {e}")
        else:
            logger.info(f"✅ Dossier ASTEN vérifié: {asten_extraction_path}")
        
        successful_shops = 0
        total_shops = len(self.shop_codes)
        failed_shops = []  # Liste des magasins en échec avec leur nom
        
        for shop_code in self.shop_codes:
            try:
                shop_info = self.shop_config.get(shop_code, {})
                shop_name = shop_info.get('name', 'Nom inconnu')
                
                if self.extract_shop(shop_code):
                    successful_shops += 1
                else:
                    # Extraction échouée (connexion, authentification, etc.)
                    failed_shops.append((shop_code, shop_name))
            except Exception as e:
                # Erreur lors de l'extraction
                shop_info = self.shop_config.get(shop_code, {})
                shop_name = shop_info.get('name', 'Nom inconnu')
                failed_shops.append((shop_code, shop_name))
                logger.error(f"❌ Erreur lors de l'extraction du magasin {shop_code}: {e}")
        
        # Résumé
        logger.info("=" * 60)
        logger.info("RÉSUMÉ DE L'EXTRACTION")
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
        extractor = ProsumaAPIProduitNonTrouveExtractor()
        extractor.extract_all()
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")

if __name__ == "__main__":
    main()