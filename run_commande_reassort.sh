#!/bin/bash

# ============================================================================
# Script d'extraction automatique des commandes réassort
# Période: Hier à Aujourd'hui
# Filtre: En attente de livraison
# 
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

# ============================================================================
# Configuration AUTOMATIQUE et INTELLIGENTE selon l'OS
# Ce script fait TOUT automatiquement : détection, installation, configuration
# ============================================================================

# Détecter l'OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]] || [[ -n "$MSYSTEM" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

# Détecter la distribution Linux et le gestionnaire de paquets
detect_linux_distro() {
    if [ -f /etc/redhat-release ]; then
        # Red Hat, CentOS, Fedora
        if command -v dnf &> /dev/null; then
            echo "redhat-dnf"
        elif command -v yum &> /dev/null; then
            echo "redhat-yum"
        else
            echo "redhat"
        fi
    elif [ -f /etc/debian_version ]; then
        # Debian, Ubuntu
        echo "debian"
    elif [ -f /etc/fedora-release ]; then
        echo "fedora"
    else
        echo "unknown"
    fi
}

# Installer les dépendances système nécessaires (Linux uniquement)
install_system_dependencies() {
    local distro="$1"
    
    echo "🔧 Vérification des dépendances système..."
    
    case "$distro" in
        redhat-dnf)
            echo "   📦 Distribution: Red Hat/CentOS/Fedora (dnf)"
            if ! rpm -qa | grep -q cifs-utils; then
                echo "   ⚙️  Installation de cifs-utils avec dnf..."
                sudo dnf install -y cifs-utils 2>/dev/null || echo "   ⚠️  Installation manuelle requise: sudo dnf install cifs-utils"
            else
                echo "   ✅ cifs-utils déjà installé"
            fi
            ;;
        redhat-yum)
            echo "   📦 Distribution: Red Hat/CentOS (yum)"
            if ! rpm -qa | grep -q cifs-utils; then
                echo "   ⚙️  Installation de cifs-utils avec yum..."
                sudo yum install -y cifs-utils 2>/dev/null || echo "   ⚠️  Installation manuelle requise: sudo yum install cifs-utils"
            else
                echo "   ✅ cifs-utils déjà installé"
            fi
            ;;
        debian)
            echo "   📦 Distribution: Debian/Ubuntu"
            if ! dpkg -l | grep -q cifs-utils; then
                echo "   ⚙️  Installation de cifs-utils avec apt-get..."
                sudo apt-get update >/dev/null 2>&1
                sudo apt-get install -y cifs-utils 2>/dev/null || echo "   ⚠️  Installation manuelle requise: sudo apt-get install cifs-utils"
            else
                echo "   ✅ cifs-utils déjà installé"
            fi
            ;;
        fedora)
            echo "   📦 Distribution: Fedora"
            if ! rpm -qa | grep -q cifs-utils; then
                echo "   ⚙️  Installation de cifs-utils avec dnf..."
                sudo dnf install -y cifs-utils 2>/dev/null || echo "   ⚠️  Installation manuelle requise: sudo dnf install cifs-utils"
            else
                echo "   ✅ cifs-utils déjà installé"
            fi
            ;;
        *)
            echo "   ⚠️  Distribution inconnue"
            ;;
    esac
}

