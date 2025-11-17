@echo off
REM ============================================================================
REM Script pour corriger les permissions des fichiers de log existants
REM Permet à tous les utilisateurs d'écrire dans les fichiers de log
REM ============================================================================

setlocal enabledelayedexpansion

set "LOG_PATH=\\10.0.70.169\share\FOFANA\Etats Natacha\SCRIPT\LOG"

echo ============================================================
echo   CORRECTION DES PERMISSIONS DES FICHIERS DE LOG
echo ============================================================
echo.

REM Utiliser PowerShell pour corriger les permissions
echo 🔒 Correction des permissions via PowerShell...
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0fix_log_permissions.ps1" -LogPath "%LOG_PATH%"

if errorlevel 1 (
    echo.
    echo ❌ Erreur lors de l'exécution du script PowerShell
    echo    Vérifiez que PowerShell est disponible et que vous avez les droits administrateur
    pause
    exit /b 1
)

