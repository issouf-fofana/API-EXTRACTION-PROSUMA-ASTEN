@echo off
setlocal enabledelayedexpansion

:: Configuration
set "PROJECT_PATH=%~dp0"
set "NETWORK_PROJECT=\\10.0.70.169\share\FOFANA\Etats Natacha\SCRIPT\API"
set "ENV_NAME=env_Api_Extraction_Alien"
set "ENV_PATH=%USERPROFILE%\%ENV_NAME%"
set "PYTHON_MIN_VERSION=3.8"

echo ============================================================
echo           API EXTRACTION PROSUMA - EXTRACTEUR UNIFIÉ
echo ============================================================
echo.

:: Vérifier si Python est installé
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python n'est pas installé ou pas dans le PATH
    echo    Veuillez installer Python 3.8+ depuis https://python.org
    pause
    exit /b 1
)

:: Vérifier la version de Python
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python %PYTHON_VERSION% détecté

:: Créer l'environnement virtuel s'il n'existe pas
if not exist "%ENV_PATH%" (
    echo.
    echo 🔧 Création de l'environnement virtuel...
    python -m venv "%ENV_PATH%"
    if errorlevel 1 (
        echo ❌ Erreur lors de la création de l'environnement virtuel
        pause
        exit /b 1
    )
    echo ✅ Environnement virtuel créé: %ENV_PATH%
) else (
    echo ✅ Environnement virtuel existant trouvé: %ENV_PATH%
)

:: Activer l'environnement virtuel
echo.
echo 🔄 Activation de l'environnement virtuel...
call "%ENV_PATH%\Scripts\activate.bat"
if errorlevel 1 (
    echo ❌ Erreur lors de l'activation de l'environnement virtuel
    pause
    exit /b 1
)

:: Mettre à jour pip
echo.
echo 📦 Mise à jour de pip...
python -m pip install --upgrade pip

:: Installer ou mettre à jour les dépendances
echo.
echo 📦 Installation/mise à jour des dépendances...
if exist "%NETWORK_PROJECT%\requirements.txt" (
    pip install -r "%NETWORK_PROJECT%\requirements.txt" --upgrade
    if errorlevel 1 (
        echo ❌ Erreur lors de l'installation des dépendances
        pause
        exit /b 1
    )
    echo ✅ Dépendances installées/mises à jour
) else (
    echo ⚠️  Fichier requirements.txt non trouvé sur le réseau
)

:: Menu principal
:menu
cls
echo ============================================================
echo           API EXTRACTION PROSUMA - MENU PRINCIPAL
echo ============================================================
echo.
echo Environnement: %ENV_NAME%
echo Projet: %NETWORK_PROJECT%
echo.
echo 📋 EXTRACTIONS DISPONIBLES:
echo.
echo   1. Commandes Fournisseurs
echo   2. Articles
echo   3. Promotions
echo   4. Produits Non Trouvés
echo   5. Commandes par Thème/Promotion
echo   6. Réception de Commandes
echo   7. Pré-commandes Fournisseurs
echo   8. Retours de Marchandises
echo   9. Inventaires
echo  10. Statistiques de Ventes
echo.
echo   A. Extraire TOUT (toutes les APIs)
echo   Q. Quitter
echo.
set /p choice="Choisissez une option (1-10, A, Q): "

if /i "%choice%"=="1" goto run_commande
if /i "%choice%"=="2" goto run_article
if /i "%choice%"=="3" goto run_promo
if /i "%choice%"=="4" goto run_produit_non_trouve
if /i "%choice%"=="5" goto run_commande_theme
if /i "%choice%"=="6" goto run_reception
if /i "%choice%"=="7" goto run_pre_commande
if /i "%choice%"=="8" goto run_retour_marchandise
if /i "%choice%"=="9" goto run_inventaire
if /i "%choice%"=="10" goto run_stats_vente
if /i "%choice%"=="A" goto run_all
if /i "%choice%"=="Q" goto end
goto menu

:: Fonctions d'exécution
:run_commande
echo.
echo 🚀 Lancement de l'extraction COMMANDES...
cd /d "%NETWORK_PROJECT%\API_COMMANDE"
python api_commande.py
goto continue

:run_article
echo.
echo 🚀 Lancement de l'extraction ARTICLES...
echo ℹ️  Extraction de TOUS les articles (sans filtre de date)
cd /d "%NETWORK_PROJECT%\API_ARTICLE"
set DATE_START=
set DATE_END=
python api_article.py
goto continue

:run_promo
echo.
echo 🚀 Lancement de l'extraction PROMOTIONS...
cd /d "%NETWORK_PROJECT%\API_PROMO"
python api_promo.py
goto continue

:run_produit_non_trouve
echo.
echo 🚀 Lancement de l'extraction PRODUITS NON TROUVÉS...
cd /d "%NETWORK_PROJECT%\API_PRODUIT_NON_TROUVE"
python api_produit_non_trouve.py
goto continue

:run_commande_theme
echo.
echo 🚀 Lancement de l'extraction COMMANDES THÈME...
cd /d "%NETWORK_PROJECT%\API_COMMANDE_THEME"
python api_commande_theme.py
goto continue

