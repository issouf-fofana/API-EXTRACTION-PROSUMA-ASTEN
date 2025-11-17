#!/bin/bash

# ============================================================================
# Configuration - Exécution depuis le réseau partagé
# Ce script peut être placé n'importe où (ex: Bureau)
# Il exécute le code depuis le dossier réseau partagé
# ============================================================================

# Fonction pour définir la taille du terminal (Windows uniquement)
# Taille fixe: 80 colonnes × 40 lignes (non redimensionnable)
set_terminal_size() {
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]] || [[ -n "$MSYSTEM" ]]; then
        # Windows : définir la taille du terminal
        # Colonnes: 80, Lignes: 40 (taille maximale et fixe)
        
        # Méthode 1: PowerShell (pour console Windows native)
        powershell -Command "\$Host.UI.RawUI.WindowSize = New-Object System.Management.Automation.Host.Size(80, 40); \$Host.UI.RawUI.BufferSize = New-Object System.Management.Automation.Host.Size(80, 9999); \$Host.UI.RawUI.MaxWindowSize = New-Object System.Management.Automation.Host.Size(80, 40); \$Host.UI.RawUI.MaxPhysicalWindowSize = New-Object System.Management.Automation.Host.Size(80, 40)" 2>/dev/null || true
        
        # Méthode 2: mode (pour CMD) - définit la taille et limite le redimensionnement
        mode con: cols=80 lines=40 2>/dev/null || true
        
        # Méthode 3: Pour Git Bash, utiliser resize si disponible
        if command -v resize &> /dev/null; then
            resize -s 40 80 2>/dev/null || true
        fi
        
        # Méthode 4: Pour Git Bash, utiliser printf avec des codes ANSI
        # Code ANSI pour définir la taille: ESC[8;height;widtht
        printf '\033[8;40;80t' 2>/dev/null || true
        
        # Méthode 5: Essayer de désactiver le redimensionnement via PowerShell
        powershell -Command "[Console]::TreatControlCAsInput = \$false; try { \$hwnd = (Get-Process -Id \$PID).MainWindowHandle; if (\$hwnd -ne 0) { Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; public class Win32 { [DllImport(\"user32.dll\")] public static extern int SetWindowLong(IntPtr hWnd, int nIndex, int dwNewLong); [DllImport(\"user32.dll\")] public static extern int GetWindowLong(IntPtr hWnd, int nIndex); public static readonly int GWL_STYLE = -16; public static readonly int WS_SIZEBOX = 0x00040000; }'; \$style = [Win32]::GetWindowLong(\$hwnd, [Win32]::GWL_STYLE); \$newStyle = \$style -band (-bnot [Win32]::WS_SIZEBOX); [Win32]::SetWindowLong(\$hwnd, [Win32]::GWL_STYLE, \$newStyle) } } catch {}" 2>/dev/null || true
    fi
}

# Fonction pour maintenir la taille du terminal (appelée périodiquement)
# Force la taille à 80×40 et empêche le redimensionnement
maintain_terminal_size() {
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]] || [[ -n "$MSYSTEM" ]]; then
        # Redéfinir la taille silencieusement à chaque fois
        printf '\033[8;40;80t' 2>/dev/null || true
        
        # Réappliquer via mode si disponible
        mode con: cols=80 lines=40 2>/dev/null || true
    fi
}

# Variable pour gérer l'interruption
INTERRUPTED=false

# Fonction pour gérer l'interruption (Ctrl+C)
handle_interrupt() {
    # Ignorer les interruptions multiples rapides
    if [ "$INTERRUPTED" = "true" ]; then
        return
    fi
    
    INTERRUPTED=true
    echo
    echo
    echo "⚠️  INTERRUPTION DÉTECTÉE (Ctrl+C)"
    echo
    read -p "Voulez-vous vraiment arrêter l'exécution ? (O/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[OoYy]$ ]]; then
        echo "🛑 Arrêt de l'exécution..."
        if [ -n "$VIRTUAL_ENV" ]; then
            deactivate 2>/dev/null || true
        fi
        exit 130
    else
        echo "✅ Continuation de l'exécution..."
        INTERRUPTED=false
        # Réactiver le trap
        trap 'handle_interrupt' INT
        return
    fi
}

