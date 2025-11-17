@echo off
REM ============================================================================
REM Script de configuration des permissions pour les fichiers .sh
REM Permet l'exécution à tous, mais restreint la lecture/modification
REM ============================================================================

setlocal enabledelayedexpansion

set "NETWORK_PATH=\\10.0.70.169\share\FOFANA\Etats Natacha\SCRIPT\EXTRACTION_PROSUMA"
set "ADMIN_USER=%USERNAME%"

echo ============================================================
echo   CONFIGURATION DES PERMISSIONS DES FICHIERS .SH
echo ============================================================
echo.

REM Vérifier que le chemin réseau est accessible
if not exist "%NETWORK_PATH%" (
    echo ❌ ERREUR: Le chemin réseau n'est pas accessible: %NETWORK_PATH%
    echo    Vérifiez que vous avez accès au réseau partagé
    pause
    exit /b 1
)

echo ✅ Chemin réseau accessible: %NETWORK_PATH%
echo.

REM Utiliser PowerShell pour configurer les permissions
echo 🔒 Configuration des permissions via PowerShell...
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0set_permissions.ps1" -NetworkPath "%NETWORK_PATH%" -AdminUser "%ADMIN_USER%"

if errorlevel 1 (
    echo.
    echo ❌ Erreur lors de l'exécution du script PowerShell
    echo    Vérifiez que PowerShell est disponible et que vous avez les droits administrateur
    pause
    exit /b 1
)

