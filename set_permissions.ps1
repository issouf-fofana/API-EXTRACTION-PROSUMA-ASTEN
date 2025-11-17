# ============================================================================
# Script de configuration des permissions pour les fichiers .sh
# Permet l'exécution à tous, mais restreint la lecture/modification
# ============================================================================

param(
    [string]$NetworkPath = "\\10.0.70.169\share\FOFANA\Etats Natacha\SCRIPT\EXTRACTION_PROSUMA",
    [string]$AdminUser = $env:USERNAME
)

Write-Host "============================================================"
Write-Host "  CONFIGURATION DES PERMISSIONS DES FICHIERS .SH"
Write-Host "============================================================"
Write-Host ""

# Vérifier que le chemin réseau est accessible
if (-not (Test-Path $NetworkPath)) {
    Write-Host "❌ ERREUR: Le chemin réseau n'est pas accessible: $NetworkPath" -ForegroundColor Red
    Write-Host "   Vérifiez que vous avez accès au réseau partagé" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Chemin réseau accessible: $NetworkPath" -ForegroundColor Green
Write-Host ""

# Fichiers à protéger
$FilesToProtect = @(
    "run_api_extraction.sh",
    "run_commande_reassort.sh"
)

# Obtenir les fichiers .sh dans le dossier
$ShFiles = Get-ChildItem -Path $NetworkPath -Filter "*.sh" -File

if ($ShFiles.Count -eq 0) {
    Write-Host "⚠️  Aucun fichier .sh trouvé dans $NetworkPath" -ForegroundColor Yellow
    Write-Host "   Les fichiers seront protégés lorsqu'ils seront présents" -ForegroundColor Yellow
    Write-Host ""
}

# Fonction pour définir les permissions
function Set-FilePermissions {
    param(
        [string]$FilePath,
        [string]$Owner
    )
    
    try {
        Write-Host "🔒 Configuration des permissions pour: $(Split-Path $FilePath -Leaf)" -ForegroundColor Cyan
        
        # Obtenir l'ACL actuel
        $Acl = Get-Acl $FilePath
        
        # Définir le propriétaire (vous)
        $OwnerAccount = New-Object System.Security.Principal.NTAccount($Owner)
        $Acl.SetOwner($OwnerAccount)
        
        # Supprimer toutes les permissions existantes
        $Acl.SetAccessRuleProtection($true, $false)
        $Acl.Access | ForEach-Object { $Acl.RemoveAccessRule($_) | Out-Null }
        
        # Ajouter la permission complète pour le propriétaire (vous)
        $OwnerPermission = New-Object System.Security.AccessControl.FileSystemAccessRule(
            $OwnerAccount,
            "FullControl",
            "Allow"
        )
        $Acl.AddAccessRule($OwnerPermission)
        
        # Ajouter la permission d'exécution pour "Everyone" (tous les utilisateurs)
        # Note: Sur Windows, l'exécution nécessite la lecture, donc on donne "ReadAndExecute"
        # Les utilisateurs pourront lire le fichier mais pas le modifier
        $EveryoneAccount = New-Object System.Security.Principal.NTAccount("Everyone")
        $EveryonePermission = New-Object System.Security.AccessControl.FileSystemAccessRule(
            $EveryoneAccount,
            "ReadAndExecute",
            "Allow"
        )
        $Acl.AddAccessRule($EveryonePermission)
        
        # IMPORTANT: Retirer explicitement les permissions d'écriture pour Everyone
        $EveryoneWriteDeny = New-Object System.Security.AccessControl.FileSystemAccessRule(
            $EveryoneAccount,
            "Write,Modify,Delete,TakeOwnership,ChangePermissions",
            "Deny"
        )
        $Acl.AddAccessRule($EveryoneWriteDeny)
        
        # Ajouter la permission pour les administrateurs
        $AdminAccount = New-Object System.Security.Principal.NTAccount("BUILTIN\Administrators")
        $AdminPermission = New-Object System.Security.AccessControl.FileSystemAccessRule(
            $AdminAccount,
            "FullControl",
            "Allow"
        )
        $Acl.AddAccessRule($AdminPermission)
        
        # Appliquer les permissions
        Set-Acl -Path $FilePath -AclObject $Acl
        
        Write-Host "   ✅ Permissions configurées avec succès" -ForegroundColor Green
        Write-Host "      - Propriétaire ($Owner): Contrôle total" -ForegroundColor Gray
        Write-Host "      - Everyone: Lecture et Exécution uniquement" -ForegroundColor Gray
        Write-Host "      - Administrateurs: Contrôle total" -ForegroundColor Gray
        
        return $true
    }
    catch {
        Write-Host "   ❌ Erreur lors de la configuration: $_" -ForegroundColor Red
        return $false
    }
}

# Traiter chaque fichier .sh
$SuccessCount = 0
$FailCount = 0

foreach ($File in $ShFiles) {
    $FilePath = $File.FullName
    
    if (Set-FilePermissions -FilePath $FilePath -Owner $AdminUser) {
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
Write-Host "  Fichiers traités: $($ShFiles.Count)" -ForegroundColor Cyan
Write-Host "  ✅ Succès: $SuccessCount" -ForegroundColor Green
Write-Host "  ❌ Échecs: $FailCount" -ForegroundColor $(if ($FailCount -gt 0) { "Red" } else { "Gray" })
Write-Host ""

if ($SuccessCount -gt 0) {
    Write-Host "✅ Configuration terminée avec succès!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 Permissions configurées:" -ForegroundColor Yellow
    Write-Host "   - Vous ($AdminUser): Peut lire, modifier et exécuter" -ForegroundColor White
    Write-Host "   - Tous les utilisateurs: Peuvent lire et exécuter (lecture nécessaire pour exécution)" -ForegroundColor White
    Write-Host "   - Tous les utilisateurs: NE PEUVENT PAS modifier, supprimer ou changer les permissions" -ForegroundColor White
    Write-Host "   - Administrateurs: Contrôle total" -ForegroundColor White
    Write-Host ""
    Write-Host "⚠️  NOTE IMPORTANTE:" -ForegroundColor Yellow
    Write-Host "   Sur Windows, l'exécution d'un fichier nécessite la lecture." -ForegroundColor Yellow
    Write-Host "   Les utilisateurs pourront donc voir le contenu du fichier." -ForegroundColor Yellow
    Write-Host "   Mais ils ne pourront PAS le modifier, supprimer ou changer les permissions." -ForegroundColor Yellow
} else {
    Write-Host "⚠️  Aucun fichier n'a pu être configuré" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "⏸️  Appuyez sur une touche pour fermer..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