# Définir le trap pour intercepter Ctrl+C
trap 'handle_interrupt' INT

# Définir la taille du terminal au démarrage
set_terminal_size

# Chemin du dossier réseau partagé (code source)
# Format Windows UNC: \\10.0.70.169\share\FOFANA\Etats Natacha\SCRIPT\EXTRACTION_PROSUMA
NETWORK_SHARE="//10.0.70.169/share/FOFANA/Etats Natacha/SCRIPT/EXTRACTION_PROSUMA"

# Convertir le chemin réseau selon l'OS
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]] || [[ -n "$MSYSTEM" ]]; then
    # Windows (Git Bash, Cygwin, MSYS2)
    # Essayer plusieurs formats de chemins UNC
    if [ -d "//10.0.70.169/share/FOFANA/Etats Natacha/SCRIPT/EXTRACTION_PROSUMA" ] 2>/dev/null; then
        PROJECT_PATH="//10.0.70.169/share/FOFANA/Etats Natacha/SCRIPT/EXTRACTION_PROSUMA"
    elif [ -d "\\\\10.0.70.169\\share\\FOFANA\\Etats Natacha\\SCRIPT\\EXTRACTION_PROSUMA" ] 2>/dev/null; then
        PROJECT_PATH="\\\\10.0.70.169\\share\\FOFANA\\Etats Natacha\\SCRIPT\\EXTRACTION_PROSUMA"
    elif [ -d "/c/Users/Public/EXTRACTION_PROSUMA" ] 2>/dev/null; then
        PROJECT_PATH="/c/Users/Public/EXTRACTION_PROSUMA"
    else
        # Utiliser le chemin UNC directement (sera testé plus tard)
        PROJECT_PATH="//10.0.70.169/share/FOFANA/Etats Natacha/SCRIPT/EXTRACTION_PROSUMA"
    fi
else
    # macOS/Linux - utiliser le chemin tel quel
    PROJECT_PATH="$NETWORK_SHARE"
fi

# Environnement virtuel local (créé sur chaque PC)
ENV_NAME="env_Api_Extraction_Alien"
ENV_PATH="$HOME/$ENV_NAME"
PYTHON_MIN_VERSION="3.8"

echo "============================================================"
echo "           API EXTRACTION PROSUMA - EXTRACTEUR UNIFIÉ"
echo "============================================================"
echo
echo "📂 Chemin réseau partagé: $PROJECT_PATH"
echo

# Vérifier que le dossier réseau est accessible
echo "🔍 Vérification de l'accessibilité du dossier réseau..."
if [ ! -d "$PROJECT_PATH" ] 2>/dev/null; then
    echo "❌ ERREUR: Le dossier réseau partagé n'est pas accessible"
    echo "   Chemin testé: $PROJECT_PATH"
    echo
    echo "💡 Solutions possibles:"
    echo "   1. Vérifiez que le réseau est accessible"
    echo "   2. Vérifiez que le chemin réseau est correct"
    echo "   3. Sur Windows, assurez-vous que le lecteur réseau est mappé"
    echo "   4. Vérifiez vos permissions d'accès au réseau"
    echo
    echo "⏸️  Appuyez sur une touche pour fermer..."
    read -n 1 -s
    exit 1
fi

echo "✅ Dossier réseau partagé accessible: $PROJECT_PATH"
echo

# Vérifier si Python est installé (python3 ou python)
# Sur Windows, privilégier "python", sur autres OS privilégier "python3"
echo "🔍 Recherche de Python..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]] || [[ -n "$MSYSTEM" ]]; then
    # Windows : chercher d'abord "python", puis "python3"
    if command -v python &> /dev/null; then
        PY=python
        echo "   ✅ Python trouvé (Windows)"
    elif command -v python3 &> /dev/null; then
        PY=python3
        echo "   ✅ Python3 trouvé (Windows)"
    else
        echo "❌ Python n'est pas installé ou pas dans le PATH"
        echo "   Veuillez installer Python 3.8+ depuis https://python.org"
        echo
        echo "⏸️  Appuyez sur une touche pour fermer..."
        read -n 1 -s
        exit 1
    fi
