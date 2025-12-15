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
if [ -n "$NETWORK_PATH" ]; then
    echo "   Chemin:   $NETWORK_PATH"
else
    echo "   Chemin:   (racine du partage)"
fi
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

# Fonction utilitaire pour tenter un montage avec des identifiants donnés
try_mount() {
    local u="$1"
    local p="$2"
    local d="$3"

    if [ -z "$d" ]; then
        d="PROSUMA"
    fi

    local OPTIONS="username=$u,password=$p,domain=$d,uid=$(id -u),gid=$(id -g),file_mode=0755,dir_mode=0755"

    echo "🔄 Montage du partage réseau avec l'utilisateur '$d\\$u'..."
    if [ -n "$NETWORK_PATH" ]; then
        FULL_SHARE="//$NETWORK_IP/$NETWORK_SHARE/$NETWORK_PATH"
    else
        FULL_SHARE="//$NETWORK_IP/$NETWORK_SHARE"
    fi

    sudo mount -t cifs "$FULL_SHARE" "$LINUX_MOUNT_PATH" -o "$OPTIONS"
    MOUNT_RC=$?

    if [ $MOUNT_RC -eq 0 ]; then
        # Succès
        MOUNT_OPTIONS="$OPTIONS"
        echo "✅ Partage monté avec succès !"
        echo "   Accessible à: $LINUX_MOUNT_PATH"
        echo
        echo "📁 Contenu de $LINUX_MOUNT_PATH :"
        ls "$LINUX_MOUNT_PATH"
        echo
        echo "💡 Pour démonter: sudo umount $LINUX_MOUNT_PATH"
        echo "💡 Pour monter automatiquement au démarrage, ajoutez dans /etc/fstab:"
        echo "   $FULL_SHARE $LINUX_MOUNT_PATH cifs $MOUNT_OPTIONS 0 0"
    fi

    return $MOUNT_RC
}

CONFIG_FILE="$SCRIPT_DIR/config_paths.sh"

# 1) Essayer automatiquement avec les identifiants enregistrés (si présents)
if [ -n "$MOUNT_USERNAME" ] && [ -n "$MOUNT_PASSWORD" ]; then
    echo
    echo "🔐 Utilisation des identifiants enregistrés: ${MOUNT_DOMAIN:-PROSUMA}\\$MOUNT_USERNAME"
    if try_mount "$MOUNT_USERNAME" "$MOUNT_PASSWORD" "${MOUNT_DOMAIN:-PROSUMA}"; then
        echo "✅ Montage réussi avec les identifiants enregistrés."
        echo "============================================================"
        exit 0
    else
        echo "⚠️  Échec du montage avec les identifiants enregistrés."
        echo "    Un nouveau mot de passe vous sera demandé."
        # S'assurer qu'aucun montage partiel ne reste
        sudo umount "$LINUX_MOUNT_PATH" 2>/dev/null || true
    fi
fi

# 2) Demander de nouveaux identifiants à l'utilisateur
echo
echo "🔐 Identifiants de connexion au partage réseau:"
read -p "Nom d'utilisateur (ex: ifofana): " USERNAME
read -p "Domaine Windows (laisser vide pour PROSUMA): " DOMAIN
read -sp "Mot de passe: " PASSWORD
echo
echo

if [ -z "$DOMAIN" ]; then
    DOMAIN="PROSUMA"
fi

if ! try_mount "$USERNAME" "$PASSWORD" "$DOMAIN"; then
    echo "❌ Échec du montage avec les nouveaux identifiants."
    echo "   Vérifiez la connectivité réseau et les droits du compte."
    echo "============================================================"
    exit 1
fi

# 3) Mise à jour automatique de config_paths.sh avec les nouveaux identifiants
if [ -w "$CONFIG_FILE" ]; then
    echo "📝 Mise à jour des identifiants enregistrés dans config_paths.sh..."
    # Remplacer les lignes existantes (si présentes), sinon les ajouter à la fin
    if grep -q "^MOUNT_USERNAME=" "$CONFIG_FILE"; then
        sed -i.bak "s/^MOUNT_USERNAME=.*/MOUNT_USERNAME=\"$USERNAME\"/" "$CONFIG_FILE"
    else
        echo "MOUNT_USERNAME=\"$USERNAME\"" >> "$CONFIG_FILE"
    fi

    if grep -q "^MOUNT_PASSWORD=" "$CONFIG_FILE"; then
        sed -i.bak "s/^MOUNT_PASSWORD=.*/MOUNT_PASSWORD=\"$PASSWORD\"/" "$CONFIG_FILE"
    else
        echo "MOUNT_PASSWORD=\"$PASSWORD\"" >> "$CONFIG_FILE"
    fi

    if grep -q "^MOUNT_DOMAIN=" "$CONFIG_FILE"; then
        sed -i.bak "s/^MOUNT_DOMAIN=.*/MOUNT_DOMAIN=\"$DOMAIN\"/" "$CONFIG_FILE"
    else
        echo "MOUNT_DOMAIN=\"$DOMAIN\"" >> "$CONFIG_FILE"
    fi

    echo "✅ Identifiants mis à jour dans $CONFIG_FILE"
else
    echo "⚠️  Impossible de mettre à jour $CONFIG_FILE (droits insuffisants)."
fi

echo
echo "============================================================"

