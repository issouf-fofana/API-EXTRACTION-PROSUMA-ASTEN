#!/usr/bin/env python3
"""
Utilitaires partagés pour les APIs Prosuma RPOS
"""

import os
import json
import logging
import sys
import io
import subprocess
import platform

logger = logging.getLogger(__name__)

class SafeStreamHandler(logging.StreamHandler):
    """StreamHandler qui gère les erreurs d'encodage Unicode sur Windows"""
    def __init__(self, stream=None):
        if stream is None:
            stream = sys.stdout
        super().__init__(stream)
    
    def emit(self, record):
        try:
            # Formater le message
            try:
                msg = self.format(record)
            except Exception:
                # Si le formatage échoue, utiliser un message simple
                msg = f"{record.levelname}: {record.getMessage()}"
            
            stream = self.stream
            
            # Remplacer les emojis et caractères Unicode problématiques par du texte simple
            # pour éviter les erreurs d'encodage sur Windows
            safe_msg = msg
            emoji_replacements = {
                '✅': '[OK]',
                '❌': '[ERREUR]',
                '⚠️': '[ATTENTION]',
                '🔍': '[RECHERCHE]',
                '📊': '[STATS]',
                '📅': '[DATE]',
                '🏪': '[MAGASIN]',
                '📄': '[PAGE]',
                '💾': '[EXPORT]',
                '🗑️': '[SUPPRIME]',
                '📁': '[FICHIER]',
                '📥': '[IMPORT]',
                '📈': '[Taux]',
                '🚀': '[LANCE]',
                '📋': '[LISTE]'
            }
            for emoji, replacement in emoji_replacements.items():
                safe_msg = safe_msg.replace(emoji, replacement)
            
            # Encoder le message de manière sûre
            try:
                # Encoder en ASCII avec remplacement des caractères non-ASCII
                safe_msg_encoded = safe_msg.encode('ascii', errors='replace').decode('ascii', errors='replace')
            except Exception:
                # Si l'encodage ASCII échoue, utiliser UTF-8 avec replace
                safe_msg_encoded = safe_msg.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
            
            # Essayer d'écrire dans le stream
            try:
                # Pour stdout/stderr sur Windows, utiliser le buffer binaire avec UTF-8
                if hasattr(stream, 'buffer') and hasattr(stream.buffer, 'write'):
                    try:
                        # Essayer d'écrire directement en UTF-8
                        stream.buffer.write(safe_msg_encoded.encode('utf-8', errors='replace'))
                        stream.buffer.write(self.terminator.encode('utf-8', errors='replace'))
                        stream.buffer.flush()
                    except (UnicodeEncodeError, AttributeError, TypeError, OSError):
                        # Si UTF-8 échoue, utiliser ASCII
                        try:
                            stream.buffer.write(safe_msg_encoded.encode('ascii', errors='replace'))
                            stream.buffer.write(self.terminator.encode('ascii', errors='replace'))
                            stream.buffer.flush()
                        except Exception:
                            # Dernier recours : ignorer silencieusement
                            pass
                else:
                    # Fallback pour autres streams
                    try:
                        stream.write(safe_msg_encoded)
                        stream.write(self.terminator)
                        stream.flush()
                    except (UnicodeEncodeError, AttributeError, TypeError, OSError):
                        # Si l'écriture échoue, ignorer silencieusement
                        pass
            except Exception:
                # Si tout échoue, ignorer silencieusement pour éviter les boucles d'erreur
                pass
        except Exception:
            # Ignorer toutes les erreurs pour éviter les boucles infinies
            pass

def load_shop_config(base_dir):
    """Charge la configuration des magasins depuis le magasins.json unifié"""
    try:
        # Chercher dans le répertoire fourni (API_PROSUMA_RPOS)
        config_path = os.path.join(base_dir, 'magasins.json')
        
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            print(f"❌ Fichier de configuration des magasins introuvable: {config_path}")
            return {}
    except Exception as e:
        print(f"❌ Erreur lors du chargement de la configuration des magasins: {e}")
        return {}

def get_api_folder_name(api_name: str) -> str:
    """Mappe un nom d'API vers le nom de dossier réseau attendu."""
    mapping = {
        'COMMANDE': 'COMMANDE',
        'ARTICLE': 'ARTICLE',
        'PROMO': 'PROMO',
        'PRODUIT_NON_TROUVE': 'PRODUIT_NON_TROUVE',
        'COMMANDE_THEME': 'COMMANDE_THEME',
        'RECEPTION': 'RECEPTION',
        'PRE_COMMANDE': 'PRE_COMMANDE',
        'RETOUR_MARCHANDISE': 'RETOUR_MARCHANDISE',
        'INVENTAIRE': 'INVENTAIRE',
        'STATS_VENTE': 'STATS_VENTE',
    }
    key = (api_name or '').upper()
    return mapping.get(key, key)