else
    # macOS/Linux : chercher d'abord "python3", puis "python"
    if command -v python3 &> /dev/null; then
        PY=python3
        echo "   ✅ Python3 trouvé"
    elif command -v python &> /dev/null; then
        PY=python
        echo "   ✅ Python trouvé"
    else
        echo "❌ Python n'est pas installé ou pas dans le PATH"
        echo "   Veuillez installer Python 3.8+ depuis https://python.org"
        echo
        echo "⏸️  Appuyez sur une touche pour fermer..."
        read -n 1 -s
        exit 1
    fi
fi

# Vérifier que Python fonctionne et obtenir la version
echo "🔍 Vérification de la version de Python..."
if ! $PY --version &> /dev/null; then
    echo "❌ Erreur: Impossible d'exécuter $PY"
    echo "   Vérifiez que Python est correctement installé"
    echo
    echo "⏸️  Appuyez sur une touche pour fermer..."
    read -n 1 -s
    exit 1
fi

PYTHON_VERSION=$($PY --version 2>&1 | cut -d' ' -f2)
if [ -z "$PYTHON_VERSION" ]; then
    echo "❌ Erreur: Impossible de déterminer la version de Python"
    echo
    echo "⏸️  Appuyez sur une touche pour fermer..."
    read -n 1 -s
    exit 1
fi
echo "✅ Python $PYTHON_VERSION détecté"

# Vérifier que c'est Python 3
echo "🔍 Vérification que c'est Python 3..."
PYTHON_MAJOR=$($PY -c "import sys; print(sys.version_info.major)" 2>/dev/null)
if [ -z "$PYTHON_MAJOR" ] || [ "$PYTHON_MAJOR" != "3" ]; then
    echo "❌ Erreur: Python 3 est requis, mais Python $PYTHON_MAJOR a été détecté"
    echo "   Veuillez installer Python 3.8+ depuis https://python.org"
    echo
    echo "⏸️  Appuyez sur une touche pour fermer..."
    read -n 1 -s
    exit 1
fi

# Vérifier que le module venv est disponible
echo "🔍 Vérification du module venv..."
if ! $PY -m venv --help &> /dev/null; then
    echo "❌ Erreur: Le module 'venv' n'est pas disponible"
    echo "   Vérifiez que Python est correctement installé avec le module venv"
    echo
    echo "⏸️  Appuyez sur une touche pour fermer..."
    read -n 1 -s
    exit 1
fi

# Créer l'environnement virtuel s'il n'existe pas
if [ ! -d "$ENV_PATH" ]; then
    echo
    echo "🔧 Création de l'environnement virtuel..."
    echo "   Chemin: $ENV_PATH"
    if $PY -m venv "$ENV_PATH" 2>&1; then
        echo "✅ Environnement virtuel créé: $ENV_PATH"
    else
        echo "❌ Erreur lors de la création de l'environnement virtuel"
        echo "   Commande exécutée: $PY -m venv \"$ENV_PATH\""
        echo "   Vérifiez les permissions et que le chemin est valide"
        echo
        echo "⏸️  Appuyez sur une touche pour fermer..."
        read -n 1 -s
        exit 1
    fi
else
    echo "✅ Environnement virtuel existant trouvé: $ENV_PATH"
fi

# Activer l'environnement virtuel
echo
echo "🔄 Activation de l'environnement virtuel..."
if [ -f "$ENV_PATH/bin/activate" ]; then
    source "$ENV_PATH/bin/activate"
elif [ -f "$ENV_PATH/Scripts/activate" ]; then
    # Compat Windows (Git Bash)
    source "$ENV_PATH/Scripts/activate"
else
    echo "❌ Fichier d'activation introuvable dans $ENV_PATH"
    echo "   Fichiers recherchés:"
    echo "   - $ENV_PATH/bin/activate"
    echo "   - $ENV_PATH/Scripts/activate"
    echo
    echo "⏸️  Appuyez sur une touche pour fermer..."
    read -n 1 -s
    exit 1
fi

