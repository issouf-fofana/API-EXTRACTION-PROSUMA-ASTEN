@echo off
REM ============================================================================
REM Script de test pour extraire les commandes réassort pour des magasins spécifiques
REM Magasins: 110, 230, 292, 294
REM ============================================================================

setlocal

set PROJECT_PATH=%~dp0
set ENV_NAME=env_Api_Extraction_Alien
set ENV_PATH=%USERPROFILE%\%ENV_NAME%

echo ============================================================
echo    TEST EXTRACTION - COMMANDES REASSORT
echo    Magasins: 110, 230, 292, 294
echo    Periode: Hier a Aujourd'hui
echo    Filtre: En attente de livraison
echo ============================================================
echo.

REM Activer l'environnement virtuel s'il existe
if exist "%ENV_PATH%\Scripts\activate.bat" (
    echo Activation de l'environnement virtuel...
    call "%ENV_PATH%\Scripts\activate.bat"
    echo Environnement virtuel active
    echo.
)

REM Calculer les dates (hier et aujourd'hui)
REM Format: YYYY-MM-DD
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set DATE_END=%datetime:~0,4%-%datetime:~4,2%-%datetime:~6,2%

REM Calculer hier (soustraire 1 jour)
powershell -Command "$date = (Get-Date).AddDays(-1); $date.ToString('yyyy-MM-dd')" > %TEMP%\date_start.txt
set /p DATE_START=<%TEMP%\date_start.txt
del %TEMP%\date_start.txt

REM Afficher les dates
echo Configuration des dates:
echo    Date debut: %DATE_START% (hier)
echo    Date fin:    %DATE_END% (aujourd'hui)
echo.

REM Definir le filtre de statut
set STATUT_COMMANDE=en attente de livraison

echo Filtre applique: %STATUT_COMMANDE%
echo.

REM Exporter les variables d'environnement
set DATE_START=%DATE_START%
set DATE_END=%DATE_END%
set STATUT_COMMANDE=%STATUT_COMMANDE%

REM Changer vers le repertoire du projet
cd /d "%PROJECT_PATH%"

REM Lancer le script Python
echo Lancement de l'extraction pour les magasins specifies...
echo ============================================================
echo.

python test_commande_reassort_specific.py

REM Recuperer le code de retour
set EXIT_CODE=%ERRORLEVEL%

echo.
echo ============================================================
if %EXIT_CODE% EQU 0 (
    echo Test termine avec succes
) else (
    echo Test termine avec des erreurs (code: %EXIT_CODE%)
)
echo ============================================================

REM Desactiver l'environnement virtuel si active
if defined VIRTUAL_ENV (
    call deactivate
)

endlocal
exit /b %EXIT_CODE%

