#!/bin/bash

# ============================================================================
# Script d'extraction automatique des commandes réassort
# Période: Hier à Aujourd'hui
# Filtre: En attente de livraison
# ============================================================================

# Configuration
PROJECT_PATH="$(cd "$(dirname "$0")" && pwd)"
ENV_NAME="env_Api_Extraction_Alien"
ENV_PATH="$HOME/$ENV_NAME"

# Fonction pour afficher le logo ALIEN
show_alien_logo() {
    echo "┌──────────────────────────────────────────────────────────────────────────────┐"
    echo "│                                                                              │"
    echo "│                    █████╗ ██╗     ██╗███████╗███╗   ██╗                      │"
    echo "│                   ██╔══██╗██║     ██║██╔════╝████╗  ██║                      │"
    echo "│                   ███████║██║     ██║█████╗  ██╔██╗ ██║                      │"
    echo "│                   ██╔══██║██║     ██║██╔══╝  ██║╚██╗██║                      │"
    echo "│                   ██║  ██║███████╗██║███████╗██║ ╚████║                      │"
    echo "│                   ╚═╝  ╚═╝╚══════╝╚═╝╚══════╝╚═╝  ╚═══╝                      │"
    echo "│                                                                              │"
    echo "│                    EXTRACTION AUTOMATIQUE - COMMANDES RÉASSORT               │"
    echo "│                    Période: Hier à Aujourd'hui                               │"
    echo "│                    Filtre: En attente de livraison                           │"
    echo "│                                                                              │"
    echo "└──────────────────────────────────────────────────────────────────────────────┘"
    echo
}

clear
show_alien_logo

# Vérifier si Python est installé
if command -v python3 &> /dev/null; then
    PY=python3
elif command -v python &> /dev/null; then
    PY=python
else
    echo "❌ Python n'est pas installé ou pas dans le PATH"
    exit 1
fi

# Activer l'environnement virtuel s'il existe
if [ -f "$ENV_PATH/bin/activate" ]; then
    echo "🔄 Activation de l'environnement virtuel..."
    source "$ENV_PATH/bin/activate"
    echo "✅ Environnement virtuel activé"
    echo
fi

# Calculer les dates (hier et aujourd'hui)
# Format: YYYY-MM-DD
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    DATE_START=$(date -v-1d +%Y-%m-%d)
    DATE_END=$(date +%Y-%m-%d)
else
    # Linux
    DATE_START=$(date -d "yesterday" +%Y-%m-%d)
    DATE_END=$(date +%Y-%m-%d)
fi

# Afficher les dates
echo "📅 Configuration des dates:"
echo "   Date début: $DATE_START (hier)"
echo "   Date fin:    $DATE_END (aujourd'hui)"
echo

# Définir le filtre de statut
STATUT_COMMANDE="en attente de livraison"

echo "🔍 Filtre appliqué: $STATUT_COMMANDE"
echo

# Exporter les variables d'environnement
export DATE_START
export DATE_END
export STATUT_COMMANDE

# Changer vers le répertoire du projet
cd "$PROJECT_PATH" || exit 1

# Lancer l'extraction
echo "🚀 Lancement de l'extraction des commandes réassort..."
echo "============================================================"
echo

python API_COMMANDE_REASSORT/api_commande_reassort.py

# Récupérer le code de retour
EXIT_CODE=$?

echo
echo "============================================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Extraction terminée avec succès"
else
    echo "❌ Extraction terminée avec des erreurs (code: $EXIT_CODE)"
fi
echo "============================================================"

# Désactiver l'environnement virtuel si activé
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
fi

exit $EXIT_CODE