# Vérifier que l'environnement virtuel est bien activé
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Attention: L'environnement virtuel ne semble pas être activé"
    echo "   Tentative d'utilisation du Python de l'environnement virtuel directement..."
    if [ -f "$ENV_PATH/bin/python" ]; then
        PYTHON_CMD="$ENV_PATH/bin/python"
    elif [ -f "$ENV_PATH/Scripts/python.exe" ]; then
        PYTHON_CMD="$ENV_PATH/Scripts/python.exe"
    else
        echo "❌ Python de l'environnement virtuel introuvable"
        echo "   Fichiers recherchés:"
        echo "   - $ENV_PATH/bin/python"
        echo "   - $ENV_PATH/Scripts/python.exe"
        echo
        echo "⏸️  Appuyez sur une touche pour fermer..."
        read -n 1 -s
        exit 1
    fi
else
    PYTHON_CMD="python"
    echo "✅ Environnement virtuel activé: $VIRTUAL_ENV"
fi

# Exporter PYTHON_CMD pour qu'il soit accessible dans les fonctions
export PYTHON_CMD

# Mettre à jour pip
echo
echo "📦 Mise à jour de pip..."
if ! $PYTHON_CMD -m pip install --upgrade pip --quiet 2>&1; then
    echo "⚠️  Avertissement: Erreur lors de la mise à jour de pip"
    echo "   Continuons quand même..."
fi

# S'assurer qu'on est bien à la racine du projet réseau
echo "🔍 Changement vers le dossier réseau..."
if ! cd "$PROJECT_PATH" 2>/dev/null; then
    echo "❌ ERREUR: Impossible d'accéder au dossier réseau"
    echo "   Chemin: $PROJECT_PATH"
    echo "   Vérifiez que le réseau est accessible et que vous avez les permissions"
    echo
    echo "⏸️  Appuyez sur une touche pour fermer..."
    read -n 1 -s
    exit 1
fi
echo "✅ Répertoire changé vers: $(pwd)"

# Installer ou mettre à jour les dépendances depuis le réseau
echo
echo "📦 Installation/mise à jour des dépendances..."
if [ -f "$PROJECT_PATH/requirements.txt" ]; then
    echo "   Fichier requirements.txt trouvé"
    if ! $PYTHON_CMD -m pip install -r "$PROJECT_PATH/requirements.txt" --upgrade --quiet 2>&1; then
        echo "❌ Erreur lors de l'installation des dépendances"
        echo "   Tentative de réessai avec affichage des erreurs..."
        $PYTHON_CMD -m pip install -r "$PROJECT_PATH/requirements.txt" --upgrade
        if [ $? -ne 0 ]; then
            echo
            echo "⏸️  Appuyez sur une touche pour fermer..."
            read -n 1 -s
            exit 1
        fi
    fi
    echo "✅ Dépendances installées/mises à jour"
else
    echo "⚠️  Fichier requirements.txt non trouvé dans $PROJECT_PATH"
    echo "   Vérifiez que le dossier réseau contient tous les fichiers nécessaires"
    echo "   Continuons quand même..."
fi
echo
echo "✅ Initialisation terminée. Affichage du menu..."
sleep 1

