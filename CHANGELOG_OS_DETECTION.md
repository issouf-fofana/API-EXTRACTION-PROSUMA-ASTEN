# 🔄 Changelog - Détection automatique OS et chemins multi-plateformes

**Date** : 26 Novembre 2025  
**Version** : 2.0 - Multi-OS Support  
**Par** : Alien 👽

---

## 🎯 Problème résolu

### Avant ❌
Le script ne fonctionnait pas sur Linux car il tentait d'utiliser des chemins réseau Windows UNC (`//10.0.70.169/share/...`) qui ne sont pas compatibles avec Linux.

**Erreur typique sur Linux :**
```
❌ ERREUR: Le dossier réseau partagé n'est pas accessible
   Chemin testé: //10.0.70.169/share/FOFANA/Etats Natacha/SCRIPT/EXTRACTION_PROSUMA
```

### Après ✅
Les scripts détectent automatiquement l'OS et adaptent les chemins :
- **Linux** : `~/API-EXTRACTION-PROSUMA-ASTEN` ou `/mnt/share/...`
- **Windows** : `//10.0.70.169/share/...`
- **macOS** : `/Volumes/share/...`

---

## 📝 Fichiers modifiés

### 1. `run_api_extraction.sh` ⭐
**Modifications :**
- ✅ Ajout fonction `detect_os()` pour détection automatique
- ✅ Configuration des chemins selon l'OS (Linux/macOS/Windows)
- ✅ Recherche intelligente de multiples chemins possibles
- ✅ Messages informatifs selon l'OS détecté

**Nouveaux chemins supportés (Linux) :**
```bash
1. ~/API-EXTRACTION-PROSUMA-ASTEN (local)
2. /mnt/share/FOFANA/... (montage SMB)
3. /media/share/FOFANA/... (autre montage)
4. $(pwd) (répertoire courant)
```

### 2. `run_commande_reassort.sh` ⭐
**Modifications identiques à `run_api_extraction.sh` :**
- ✅ Même logique de détection OS
- ✅ Mêmes chemins supportés
- ✅ Cohérence entre les deux scripts

---

## 📦 Nouveaux fichiers créés

### 3. `config_paths.sh` 🆕
**Rôle :** Fichier de configuration centralisé pour personnaliser les chemins.

**Variables configurables :**
```bash
# Linux
LINUX_LOCAL_PATH="$HOME/API-EXTRACTION-PROSUMA-ASTEN"
LINUX_MOUNT_PATH="/mnt/share/..."

# macOS
MACOS_VOLUME_PATH="/Volumes/share/..."
MACOS_LOCAL_PATH="$HOME/API-EXTRACTION-PROSUMA-ASTEN"

# Windows
WINDOWS_UNC_PATH="//10.0.70.169/share/..."
WINDOWS_LOCAL_PATH="/c/Users/Public/EXTRACTION_PROSUMA"
```

**Fonction exportée :**
- `get_project_path(os_type)` : Retourne le bon chemin selon l'OS

### 4. `setup_linux_local.sh` 🆕
**Rôle :** Script d'installation locale sur Linux (RECOMMANDÉ).

**Fonctionnalités :**
- ✅ Copie le code localement sur `~/API-EXTRACTION-PROSUMA-ASTEN`
- ✅ 3 méthodes d'installation :
  1. Copie depuis le répertoire courant
  2. Téléchargement depuis le réseau SMB
  3. Clone depuis Git
- ✅ Vérification de l'installation
- ✅ Instructions post-installation

**Usage :**
```bash
chmod +x setup_linux_local.sh
./setup_linux_local.sh
```

### 5. `setup_linux_mount.sh` 🆕
**Rôle :** Script de montage du partage réseau Windows sur Linux.

**Fonctionnalités :**
- ✅ Installation de `cifs-utils` si nécessaire
- ✅ Création du point de montage
- ✅ Montage interactif avec identifiants
- ✅ Vérification de l'accès
- ✅ Instructions pour montage automatique au démarrage

**Usage :**
```bash
chmod +x setup_linux_mount.sh
./setup_linux_mount.sh
```

### 6. `README_LINUX.md` 📚
**Rôle :** Documentation complète pour Linux.

**Contenu :**
- ✅ Guide d'installation (2 options)
- ✅ Configuration personnalisée
- ✅ Utilisation et planification cron
- ✅ Dépannage détaillé
- ✅ Structure des chemins
- ✅ Conseils et bonnes pratiques

### 7. `QUICK_START.md` 🚀
**Rôle :** Guide de démarrage rapide multi-OS.

**Contenu :**
- ✅ Démarrage ultra-rapide (Windows/Linux/macOS)
- ✅ Détection automatique expliquée
- ✅ Résolution de problèmes en 3 étapes
- ✅ Tableau des scripts disponibles
- ✅ Workflow typique
- ✅ Astuces pro

### 8. `CHANGELOG_OS_DETECTION.md` 📋
**Rôle :** Ce fichier - historique des modifications.

---

## 🔍 Détails techniques

### Détection de l'OS

```bash
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]] || [[ -n "$MSYSTEM" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}
```

### Logique de sélection des chemins

**Priorité Linux :**
1. Chemin local (`~/API-EXTRACTION-PROSUMA-ASTEN`) ⭐ RECOMMANDÉ
2. Montage SMB (`/mnt/share/...`)
3. Autre montage (`/media/share/...`)
4. Répertoire courant (`$(pwd)`)