def build_network_path(network_base: str, api_name: str) -> str:
    """Construit le chemin réseau final vers EXPORT/EXPORT_<API> en respectant l'OS.

    - Windows: conserve le chemin UNC et utilise les backslashes
    - Autres OS: utilise des slashes et normalise les UNC en //host/share
    """
    api_folder = get_api_folder_name(api_name)

    base = network_base or ""

    # Windows (nt): garder UNC et backslashes
    if os.name == 'nt':
        base = base.replace('/', '\\').rstrip('\\')
        return f"{base}\\EXPORT\\EXPORT_{api_folder}"

    # Non-Windows: utiliser des slashes
    if base.startswith('\\\\'):
        # Transformer \\host\share\path en //host/share/path
        base = '//' + base.lstrip('\\').replace('\\', '/')
    return f"{base.rstrip('/')}" + f"/EXPORT/EXPORT_{api_folder}"

def create_network_folder(network_path):
    """Crée le dossier réseau s'il n'existe pas"""
    try:
        if not os.path.exists(network_path):
            os.makedirs(network_path, exist_ok=True)
            logger.info(f"✅ Dossier réseau créé: {network_path}")
        return True
    except Exception as e:
        logger.error(f"❌ Erreur lors de la création du dossier réseau {network_path}: {e}")
        return False

def set_log_file_permissions(log_file_path):
    """Définit les permissions d'un fichier de log pour permettre à tous les utilisateurs d'écrire
    
    Sur Windows, utilise PowerShell ou icacls pour définir les permissions NTFS.
    Sur Linux/Mac, utilise chmod pour donner les permissions d'écriture.
    
    Cette fonction est appelée automatiquement après la création de chaque fichier de log
    pour s'assurer que tous les utilisateurs peuvent écrire dedans, même si le fichier
    a été créé par un autre utilisateur.
    
    Args:
        log_file_path: Chemin complet du fichier de log
        
    Returns:
        bool: True si les permissions ont été définies avec succès, False sinon
    """
    if not log_file_path:
        return False
    
    # Attendre un peu que le fichier soit créé (si nécessaire)
    import time
    max_attempts = 3
    for attempt in range(max_attempts):
        if os.path.exists(log_file_path):
            break
        time.sleep(0.1)
    
    if not os.path.exists(log_file_path):
        # Le fichier n'existe pas encore, on essaiera plus tard
        return False
    
    try:
        if platform.system() == 'Windows':
            # Sur Windows, utiliser PowerShell ou icacls pour définir les permissions NTFS
            # Donner à Everyone les permissions de lecture et écriture
            
            # Méthode 1: PowerShell (plus fiable pour les chemins UNC)
            # Échapper les backslashes et guillemets pour PowerShell
            escaped_path = log_file_path.replace('\\', '\\\\').replace('"', '`"')
            ps_command = f'''
$file = "{escaped_path}"
if (Test-Path $file) {{
    try {{
        $acl = Get-Acl $file
        $permission = "Everyone", "Read,Write", "Allow"
        $accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule $permission
        $acl.SetAccessRule($accessRule)
        Set-Acl $file $acl
        exit 0
    }} catch {{
        exit 1
    }}
}} else {{
    exit 1
}}
'''
            try:
                result = subprocess.run(
                    ['powershell', '-ExecutionPolicy', 'Bypass', '-Command', ps_command],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )
                if result.returncode == 0:
                    return True
            except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
                pass
            
            # Méthode 2: icacls (fallback si PowerShell échoue)
            try:
                # Convertir le chemin pour icacls (échapper les backslashes)
                escaped_path = log_file_path.replace('\\', '\\\\')
                icacls_command = ['icacls', escaped_path, '/grant', 'Everyone:(R,W)', '/Q']
                result = subprocess.run(
                    icacls_command,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )
                return result.returncode == 0
            except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
                return False
        else:
            # Sur Linux/Mac, utiliser chmod pour donner les permissions d'écriture à tous
            try:
                # Donner les permissions rw-rw-rw- (666)
                os.chmod(log_file_path, 0o666)
                return True
            except (OSError, PermissionError):
                return False
    except Exception:
        # Ignorer toutes les erreurs silencieusement pour ne pas interrompre l'exécution
        return False