# Fonction pour valider et demander une date
ask_date() {
    local prompt="$1"
    local date_var="$2"
    while true; do
        read -p "$prompt (YYYY-MM-DD): " input_date
        if [[ $input_date =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
            # Vérifier que la date est valide (compatible macOS et Linux)
            if date -j -f "%Y-%m-%d" "$input_date" >/dev/null 2>&1 || date -d "$input_date" >/dev/null 2>&1; then
                eval "$date_var='$input_date'"
                break
            else
                echo "❌ Date invalide. Veuillez ressaisir une date valide."
            fi
        else
            echo "❌ Format incorrect. Utilisez le format YYYY-MM-DD (ex: 2025-01-15)"
        fi
    done
}

# Variables globales pour mémoriser les dates
DATES_ALREADY_SET=false

# Fonction pour demander les dates
ask_dates() {
    echo
    echo "┌──────────────────────────────────────────────────────────────────────────────┐"
    echo "│                                                                              │"
    echo "│                    📅 CONFIGURATION DES DATES D'EXTRACTION                   │"
    echo "│                                                                              │"
    echo "│    1. Aujourd'hui                                                            │"
    echo "│    2. Hier                                                                   │"
    echo "│    3. Dates par défaut (hier à aujourd'hui)                                  │"
    echo "│    4. Dates personnalisées                                                   │"
    echo "│                                                                              │"
    echo "└──────────────────────────────────────────────────────────────────────────────┘"
    echo
    maintain_terminal_size
    read -p "Choisissez une option (1-4): " date_choice
    
    case $date_choice in
        1)
            echo "✅ Utilisation de la date d'aujourd'hui"
            export USE_DEFAULT_DATES="false"
            export CUSTOM_START_DATE=$(date +%Y-%m-%d)
            export CUSTOM_END_DATE=$(date +%Y-%m-%d)
            export DATES_ALREADY_SET=true
            ;;
        2)
            echo "✅ Utilisation de la date d'hier"
            export USE_DEFAULT_DATES="false"
            # Calculer la date d'hier selon l'OS
            if [[ "$OSTYPE" == "darwin"* ]]; then
                # macOS
                export CUSTOM_START_DATE=$(date -v-1d +%Y-%m-%d)
                export CUSTOM_END_DATE=$(date -v-1d +%Y-%m-%d)
            else
                # Linux/Windows
                export CUSTOM_START_DATE=$(date -d "yesterday" +%Y-%m-%d)
                export CUSTOM_END_DATE=$(date -d "yesterday" +%Y-%m-%d)
            fi
            export DATES_ALREADY_SET=true
            ;;
        3)
            echo "✅ Utilisation des dates par défaut (hier à aujourd'hui)"
            export USE_DEFAULT_DATES="true"
            export DATES_ALREADY_SET=true
            ;;
        4)
            echo
            echo "📅 Saisie des dates personnalisées :"
            echo "   Format attendu : YYYY-MM-DD (ex: 2025-01-15)"
            echo
            
            # Demander les dates avec validation
            ask_date "Date de début" "start_date"
            ask_date "Date de fin" "end_date"
            
            # Vérifier que la date de fin est après la date de début
            if [[ "$start_date" > "$end_date" ]]; then
                echo "❌ La date de fin doit être après la date de début."
                echo "   Date de début: $start_date"
                echo "   Date de fin: $end_date"
                echo "   Utilisation des dates par défaut."
                export USE_DEFAULT_DATES="true"
            else
                echo "✅ Dates personnalisées : $start_date à $end_date"
                export USE_DEFAULT_DATES="false"
                export CUSTOM_START_DATE="$start_date"
                export CUSTOM_END_DATE="$end_date"
            fi
            export DATES_ALREADY_SET=true
            ;;
        *)
            echo "❌ Option invalide. Utilisation des dates par défaut."
            export USE_DEFAULT_DATES="true"
            export DATES_ALREADY_SET=true
            ;;
    esac
}

