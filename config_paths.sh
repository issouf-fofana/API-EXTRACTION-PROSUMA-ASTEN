#!/bin/bash

# ============================================================================
# Fichier de configuration des chemins - À ADAPTER selon votre environnement
# ============================================================================
# Ce fichier permet de configurer les chemins d'accès au projet selon votre
# configuration spécifique. Modifiez les valeurs ci-dessous selon vos besoins.
# ============================================================================

# ==================== LINUX ====================
# Chemin où le code est copié localement sur votre serveur Linux
LINUX_LOCAL_PATH="$HOME/API-EXTRACTION-PROSUMA-ASTEN"

# Chemin du point de montage SMB/CIFS (si vous montez le partage réseau)
# On monte la racine du partage Windows //10.0.70.169/SHARE sur /mnt/share
LINUX_MOUNT_PATH="/mnt/share"

# Informations du partage réseau Windows
NETWORK_IP="10.0.70.169"
NETWORK_SHARE="share"
# On monte la RACINE du partage (FOFANA sera donc visible sous /mnt/share/FOFANA)
NETWORK_PATH=""

# Identifiants par défaut pour le montage SMB (à adapter si besoin)
MOUNT_USERNAME="ifofana"
MOUNT_PASSWORD="youssef59@Alienware"
MOUNT_DOMAIN="PROSUMA"

# ==================== macOS ====================
# Chemin du volume réseau monté sur macOS
MACOS_VOLUME_PATH="/Volumes/share/FOFANA/Etats Natacha/SCRIPT/EXTRACTION_PROSUMA"

# Chemin local sur macOS
MACOS_LOCAL_PATH="$HOME/API-EXTRACTION-PROSUMA-ASTEN"

# ==================== WINDOWS ====================
# Chemin réseau UNC Windows
WINDOWS_UNC_PATH="//10.0.70.169/share/FOFANA/Etats Natacha/SCRIPT/EXTRACTION_PROSUMA"

# Chemin local Windows
WINDOWS_LOCAL_PATH="/c/Users/Public/EXTRACTION_PROSUMA"

# ============================================================================
# NE PAS MODIFIER CI-DESSOUS (sauf si vous savez ce que vous faites)
# ============================================================================

# Fonction pour obtenir le chemin selon l'OS
get_project_path() {
    local os_type="$1"
    
    case "$os_type" in
        linux)
            # Priorité: Local > Mount > Current Dir
            if [ -d "$LINUX_LOCAL_PATH" ]; then
                echo "$LINUX_LOCAL_PATH"
            elif [ -d "$LINUX_MOUNT_PATH" ]; then
                echo "$LINUX_MOUNT_PATH"
            elif [ -f "$(pwd)/API_COMMANDE/api_commande.py" ]; then
                echo "$(pwd)"
            else
                echo "$LINUX_LOCAL_PATH"
            fi
            ;;
        macos)
            if [ -d "$MACOS_VOLUME_PATH" ]; then
                echo "$MACOS_VOLUME_PATH"
            elif [ -d "$MACOS_LOCAL_PATH" ]; then
                echo "$MACOS_LOCAL_PATH"
            else
                echo "$MACOS_LOCAL_PATH"
            fi
            ;;
        windows)
            if [ -d "$WINDOWS_UNC_PATH" ] 2>/dev/null; then
                echo "$WINDOWS_UNC_PATH"
            elif [ -d "$WINDOWS_LOCAL_PATH" ]; then
                echo "$WINDOWS_LOCAL_PATH"
            else
                echo "$WINDOWS_UNC_PATH"
            fi
            ;;
        *)
            echo "$(pwd)"
            ;;
    esac
}

# Export des variables pour utilisation dans d'autres scripts
export LINUX_LOCAL_PATH
export LINUX_MOUNT_PATH
export NETWORK_IP
export NETWORK_SHARE
export NETWORK_PATH
export MOUNT_USERNAME
export MOUNT_PASSWORD
export MOUNT_DOMAIN
export MACOS_VOLUME_PATH
export MACOS_LOCAL_PATH
export WINDOWS_UNC_PATH
export WINDOWS_LOCAL_PATH

