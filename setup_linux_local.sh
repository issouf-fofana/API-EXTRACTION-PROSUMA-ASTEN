#!/bin/bash

# ============================================================================
# Script de copie locale du code sur Linux
# Alternative au montage réseau: copie le code localement
# ============================================================================

# Charger la configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config_paths.sh" 2>/dev/null || {
    LINUX_LOCAL_PATH="$HOME/API-EXTRACTION-PROSUMA-ASTEN"
}

echo "============================================================"
echo "    INSTALLATION LOCALE DU CODE SUR LINUX"
echo "============================================================"
echo

# Vérifier qu'on est bien sur Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "❌ Ce script est conçu pour Linux uniquement"
    exit 1
fi

echo "📋 Configuration:"
echo "   Destination: $LINUX_LOCAL_PATH"
echo

# Vérifier si le dossier existe déjà
if [ -d "$LINUX_LOCAL_PATH" ]; then
    echo "⚠️  Le dossier existe déjà: $LINUX_LOCAL_PATH"
    echo
    read -p "Voulez-vous le remplacer ? (O/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[OoYy]$ ]]; then
        echo "🗑️  Suppression de l'ancien dossier..."
        rm -rf "$LINUX_LOCAL_PATH"
    else
        echo "❌ Installation annulée"
        exit 0
    fi
fi

echo "📦 Méthode d'installation:"
echo "   1. Copier depuis ce répertoire (si vous y êtes déjà)"
echo "   2. Télécharger depuis le réseau (SMB)"
echo "   3. Cloner depuis un dépôt Git (si disponible)"
echo
read -p "Choisissez une option (1-3): " INSTALL_METHOD

case $INSTALL_METHOD in
    1)
        # Copier depuis le répertoire courant
        echo
        echo "📂 Copie depuis: $(pwd)"
        echo "   Vers: $LINUX_LOCAL_PATH"
        
        if [ ! -f "$(pwd)/requirements.txt" ]; then
            echo "❌ Vous n'êtes pas dans le bon répertoire"
            echo "   Fichier requirements.txt non trouvé"
            exit 1
        fi
        
        echo "🔄 Copie en cours..."
        mkdir -p "$LINUX_LOCAL_PATH"
        cp -r "$(pwd)"/* "$LINUX_LOCAL_PATH/"
        
        if [ $? -eq 0 ]; then
            echo "✅ Code copié avec succès !"
        else
            echo "❌ Erreur lors de la copie"
            exit 1
        fi
        ;;
        
    2)
        # Télécharger depuis le réseau
        echo
        echo "🌐 Téléchargement depuis le réseau..."
        echo "   Serveur: //10.0.70.169/share"
        echo
        
        read -p "Nom d'utilisateur: " USERNAME
        read -sp "Mot de passe: " PASSWORD
        echo
        echo
        
        # Utiliser smbclient pour copier
        if ! command -v smbclient &> /dev/null; then
            echo "❌ smbclient n'est pas installé"
            echo "   Installez avec: sudo apt-get install smbclient"
            exit 1
        fi
        
        mkdir -p "$LINUX_LOCAL_PATH"
        
        echo "🔄 Téléchargement en cours..."
        smbclient "//10.0.70.169/share" -U "$USERNAME%$PASSWORD" -c "cd \"FOFANA/Etats Natacha/SCRIPT/EXTRACTION_PROSUMA\"; prompt OFF; recurse ON; mget *" -D "$LINUX_LOCAL_PATH"
        
        if [ $? -eq 0 ]; then
            echo "✅ Code téléchargé avec succès !"
        else
            echo "❌ Erreur lors du téléchargement"
            exit 1
        fi
        ;;
        
    3)
        # Clone Git
        echo
        read -p "URL du dépôt Git: " GIT_URL
        
        if [ -z "$GIT_URL" ]; then
            echo "❌ URL vide"
            exit 1
        fi
        
        echo "🔄 Clonage en cours..."
        git clone "$GIT_URL" "$LINUX_LOCAL_PATH"
        
        if [ $? -eq 0 ]; then
            echo "✅ Dépôt cloné avec succès !"
        else
            echo "❌ Erreur lors du clonage"
            exit 1
        fi
        ;;
        
    *)
        echo "❌ Option invalide"
        exit 1
        ;;
esac

# Vérification finale
echo
echo "🔍 Vérification de l'installation..."
if [ -f "$LINUX_LOCAL_PATH/requirements.txt" ]; then
    echo "✅ Installation réussie !"
    echo "   Chemin: $LINUX_LOCAL_PATH"
    echo
    echo "📋 Fichiers trouvés:"
    ls -1 "$LINUX_LOCAL_PATH" | head -10
    echo
    echo "💡 Prochaines étapes:"
    echo "   1. cd $LINUX_LOCAL_PATH"
    echo "   2. ./run_api_extraction.sh"
else
    echo "❌ Installation incomplète"
    echo "   Fichier requirements.txt non trouvé dans $LINUX_LOCAL_PATH"
fi

echo
echo "============================================================"