# Fonction pour exécuter une extraction
run_extraction() {
    local api_name="$1"
    local api_folder="$2"
    local script_name="$3"
    local skip_date_prompt="${4:-false}"
  local wants_status_filter=false
  local selected_status=""
    
    echo
    echo "🚀 Lancement de l'extraction $api_name..."
    
    # L'API BASE_ARTICLE ne nécessite pas de dates (récupère tous les articles)
    if [ "$api_folder" = "API_BASE_ARTICLE" ]; then
        echo "ℹ️  Extraction de TOUS les articles (sans filtre de date)"
        skip_date_prompt="true"
    fi
    
    # Demander les dates seulement si pas encore définies et si on n'est pas dans le mode "Extraire TOUT"
    if [ "$DATES_ALREADY_SET" = "false" ] && [ "$skip_date_prompt" = "false" ]; then
        ask_dates
    elif [ "$DATES_ALREADY_SET" = "true" ] && [ "$skip_date_prompt" = "false" ]; then
        echo "📅 Utilisation des dates déjà configurées"
    fi
    
  # Aller dans le dossier API sur le réseau
  if ! cd "$PROJECT_PATH/$api_folder" 2>/dev/null; then
    echo "❌ ERREUR: Impossible d'accéder au dossier $api_folder sur le réseau"
    echo "   Chemin: $PROJECT_PATH/$api_folder"
    return 1
  fi

  # Proposer un filtre de statut pour les APIs Commandes
  case "$api_folder" in
    API_COMMANDE|API_COMMANDE_REASSORT|API_COMMANDE_DIRECTE)
      wants_status_filter=true
      ;;
  esac

  if [ "$wants_status_filter" = "true" ]; then
    echo
    echo "┌──────────────────────────────────────────────────────────────────────────────┐"
    echo "│                                                                              │"
    echo "│                 📊 FILTRE STATUT DES COMMANDES                               │"
    echo "│                                                                              │"
    echo "│    0. Tous les statuts (pas de filtre)                                       │"
    echo "│    1. en attente de livraison                                                │"
    echo "│    2. en préparation                                                        │"
    echo "│    3. complète                                                               │"
    echo "│    4. annulée                                                                │"
    echo "│                                                                              │"
    echo "└──────────────────────────────────────────────────────────────────────────────┘"
    maintain_terminal_size
    read -p "Choisissez un statut (0-4): " status_choice
    case $status_choice in
      1) selected_status="en attente de livraison" ;;
      2) selected_status="en préparation" ;;
      3) selected_status="complète" ;;
      4) selected_status="annulée" ;;
      *) selected_status="" ;;
    esac
    if [ -n "$selected_status" ]; then
      echo "🧭 Filtre statut: $selected_status"
    else
      echo "🧭 Filtre statut: aucun (tous)"
    fi
  fi
    
    # Passer les variables d'environnement pour les dates
    # Pour l'API BASE_ARTICLE, ne pas passer de dates (récupère tous les articles)
    if [ "$api_folder" = "API_BASE_ARTICLE" ]; then
        # S'assurer que les variables de dates ne sont pas définies
        unset DATE_START
        unset DATE_END
        echo "🔧 Variables d'environnement: DATE_START=, DATE_END= (aucune date - extraction complète)"
        $PYTHON_CMD "$script_name"
    elif [ "$USE_DEFAULT_DATES" = "false" ]; then
    echo "🔧 Variables d'environnement définies: DATE_START=$CUSTOM_START_DATE, DATE_END=$CUSTOM_END_DATE"
    if [ -n "$selected_status" ]; then
      DATE_START="$CUSTOM_START_DATE" DATE_END="$CUSTOM_END_DATE" STATUT_COMMANDE="$selected_status" $PYTHON_CMD "$script_name"
    else
      DATE_START="$CUSTOM_START_DATE" DATE_END="$CUSTOM_END_DATE" STATUT_COMMANDE="" $PYTHON_CMD "$script_name"
    fi
    else
        # S'assurer que les variables ne sont pas définies pour utiliser les dates par défaut
        unset DATE_START
        unset DATE_END
    if [ -n "$selected_status" ]; then
      STATUT_COMMANDE="$selected_status" $PYTHON_CMD "$script_name"
    else
      STATUT_COMMANDE="" $PYTHON_CMD "$script_name"
    fi
    fi
}

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
    echo "│             API EXTRACTION BACK OFFICE ASTEN - MENU PRINCIPAL                │"
    echo "│                                                                              │"
    echo "└──────────────────────────────────────────────────────────────────────────────┘"
}

