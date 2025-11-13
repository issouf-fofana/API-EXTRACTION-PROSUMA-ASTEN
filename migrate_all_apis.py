#!/usr/bin/env python3
"""
Script de migration pour appliquer les corrections à tous les scripts API
"""

import os
import shutil
import glob

def migrate_api_script(api_folder, api_name):
    """Migre un script API vers la nouvelle structure"""
    script_path = os.path.join(api_folder, f"api_{api_name.lower()}.py")
    
    if not os.path.exists(script_path):
        print(f"⚠️ Script non trouvé: {script_path}")
        return False
    
    print(f"🔄 Migration de {api_name}...")
    
    # Lire le contenu actuel
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Appliquer les corrections
    new_content = content
    
    # 1. Ajouter les imports utils
    if "from utils import" not in new_content:
        import_line = "import sys\nsys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\nfrom utils import load_shop_config, build_network_path, create_network_folder"
        new_content = new_content.replace("import urllib3", f"import urllib3\n{import_line}")
    
    # 2. Remplacer la configuration des magasins
    old_config = """        # Configuration des magasins
        self.shop_codes = os.getenv('SHOP_CODES', '').split(',')
        self.shop_mapping = {}
        for mapping in os.getenv('SHOP_MAPPING', '').split(','):
            if ':' in mapping:
                code, name = mapping.split(':', 1)
                self.shop_mapping[code] = name"""
    
    new_config = """        # Configuration des magasins
        self.shop_config = load_shop_config()
        self.shop_codes = list(self.shop_config.keys())
        
        # Configuration du dossier de téléchargement
        self.network_folder_base = os.getenv('DOWNLOAD_FOLDER_BASE', '\\\\10.0.70.169\\share\\FOFANA')
        self.base_dir = os.path.dirname(os.path.abspath(__file__))"""
    
    if old_config in new_content:
        new_content = new_content.replace(old_config, new_config)
    
    # 3. Ajouter setup_logging
    if "def setup_logging(self):" not in new_content:
        setup_logging = '''
    def setup_logging(self):
        """Configure le logging avec fichier sur le réseau"""
        log_path = self.get_log_network_path()
        if log_path:
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(os.path.join(log_path, f'prosuma_api_{api_name.lower()}.log')),
                    logging.StreamHandler()
                ]
            )
        else:
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(f'prosuma_api_{api_name.lower()}.log'),
                    logging.StreamHandler()
                ]
            )
        
        global logger
        logger = logging.getLogger(__name__)'''
        
        # Insérer après __init__
        init_end = new_content.find("        logger.info(f\"Extracteur")
        if init_end != -1:
            new_content = new_content[:init_end] + setup_logging + "\n        " + new_content[init_end:]
    
    # 4. Ajouter get_log_network_path
    if "def get_log_network_path(self):" not in new_content:
        log_method = '''
    def get_log_network_path(self):
        """Retourne le chemin réseau pour les logs"""
        if not self.network_folder_base:
            return None
        # Chemin: \\\\10.0.70.169\\share\\FOFANA\\LOG
        base = self.network_folder_base.replace('/', '\\\\')
        if base.endswith('\\\\'):
            base = base[:-1]
        log_path = f"{base}\\\\LOG"
        if create_network_folder(log_path):
            return log_path
        return None'''
        
        # Insérer après get_network_path_for_shop
        network_method = new_content.find("def get_network_path_for_shop")
        if network_method != -1:
            method_end = new_content.find("\n    def ", network_method + 1)
            if method_end == -1:
                method_end = len(new_content)
            new_content = new_content[:method_end] + log_method + "\n" + new_content[method_end:]
    
    # 5. Remplacer get_network_path_for_shop
    old_network_method = """    def get_network_path_for_shop(self, shop_code):
        \"\"\"Retourne le chemin réseau pour un magasin spécifique\"\"\"
        if not self.network_folder_base:
            return None
        
        # Construire le chemin: \\\\10.0.70.169\\share\\FOFANA\\EXTRAXTION_API_ASTEN\\EXPORT_"""
    
    new_network_method = f"""    def get_network_path_for_shop(self, shop_code):
        \"\"\"Retourne le chemin réseau pour un magasin spécifique\"\"\"
        network_path = build_network_path(self.network_folder_base, "{api_name}")
        if create_network_folder(network_path):
            return network_path
        return None"""
    
    if old_network_method in new_content:
        new_content = new_content.replace(old_network_method, new_network_method)
    
    # 6. Modifier export_to_csv pour utiliser la nouvelle logique
    if "def export_to_csv(" in new_content:
        # Remplacer la logique d'export
        old_export_start = new_content.find("def export_to_csv(")
        old_export_end = new_content.find("\n    def ", old_export_start + 1)
        if old_export_end == -1:
            old_export_end = len(new_content)
        
        new_export = f'''    def export_to_csv(self, data, shop_code, shop_name):
        """Exporte les données vers un fichier CSV"""
        if not data:
            logger.warning(f"Aucune donnée à exporter pour le magasin {{shop_code}}")
            return None
        
        # Créer le dossier réseau
        network_path = self.get_network_path_for_shop(shop_code)
        if not network_path:
            logger.error(f"Impossible de créer le dossier réseau pour le magasin {{shop_code}}")
            return None
        
        # Créer un fichier temporaire local
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'export_{api_name.lower()}_{{shop_code}}_{{timestamp}}.csv'
        local_filepath = os.path.join(self.base_dir, filename)
        
        try:
            # Créer le fichier CSV local (logique spécifique à chaque API)
            # Cette méthode doit être implémentée par chaque API
            
            # Copier vers le réseau et supprimer le fichier local
            network_filepath = os.path.join(network_path, filename)
            shutil.copy2(local_filepath, network_filepath)
            logger.info(f"✅ Fichier copié sur le réseau: {{network_filepath}}")
            
            # Supprimer le fichier local
            os.remove(local_filepath)
            logger.info(f"🗑️ Fichier local supprimé")
            
            return network_filepath
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'export CSV: {{e}}")
            return None'''
        
        new_content = new_content[:old_export_start] + new_export + new_content[old_export_end:]
    
    # 7. Appeler setup_logging dans __init__
    if "self.setup_logging()" not in new_content:
        new_content = new_content.replace(
            "        self.base_dir = os.path.dirname(os.path.abspath(__file__))",
            "        self.base_dir = os.path.dirname(os.path.abspath(__file__))\n        \n        # Configuration du logging sera faite dans setup_logging()\n        self.setup_logging()"
        )
    
    # Écrire le fichier modifié
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ {api_name} migré avec succès")
    return True