:run_reception
echo.
echo 🚀 Lancement de l'extraction RÉCEPTION...
cd /d "%NETWORK_PROJECT%\API_RECEPTION"
python api_reception.py
goto continue

:run_pre_commande
echo.
echo 🚀 Lancement de l'extraction PRÉ-COMMANDES...
cd /d "%NETWORK_PROJECT%\API_PRE_COMMANDE"
python api_pre_commande.py
goto continue

:run_retour_marchandise
echo.
echo 🚀 Lancement de l'extraction RETOURS MARCHANDISES...
cd /d "%NETWORK_PROJECT%\API_RETOUR_MARCHANDISE"
python api_retour_marchandise.py
goto continue

:run_inventaire
echo.
echo 🚀 Lancement de l'extraction INVENTAIRES...
cd /d "%NETWORK_PROJECT%\API_INVENTAIRE"
python api_inventaire.py
goto continue

:run_stats_vente
echo.
echo 🚀 Lancement de l'extraction STATISTIQUES VENTES...
cd /d "%NETWORK_PROJECT%\API_STATS_VENTE"
python api_stats_vente.py
goto continue

:run_all
echo.
echo 🚀 Lancement de TOUTES les extractions...
echo.
echo 1/10 - Commandes Fournisseurs...
cd /d "%NETWORK_PROJECT%\API_COMMANDE"
python api_commande.py
echo.
echo 2/10 - Articles...
echo ℹ️  Extraction de TOUS les articles (sans filtre de date)
cd /d "%NETWORK_PROJECT%\API_ARTICLE"
set DATE_START=
set DATE_END=
python api_article.py
echo.
echo 3/10 - Promotions...
cd /d "%NETWORK_PROJECT%\API_PROMO"
python api_promo.py
echo.
echo 4/10 - Produits Non Trouvés...
cd /d "%NETWORK_PROJECT%\API_PRODUIT_NON_TROUVE"
python api_produit_non_trouve.py
echo.
echo 5/10 - Commandes par Thème...
cd /d "%NETWORK_PROJECT%\API_COMMANDE_THEME"
python api_commande_theme.py
echo.
echo 6/10 - Réception de Commandes...
cd /d "%NETWORK_PROJECT%\API_RECEPTION"
python api_reception.py
echo.
echo 7/10 - Pré-commandes Fournisseurs...
cd /d "%NETWORK_PROJECT%\API_PRE_COMMANDE"
python api_pre_commande.py
echo.
echo 8/10 - Retours de Marchandises...
cd /d "%NETWORK_PROJECT%\API_RETOUR_MARCHANDISE"
python api_retour_marchandise.py
echo.
echo 9/10 - Inventaires...
cd /d "%NETWORK_PROJECT%\API_INVENTAIRE"
python api_inventaire.py
echo.
echo 10/10 - Statistiques de Ventes...
cd /d "%NETWORK_PROJECT%\API_STATS_VENTE"
python api_stats_vente.py
echo.
echo ✅ Toutes les extractions terminées !
goto continue

:continue
echo.
echo ============================================================
echo.
set /p continue="Appuyez sur Entrée pour continuer ou 'Q' pour quitter: "
if /i "%continue%"=="Q" goto end
goto menu

:end
echo.
echo ============================================================
echo                    📁 FICHIERS CSV GÉNÉRÉS
echo ============================================================
echo.
echo Les fichiers CSV ont été générés dans :
echo.
echo 📂 RÉSEAU PARTAGÉ:
echo    \\10.0.70.169\share\FOFANA\Etats Natacha\SCRIPT\EXPORT\
echo.
echo 📁 Dossiers par type d'extraction :
echo    ├── EXPORT_COMMANDE\          (Commandes Fournisseurs)
echo    ├── EXPORT_ARTICLE\           (Articles)
echo    ├── EXPORT_PROMO\             (Promotions)
echo    ├── EXPORT_PRODUIT_NON_TROUVE\ (Produits Non Trouvés)
echo    ├── EXPORT_COMMANDE_THEME\    (Commandes par Thème)
echo    ├── EXPORT_RECEPTION\         (Réception de Commandes)
echo    ├── EXPORT_PRE_COMMANDE\      (Pré-commandes Fournisseurs)
echo    ├── EXPORT_RETOUR_MARCHANDISE\ (Retours de Marchandises)
echo    ├── EXPORT_INVENTAIRE\        (Inventaires)
echo    └── EXPORT_STATS_VENTE\       (Statistiques de Ventes)
echo.
echo 📋 LOGS:
echo    \\10.0.70.169\share\FOFANA\Etats Natacha\SCRIPT\LOG\
echo.
echo 💡 Pour accéder aux fichiers :
echo    1. Ouvrez l'Explorateur Windows
echo    2. Tapez dans la barre d'adresse : \\10.0.70.169\share\FOFANA\Etats Natacha\SCRIPT\EXPORT\
echo    3. Naviguez vers le dossier de l'extraction souhaitée
echo.
echo "👋 Au revoir ! Ce script a été créé par Alien pour l'extraction des APIs Prosuma."
deactivate
pause
exit /b 0
