# ============================================================================
# Script pour corriger les permissions des fichiers de log existants
# Permet à tous les utilisateurs d'écrire dans les fichiers de log
# ============================================================================

param(
    [string]$LogPath = "\\10.0.70.169\share\FOFANA\Etats Natacha\SCRIPT\LOG"
)

Write-Host "============================================================"
Write-Host "  CORRECTION DES PERMISSIONS DES FICHIERS DE LOG"
Write-Host "============================================================"
Write-Host ""

# Vérifier que le chemin est accessible
if (-not (Test-Path $LogPath)) {
    Write-Host "❌ ERREUR: Le chemin des logs n'est pas accessible: $LogPath" -ForegroundColor Red
    Write-Host "   Vérifiez que vous avez accès au réseau partagé" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Chemin des logs accessible: $LogPath" -ForegroundColor Green
Write-Host ""

# Obtenir tous les fichiers .log dans le dossier
$LogFiles = Get-ChildItem -Path $LogPath -Filter "*.log" -File

if ($LogFiles.Count -eq 0) {
    Write-Host "⚠️  Aucun fichier de log trouvé dans $LogPath" -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host "📋 ${LogFiles.Count} fichier(s) de log trouvé(s)" -ForegroundColor Cyan
    Write-Host ""
}

# Fonction pour corriger les permissions d'un fichier
function Fix-LogFilePermissions {
    param(
        [string]$FilePath
    )
    
    try {
        $FileName = Split-Path $FilePath -Leaf
        Write-Host "🔒 Correction des permissions pour: $FileName" -ForegroundColor Cyan
        
        # Obtenir l'ACL actuel
        $Acl = Get-Acl $FilePath
        
        # Vérifier si Everyone a déjà les permissions d'écriture
        $hasEveryoneWrite = $false
        foreach ($rule in $Acl.Access) {
            if ($rule.IdentityReference -eq "Everyone" -and 
                ($rule.FileSystemRights -match "Write" -or $rule.FileSystemRights -match "FullControl")) {
                $hasEveryoneWrite = $true
                break
            }
        }
        
        if (-not $hasEveryoneWrite) {
            # Ajouter la permission d'écriture pour Everyone
            $EveryoneAccount = New-Object System.Security.Principal.NTAccount("Everyone")
            $EveryonePermission = New-Object System.Security.AccessControl.FileSystemAccessRule(
                $EveryoneAccount,
                "Read,Write",
                "Allow"
            )
            $Acl.SetAccessRule($EveryonePermission)
            
            # Appliquer les permissions
            Set-Acl -Path $FilePath -AclObject $Acl
            
            Write-Host "   ✅ Permissions corrigées" -ForegroundColor Green
            return $true
        } else {
            Write-Host "   ℹ️  Permissions déjà correctes" -ForegroundColor Gray
            return $true
        }
    }
    catch {
        Write-Host "   ❌ Erreur: $_" -ForegroundColor Red
        return $false
    }
}

# Traiter chaque fichier de log
$SuccessCount = 0
$FailCount = 0

foreach ($LogFile in $LogFiles) {
    $FilePath = $LogFile.FullName
    
    if (Fix-LogFilePermissions -FilePath $FilePath) {
        $SuccessCount++
    } else {
        $FailCount++
    }
    Write-Host ""
}

# Résumé
Write-Host "============================================================"
Write-Host "  RÉSUMÉ"
Write-Host "============================================================"
Write-Host "  Fichiers traités: $($LogFiles.Count)" -ForegroundColor Cyan
Write-Host "  ✅ Succès: $SuccessCount" -ForegroundColor Green
Write-Host "  ❌ Échecs: $FailCount" -ForegroundColor $(if ($FailCount -gt 0) { "Red" } else { "Gray" })
Write-Host ""

if ($SuccessCount -gt 0) {
    Write-Host "✅ Correction terminée avec succès!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 Permissions configurées:" -ForegroundColor Yellow
    Write-Host "   - Tous les utilisateurs peuvent maintenant écrire dans les fichiers de log" -ForegroundColor White
} else {
    Write-Host "⚠️  Aucun fichier n'a pu être corrigé" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "⏸️  Appuyez sur une touche pour fermer..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

