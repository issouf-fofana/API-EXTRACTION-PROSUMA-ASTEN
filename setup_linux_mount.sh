#!/bin/bash

# ============================================================================
# Script de montage du partage réseau Windows sur Linux
# Ce script monte le partage réseau Windows SMB/CIFS sur Linux
# ============================================================================

# Charger la configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config_paths.sh" 2>/dev/null || {
    # Valeurs par défaut si config_paths.sh n'existe pas
    NETWORK_IP="10.0.70.169"
    NETWORK_SHARE="share"
    NETWORK_PATH="FOFANA/Etats Natacha/SCRIPT/EXTRACTION_PROSUMA"
    LINUX_MOUNT_PATH="/mnt/share/FOFANA/Etats Natacha/SCRIPT/EXTRACTION_PROSUMA"
}

echo "============================================================"
echo "    MONTAGE DU PARTAGE RÉSEAU WINDOWS SUR LINUX"
echo "============================================================"
echo

# Vérifier qu'on est bien sur Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "❌ Ce script est conçu pour Linux uniquement"
    echo "   OS détecté: $OSTYPE"
    exit 1
fi

echo "📋 Configuration:"
echo "   Serveur:  $NETWORK_IP"
echo "   Partage:  //$NETWORK_IP/$NETWORK_SHARE"
echo "   Chemin:   $NETWORK_PATH"
echo "   Point de montage: $LINUX_MOUNT_PATH"
echo

# Vérifier si cifs-utils est installé
if ! command -v mount.cifs &> /dev/null; then
    echo "⚠️  Le paquet 'cifs-utils' n'est pas installé"
    echo
    read -p "Voulez-vous l'installer maintenant ? (O/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[OoYy]$ ]]; then
        echo "📦 Installation de cifs-utils..."
        if command -v apt-get &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y cifs-utils
        elif command -v yum &> /dev/null; then
            sudo yum install -y cifs-utils
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y cifs-utils
        else
            echo "❌ Gestionnaire de paquets non supporté"
            echo "   Installez manuellement: sudo apt-get install cifs-utils"
            exit 1
        fi
    else
        echo "❌ Installation annulée"
        exit 1
    fi
fi

# Vérifier si le point de montage existe
if [ ! -d "$LINUX_MOUNT_PATH" ]; then
    echo "📁 Création du point de montage: $LINUX_MOUNT_PATH"
    sudo mkdir -p "$LINUX_MOUNT_PATH"
    if [ $? -ne 0 ]; then
        echo "❌ Impossible de créer le point de montage"
        exit 1
    fi
fi

# Vérifier si déjà monté
if mount | grep -q "$LINUX_MOUNT_PATH"; then
    echo "✅ Le partage est déjà monté sur $LINUX_MOUNT_PATH"
    echo
    read -p "Voulez-vous le démonter et remonter ? (O/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[OoYy]$ ]]; then
        echo "🔄 Démontage..."
        sudo umount "$LINUX_MOUNT_PATH"
    else
        echo "✅ Terminé"
        exit 0
    fi
fi

# Demander les identifiants
echo
echo "🔐 Identifiants de connexion au partage réseau:"
read -p "Nom d'utilisateur: " USERNAME
read -sp "Mot de passe: " PASSWORD
echo
echo

# Options de montage
MOUNT_OPTIONS="username=$USERNAME,password=$PASSWORD,uid=$(id -u),gid=$(id -g),file_mode=0755,dir_mode=0755"

# Monter le partage
echo "🔄 Montage du partage réseau..."
FULL_SHARE="//$NETWORK_IP/$NETWORK_SHARE/$NETWORK_PATH"

sudo mount -t cifs "$FULL_SHARE" "$LINUX_MOUNT_PATH" -o "$MOUNT_OPTIONS"

if [ $? -eq 0 ]; then
    echo "✅ Partage monté avec succès !"
    echo "   Accessible à: $LINUX_MOUNT_PATH"
    echo
    
    # Tester l'accès
    if [ -f "$LINUX_MOUNT_PATH/requirements.txt" ]; then
        echo "✅ Fichiers du projet accessibles"
    else
        echo "⚠️  Le partage est monté mais les fichiers ne sont pas accessibles"
        echo "   Vérifiez le chemin: $FULL_SHARE"
    fi
    
    echo
    echo "💡 Pour démonter: sudo umount $LINUX_MOUNT_PATH"
    echo "💡 Pour monter automatiquement au démarrage, ajoutez dans /etc/fstab:"
    echo "   $FULL_SHARE $LINUX_MOUNT_PATH cifs $MOUNT_OPTIONS 0 0"
else
    echo "❌ Échec du montage"
    echo "   Vérifiez:"
    echo "   - La connectivité réseau vers $NETWORK_IP"
    echo "   - Les identifiants fournis"
    echo "   - Le chemin du partage: $FULL_SHARE"
fi

echo
echo "============================================================"