**Priorité Windows :**
1. Chemin réseau UNC (`//10.0.70.169/...`) ⭐ PAR DÉFAUT
2. Chemin UNC backslash (`\\10.0.70.169\...`)
3. Chemin local (`/c/Users/Public/...`)
4. Répertoire courant

**Priorité macOS :**
1. Volume réseau (`/Volumes/share/...`) ⭐ SI MONTÉ
2. Chemin local (`~/API-EXTRACTION-PROSUMA-ASTEN`)
3. Répertoire courant

### Messages informatifs

Le script affiche maintenant l'OS détecté et le chemin utilisé :

```bash
🐧 Système détecté: Linux
   → Utilisation du chemin local: /home/fofana/API-EXTRACTION-PROSUMA-ASTEN
```

```bash
🪟 Système détecté: Windows
   → Utilisation du chemin réseau UNC: //10.0.70.169/share/...
```

---

## ✅ Tests réalisés

### Scénarios testés

| OS | Scénario | Résultat |
|----|----------|----------|
| Windows | Réseau UNC accessible | ✅ OK |
| Windows | Réseau UNC non accessible, local existe | ✅ OK |
| Linux | Installation locale | ✅ OK |
| Linux | Montage SMB | ✅ OK |
| Linux | Répertoire courant | ✅ OK |
| macOS | Volume monté | ✅ OK |
| macOS | Local | ✅ OK |

---

## 📊 Compatibilité

### Systèmes supportés

| OS | Version | Status |
|----|---------|--------|
| Windows 10/11 | Git Bash, WSL | ✅ Supporté |
| Ubuntu | 18.04+ | ✅ Supporté |
| Debian | 10+ | ✅ Supporté |
| CentOS/RHEL | 7+ | ✅ Supporté |
| macOS | 10.15+ | ✅ Supporté |

### Prérequis

| Composant | Windows | Linux | macOS |
|-----------|---------|-------|-------|
| Python 3.8+ | ✅ | ✅ | ✅ |
| Bash | ✅ Git Bash | ✅ Natif | ✅ Natif |
| cifs-utils | ❌ | ⚠️ Si montage | ❌ |
| smbclient | ❌ | ⚠️ Si téléchargement | ❌ |

---

## 🚀 Migration depuis l'ancienne version

### Si vous utilisez déjà le script sur Windows

**Aucune action requise** ✅ - Le script fonctionne exactement comme avant.

### Si vous voulez utiliser sur Linux

**Option 1 - Installation locale (RECOMMANDÉ) :**

```bash
# 1. Transférez les nouveaux fichiers sur votre serveur Linux
# 2. Rendre exécutable
chmod +x setup_linux_local.sh

# 3. Installer
./setup_linux_local.sh

# 4. Utiliser
cd ~/API-EXTRACTION-PROSUMA-ASTEN
chmod +x run_api_extraction.sh
./run_api_extraction.sh
```

**Option 2 - Montage réseau :**

```bash
# 1. Monter le partage
chmod +x setup_linux_mount.sh
./setup_linux_mount.sh

# 2. Le script utilisera automatiquement le montage
./run_api_extraction.sh
```

---

## 🎯 Recommandations

### Pour Linux 🐧

**✅ RECOMMANDÉ : Installation locale**
- ⚡ Plus rapide (pas de latence réseau)
- 🔒 Plus fiable (pas de coupures réseau)
- 💾 Indépendant du réseau

**Commande :**
```bash
./setup_linux_local.sh
```

### Pour Windows 🪟

**✅ RECOMMANDÉ : Réseau direct**
- 🔄 Code toujours à jour
- 📁 Pas de duplication
- 🚀 Fonctionne directement

**Aucune action nécessaire** - utilisez comme avant.

### Pour macOS 🍎

**✅ RECOMMANDÉ : Volume réseau**
- 🔄 Code à jour
- 🖱️ Montage via Finder facile
- 📁 Accessible comme un disque local

**Montage :**
```
Finder → Aller → Se connecter au serveur
smb://10.0.70.169/share
```

---

## 🐛 Problèmes résolus

### Avant
```
❌ Script ne démarre pas sur Linux
❌ Chemin réseau Windows incompatible avec Linux
❌ Erreur "dossier non accessible"
❌ Pas d'alternative au réseau
```

### Après
```
✅ Détection automatique de l'OS
✅ Chemins adaptés selon la plateforme
✅ Multiples chemins de secours
✅ Scripts d'installation pour Linux
✅ Documentation complète
✅ Messages d'aide contextuels
```

---

## 📚 Documentation

| Fichier | Description |
|---------|-------------|
| `README_LINUX.md` | Guide complet Linux |
| `QUICK_START.md` | Démarrage rapide multi-OS |
| `config_paths.sh` | Configuration des chemins |
| `CHANGELOG_OS_DETECTION.md` | Ce fichier |
| `API_*/README.md` | Documentation par API |

---

## 🔮 Évolutions futures possibles

- [ ] Support de variables d'environnement personnalisées
- [ ] Auto-détection du montage SMB actif
- [ ] Script de synchronisation bidirectionnelle
- [ ] Support Docker
- [ ] Interface web de configuration

---

## 👨‍💻 Contributeurs

- **Alien** 👽 - Création et développement

---

## 📞 Support

En cas de problème :
1. Consultez `README_LINUX.md` ou `QUICK_START.md`
2. Vérifiez votre OS avec `echo $OSTYPE`
3. Testez la détection avec `detect_os()`
4. Vérifiez les chemins avec `ls -la`

---

**✅ Version 2.0 - Multi-OS Support est maintenant opérationnelle !**

🚀 Créé avec ❤️ par Alien pour ASTEN - API Extraction Prosuma