# Menu principal
while true; do
    # Maintenir la taille du terminal
    maintain_terminal_size
    clear
    show_alien_logo
    echo
    echo "┌──────────────────────────────────────────────────────────────────────────────┐"
    echo "│                                                                              │"
    echo "│  📋 EXTRACTIONS DISPONIBLES:                                                │"
    echo "│                                                                              │"
    echo "│    1. Commandes Fournisseurs (Toutes)                                       │"
    echo "│    2. Commandes Directes                                                    │"
    echo "│    3. Commandes Réassort                                                    │"
    echo "│    4. Base Articles (Tous les articles)                                     │"
    echo "│    5. Articles avec prix promo                                              │"
    echo "│    6. Promotions                                                            │"
    echo "│    7. Produits Non Trouvés                                                  │"
    echo "│    8. Commandes par Thème/Promotion                                         │"
    echo "│    9. Réception de Commandes                                                │"
    echo "│   10. Pré-commandes Fournisseurs                                            │"
    echo "│   11. Retours de Marchandises                                               │"
    echo "│   12. Inventaires                                                           │"
    echo "│   13. Statistiques de Ventes                                                │"
    echo "│                                                                              │"
    echo "│    A. Extraire TOUT (toutes les APIs)                                       │"
    echo "│    R. Réinitialiser les dates                                               │"
    echo "│    Q. Quitter                                                               │"
    echo "│                                                                              │"
    echo "└──────────────────────────────────────────────────────────────────────────────┘"
    echo
  
    
    maintain_terminal_size
    read -p "Choisissez une option (1-13, A, R, Q): " choice

    case $choice in
        1)
            run_extraction "COMMANDES" "API_COMMANDE" "api_commande.py"
            ;;
        2)
            run_extraction "COMMANDES DIRECTES" "API_COMMANDE_DIRECTE" "api_commande_directe.py"
            ;;
        3)
            run_extraction "COMMANDES RÉASSORT" "API_COMMANDE_REASSORT" "api_commande_reassort.py"
            ;;
        4)
            run_extraction "BASE ARTICLES" "API_BASE_ARTICLE" "api_article.py" "true"
            ;;
        5)
            run_extraction "ARTICLES AVEC PRIX PROMO" "API_ARTICLE_PROMO" "api_article_promo.py"
            ;;
        6)
            run_extraction "PROMOTIONS" "API_PROMO" "api_promo.py"
            ;;
        7)
            run_extraction "PRODUITS NON TROUVÉS" "API_PRODUIT_NON_TROUVE" "api_produit_non_trouve.py"
            ;;
        8)
            run_extraction "COMMANDES THÈME" "API_COMMANDE_THEME" "api_commande_theme.py"
            ;;
        9)
            run_extraction "RÉCEPTION" "API_RECEPTION" "api_reception.py"
            ;;
        10)
            run_extraction "PRÉ-COMMANDES" "API_PRE_COMMANDE" "api_pre_commande.py"
            ;;
        11)
            run_extraction "RETOURS MARCHANDISES" "API_RETOUR_MARCHANDISE" "api_retour_marchandise.py"
            ;;
        12)
            run_extraction "INVENTAIRES" "API_INVENTAIRE" "api_inventaire.py"
            ;;
        13)
            run_extraction "STATISTIQUES VENTES" "API_STATS_VENTE" "api_stats_vente.py"
            ;;
        A|a)
            echo
            echo "🚀 Lancement de TOUTES les extractions..."
            
            # Demander les dates seulement si pas encore définies
            if [ "$DATES_ALREADY_SET" = "false" ]; then
                ask_dates
            else
                echo "📅 Utilisation des dates déjà configurées"
            fi
            
            echo
            echo "1/13 - Commandes Fournisseurs (Toutes)..."
            run_extraction "COMMANDES" "API_COMMANDE" "api_commande.py" "true"
            echo
            echo "2/13 - Commandes Directes..."
            run_extraction "COMMANDES DIRECTES" "API_COMMANDE_DIRECTE" "api_commande_directe.py" "true"
            echo
            echo "3/13 - Commandes Réassort..."
            run_extraction "COMMANDES RÉASSORT" "API_COMMANDE_REASSORT" "api_commande_reassort.py" "true"
            echo
            echo "4/13 - Base Articles..."
            run_extraction "BASE ARTICLES" "API_BASE_ARTICLE" "api_article.py" "true"
            echo
            echo "5/13 - Articles avec prix promo..."
            run_extraction "ARTICLES AVEC PRIX PROMO" "API_ARTICLE_PROMO" "api_article_promo.py" "true"
            echo
            echo "6/13 - Promotions..."
            run_extraction "PROMOTIONS" "API_PROMO" "api_promo.py" "true"
            echo
            echo "7/13 - Produits Non Trouvés..."
            run_extraction "PRODUITS NON TROUVÉS" "API_PRODUIT_NON_TROUVE" "api_produit_non_trouve.py" "true"
            echo
            echo "8/13 - Commandes par Thème..."
            run_extraction "COMMANDES THÈME" "API_COMMANDE_THEME" "api_commande_theme.py" "true"
            echo
            echo "9/13 - Réception de Commandes..."
            run_extraction "RÉCEPTION" "API_RECEPTION" "api_reception.py" "true"
            echo
            echo "10/13 - Pré-commandes Fournisseurs..."
            run_extraction "PRÉ-COMMANDES" "API_PRE_COMMANDE" "api_pre_commande.py" "true"
            echo
            echo "11/13 - Retours de Marchandises..."
            run_extraction "RETOURS MARCHANDISES" "API_RETOUR_MARCHANDISE" "api_retour_marchandise.py" "true"
            echo
            echo "12/13 - Inventaires..."
            run_extraction "INVENTAIRES" "API_INVENTAIRE" "api_inventaire.py" "true"
            echo
            echo "13/13 - Statistiques de Ventes..."
            run_extraction "STATISTIQUES VENTES" "API_STATS_VENTE" "api_stats_vente.py" "true"
            echo
            echo "✅ Toutes les extractions terminées !"
            ;;
        R|r)
            echo
            echo "🔄 Réinitialisation des dates..."
            export DATES_ALREADY_SET=false
            unset USE_DEFAULT_DATES
            unset CUSTOM_START_DATE
            unset CUSTOM_END_DATE
            echo "✅ Dates réinitialisées. Vous devrez reconfigurer les dates pour la prochaine extraction."
            sleep 2
            continue
            ;;
        Q|q)
            break
            ;;
        *)
            echo "❌ Option invalide. Veuillez choisir 1-13, A, R ou Q."
            sleep 2
            continue
            ;;
    esac

    echo
    echo "============================================================"
    echo
    maintain_terminal_size
    read -p "Appuyez sur Entrée pour continuer ou 'Q' pour quitter: " continue
    if [[ $continue == "Q" || $continue == "q" ]]; then
        break
    fi
