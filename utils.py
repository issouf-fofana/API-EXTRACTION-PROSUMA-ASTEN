#!/usr/bin/env python3
"""
Utilitaires partagés pour les APIs Prosuma RPOS
"""

import os
import json
import logging
import sys
import io

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







