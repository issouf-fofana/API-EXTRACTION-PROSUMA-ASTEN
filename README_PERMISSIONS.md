# 🔒 Configuration des Permissions des Fichiers .sh

## 📋 Description

Ce script configure les permissions des fichiers `.sh` sur le réseau partagé pour que :
- ✅ **Tous les utilisateurs** puissent **exécuter** les scripts
- ❌ **Seul vous** pouvez **modifier** ou **ouvrir** les fichiers pour les éditer
- ❌ **Les autres utilisateurs** ne peuvent **pas modifier, supprimer ou changer les permissions**

## ⚠️ Limitation Windows

**IMPORTANT** : Sur Windows, l'exécution d'un fichier nécessite la lecture. Par conséquent :
- Les utilisateurs **pourront voir le contenu** du fichier (lecture nécessaire pour exécution)
- Mais ils **ne pourront PAS** :
  - Modifier le fichier
  - Supprimer le fichier
  - Changer les permissions
  - Prendre possession du fichier

## 🚀 Utilisation

### Méthode 1 : Script Batch (Recommandé)

1. Double-cliquez sur `set_permissions.bat`
2. Le script va :
   - Vérifier l'accès au réseau
   - Configurer les permissions pour tous les fichiers `.sh`
   - Afficher un résumé

### Méthode 2 : Script PowerShell Direct

1. Ouvrez PowerShell en tant qu'**Administrateur**
2. Naviguez vers le dossier contenant les scripts
3. Exécutez :
   ```powershell
   .\set_permissions.ps1
   ```

### Paramètres personnalisés

Vous pouvez spécifier le chemin réseau et l'utilisateur :

```powershell
.\set_permissions.ps1 -NetworkPath "\\10.0.70.169\share\FOFANA\Etats Natacha\SCRIPT\EXTRACTION_PROSUMA" -AdminUser "VOTRE_NOM_UTILISATEUR"
```

## 📁 Fichiers Protégés

Les fichiers suivants seront protégés :
- `run_api_extraction.sh`
- `run_commande_reassort.sh`
- Tous les autres fichiers `.sh` dans le dossier

## 🔐 Permissions Configurées

Après exécution, les permissions seront :

| Utilisateur | Lecture | Exécution | Modification | Suppression |
|------------|---------|-----------|--------------|-------------|
| **Vous (Propriétaire)** | ✅ | ✅ | ✅ | ✅ |
| **Tous les utilisateurs** | ✅* | ✅ | ❌ | ❌ |
| **Administrateurs** | ✅ | ✅ | ✅ | ✅ |

*Lecture nécessaire pour l'exécution sur Windows

## 🛠️ Dépannage

### Erreur : "Accès refusé"
- Exécutez PowerShell en tant qu'**Administrateur**
- Vérifiez que vous avez les droits sur le partage réseau

### Erreur : "Chemin réseau non accessible"
- Vérifiez que le chemin réseau est correct
- Vérifiez que vous êtes connecté au réseau
- Vérifiez vos permissions d'accès au partage

### Les permissions ne s'appliquent pas
- Vérifiez que vous avez les droits administrateur
- Vérifiez que le partage réseau permet la modification des permissions NTFS
- Contactez l'administrateur réseau si nécessaire

## 📝 Notes

- Les permissions sont configurées au niveau **NTFS** (fichier système)
- Les permissions de **partage réseau** peuvent également affecter l'accès
- Si vous modifiez les fichiers après avoir configuré les permissions, vous devrez peut-être réexécuter le script

## 🔄 Réinitialisation des Permissions

Pour réinitialiser les permissions (donner accès complet à tous) :

```powershell
# Supprimer les restrictions
icacls "\\10.0.70.169\share\FOFANA\Etats Natacha\SCRIPT\EXTRACTION_PROSUMA\*.sh" /grant Everyone:F
```

Puis réexécutez `set_permissions.bat` pour reconfigurer.