done

echo
echo "============================================================"
echo "                    📁 FICHIERS CSV GÉNÉRÉS"
echo "============================================================"
echo
echo "Les fichiers CSV ont été générés dans :"
echo
echo "📂 RÉSEAU PARTAGÉ:"
echo "   /Volumes/SHARE/FOFANA/EXPORT/"
echo
echo "📁 Dossiers par type d'extraction :"
echo "   ├── EXPORT_COMMANDE/          (Commandes Fournisseurs)"
echo "   ├── EXPORT_COMMANDE_DIRECTE/  (Commandes Directes)"
echo "   ├── EXPORT_COMMANDE_REASSORT/ (Commandes Réassort)"
echo "   ├── EXPORT_BASE_ARTICLE/      (Base Articles)"
echo "   ├── EXPORT_ARTICLE_PROMO/     (Articles avec prix promo)"
echo "   ├── EXPORT_PROMO/             (Promotions)"
echo "   ├── EXPORT_PRODUIT_NON_TROUVE/ (Produits Non Trouvés)"
echo "   ├── EXPORT_COMMANDE_THEME/    (Commandes par Thème)"
echo "   ├── EXPORT_RECEPTION/         (Réception de Commandes)"
echo "   ├── EXPORT_PRE_COMMANDE/      (Pré-commandes Fournisseurs)"
echo "   ├── EXPORT_RETOUR_MARCHANDISE/ (Retours de Marchandises)"
echo "   ├── EXPORT_INVENTAIRE/        (Inventaires)"
echo "   └── EXPORT_STATS_VENTE/       (Statistiques de Ventes)"
echo
echo "📋 LOGS:"
echo "   /Volumes/SHARE/FOFANA/Etats Natacha/SCRIPT/LOG/"
echo
echo "💡 Pour accéder aux fichiers :"
echo "   1. Ouvrez le Finder (macOS) ou votre gestionnaire de fichiers"
echo "   2. Naviguez vers : /Volumes/SHARE/FOFANA/EXPORT/"
echo "   3. Naviguez vers le dossier de l'extraction souhaitée"
echo
echo "👋 Au revoir ! Ce script a été créé par Alien pour l'extraction des APIs Prosuma."
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
fi
echo
echo "⏸️  Appuyez sur une touche pour fermer..."
read -n 1 -s