# Configuration automatique du chemin projet
configure_project_path() {
    local os_type="$1"
    local distro="$2"
    
    if [ "$os_type" = "linux" ]; then
        # ==================== LINUX - CONFIGURATION AUTOMATIQUE ====================
        echo "🐧 Système détecté: Linux ($distro)"
        echo
        
        # Installer les dépendances nécessaires
        install_system_dependencies "$distro"
        echo
        
        # Vérifier les chemins possibles
        if [ -d "$HOME/API-EXTRACTION-PROSUMA-ASTEN" ] && [ -f "$HOME/API-EXTRACTION-PROSUMA-ASTEN/requirements.txt" ]; then
            PROJECT_PATH="$HOME/API-EXTRACTION-PROSUMA-ASTEN"
            echo "✅ Installation locale trouvée: $PROJECT_PATH"
            return 0
        elif [ -d "/mnt/share/FOFANA/Etats Natacha/SCRIPT/EXTRACTION_PROSUMA" ] && [ -f "/mnt/share/FOFANA/Etats Natacha/SCRIPT/EXTRACTION_PROSUMA/requirements.txt" ]; then
            PROJECT_PATH="/mnt/share/FOFANA/Etats Natacha/SCRIPT/EXTRACTION_PROSUMA"
            echo "✅ Montage réseau trouvé: $PROJECT_PATH"
            return 0
        elif [ -f "$(pwd)/requirements.txt" ] && [ -f "$(pwd)/API_COMMANDE_REASSORT/api_commande_reassort.py" ]; then
            PROJECT_PATH="$(pwd)"
            echo "✅ Exécution depuis le répertoire du projet: $PROJECT_PATH"
            return 0
        else
            # Installation automatique si on a les fichiers source
            if [ -f "$(pwd)/requirements.txt" ]; then
                echo "✅ Code source détecté - Installation locale automatique..."
                TARGET_PATH="$HOME/API-EXTRACTION-PROSUMA-ASTEN"
                mkdir -p "$TARGET_PATH"
                echo "📂 Copie vers $TARGET_PATH..."
                cp -r "$(pwd)"/* "$TARGET_PATH/" 2>/dev/null || rsync -av --exclude='env*' "$(pwd)/" "$TARGET_PATH/" 2>/dev/null
                PROJECT_PATH="$TARGET_PATH"
                echo "✅ Installation terminée: $PROJECT_PATH"
                return 0
            else
                PROJECT_PATH="$HOME/API-EXTRACTION-PROSUMA-ASTEN"
                echo "⚠️  Aucune installation trouvée: $PROJECT_PATH"
                return 1
            fi
        fi
        
    elif [ "$os_type" = "macos" ]; then
        # ==================== macOS ====================
        echo "🍎 Système détecté: macOS"
        if [ -d "/Volumes/share/FOFANA/Etats Natacha/SCRIPT/EXTRACTION_PROSUMA" ]; then
            PROJECT_PATH="/Volumes/share/FOFANA/Etats Natacha/SCRIPT/EXTRACTION_PROSUMA"
        elif [ -d "$HOME/API-EXTRACTION-PROSUMA-ASTEN" ]; then
            PROJECT_PATH="$HOME/API-EXTRACTION-PROSUMA-ASTEN"
        elif [ -f "$(pwd)/requirements.txt" ]; then
            PROJECT_PATH="$(pwd)"
        else
            PROJECT_PATH="$HOME/API-EXTRACTION-PROSUMA-ASTEN"
        fi
        echo "   → $PROJECT_PATH"
        
    elif [ "$os_type" = "windows" ]; then
        # ==================== WINDOWS ====================
        echo "🪟 Système détecté: Windows"
        if [ -d "//10.0.70.169/share/FOFANA/Etats Natacha/SCRIPT/EXTRACTION_PROSUMA" ] 2>/dev/null; then
            PROJECT_PATH="//10.0.70.169/share/FOFANA/Etats Natacha/SCRIPT/EXTRACTION_PROSUMA"
        elif [ -d "\\\\10.0.70.169\\share\\FOFANA\\Etats Natacha\\SCRIPT\\EXTRACTION_PROSUMA" ] 2>/dev/null; then
            PROJECT_PATH="\\\\10.0.70.169\\share\\FOFANA\\Etats Natacha\\SCRIPT\\EXTRACTION_PROSUMA"
        elif [ -d "/c/Users/Public/EXTRACTION_PROSUMA" ] 2>/dev/null; then
            PROJECT_PATH="/c/Users/Public/EXTRACTION_PROSUMA"
        elif [ -f "$(pwd)/requirements.txt" ]; then
            PROJECT_PATH="$(pwd)"
        else
            PROJECT_PATH="//10.0.70.169/share/FOFANA/Etats Natacha/SCRIPT/EXTRACTION_PROSUMA"
        fi
        echo "   → $PROJECT_PATH"
    else
        echo "❓ Système inconnu: $OSTYPE"
        PROJECT_PATH="$(pwd)"
    fi
}

# Exécuter la configuration
DETECTED_OS=$(detect_os)
LINUX_DISTRO=""

if [ "$DETECTED_OS" = "linux" ]; then
    LINUX_DISTRO=$(detect_linux_distro)
fi

configure_project_path "$DETECTED_OS" "$LINUX_DISTRO"

# Environnement virtuel local (créé sur chaque PC)
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
echo

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

# Exporter PYTHON_CMD pour qu'il soit accessible partout
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
fi
echo

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

# Changer vers le répertoire du projet réseau (déjà fait, mais on vérifie)
if ! cd "$PROJECT_PATH" 2>/dev/null; then
    echo "❌ ERREUR: Impossible d'accéder au dossier réseau"
    echo "   Chemin: $PROJECT_PATH"
    echo "   Vérifiez que le réseau est accessible et que vous avez les permissions"
    echo
    echo "⏸️  Appuyez sur une touche pour fermer..."
    read -n 1 -s
    exit 1
fi

# Lancer l'extraction depuis le réseau
echo "🚀 Lancement de l'extraction des commandes réassort..."
echo "   Code source: $PROJECT_PATH/API_COMMANDE_REASSORT/"
echo "============================================================"
echo

$PYTHON_CMD "$PROJECT_PATH/API_COMMANDE_REASSORT/api_commande_reassort.py"

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

echo
echo "⏸️  Appuyez sur une touche pour fermer..."
read -n 1 -s

exit $EXIT_CODE