def main():
    """Fonction principale de migration"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Liste des APIs à migrer
    apis = [
        ("API_PROMO", "PROMO"),
        ("API_PRODUIT_NON_TROUVE", "PRODUIT_NON_TROUVE"),
        ("API_COMMANDE_THEME", "COMMANDE_THEME"),
        ("API_RECEPTION", "RECEPTION"),
        ("API_PRE_COMMANDE", "PRE_COMMANDE"),
        ("API_RETOUR_MARCHANDISE", "RETOUR_MARCHANDISE"),
        ("API_INVENTAIRE", "INVENTAIRE"),
        ("API_STATS_VENTE", "STATS_VENTE")
    ]
    
    print("🚀 Début de la migration des scripts API...")
    print("=" * 50)
    
    for api_folder, api_name in apis:
        folder_path = os.path.join(base_dir, api_folder)
        if os.path.exists(folder_path):
            migrate_api_script(folder_path, api_name)
        else:
            print(f"⚠️ Dossier non trouvé: {folder_path}")
    
    print("=" * 50)
    print("✅ Migration terminée !")
    print("\n📋 Prochaines étapes:")
    print("1. Vérifier les scripts migrés")
    print("2. Tester chaque API individuellement")
    print("3. Copier vers le réseau")

if __name__ == "__main__":
    main()

