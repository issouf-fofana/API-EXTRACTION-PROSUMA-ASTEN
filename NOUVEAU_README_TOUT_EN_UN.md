# 🚀 Scripts TOUT-EN-UN - Configuration Automatique

**Version** : 3.0 - Auto-Install & Auto-Configure  
**Date** : 26 Novembre 2025  
**Par** : Alien 👽

---

## 🎯 NOUVEAUTÉ : UN SEUL SCRIPT FAIT TOUT !

Fini les multiples scripts à lancer ! Maintenant **un seul fichier** :
- ✅ Détecte automatiquement votre système (Red Hat/Ubuntu/Windows/macOS)
- ✅ Installe automatiquement les dépendances (avec `dnf` pour Red Hat)
- ✅ Configure automatiquement les chemins
- ✅ Copie le code localement si nécessaire
- ✅ Vérifie tout à chaque lancement

---

## 🎨 Ce qui a changé

### Avant (Version 2.0) ❌
```bash
# Il fallait lancer 3 scripts différents :
chmod +x setup_linux_local.sh
./setup_linux_local.sh                 # 1. Installer
cd ~/API-EXTRACTION-PROSUMA-ASTEN
chmod +x run_api_extraction.sh
./run_api_extraction.sh                # 2. Lancer
```

### Maintenant (Version 3.0) ✅
```bash
# UN SEUL SCRIPT FAIT TOUT :
./run_api_extraction.sh                # TERMINÉ !
```

---

## 🔧 Détection automatique

### Red Hat / CentOS / Fedora (VOTRE CAS)
```
🐧 Système détecté: Linux (redhat-dnf)

🔧 Vérification des dépendances système...
   📦 Distribution: Red Hat/CentOS/Fedora (dnf)
   ⚙️  Installation de cifs-utils avec dnf...
   ✅ cifs-utils installé

✅ Code source détecté - Installation locale automatique...
📂 Copie vers /home/fofana/API-EXTRACTION-PROSUMA-ASTEN...
✅ Installation terminée
```

### Ubuntu / Debian
```
🐧 Système détecté: Linux (debian)

🔧 Vérification des dépendances système...
   📦 Distribution: Debian/Ubuntu
   ⚙️  Installation de cifs-utils avec apt-get...
   ✅ cifs-utils installé
```

### Windows
```
🪟 Système détecté: Windows
   → Réseau UNC: //10.0.70.169/share/...
```

---

## 🚀 Utilisation ULTRA-SIMPLE

### Sur Red Hat / CentOS (votre serveur)

```bash
# 1. Première fois : Copier les fichiers sur le serveur
#    (via scp, rsync, ou téléchargement)

# 2. Rendre exécutable
chmod +x run_api_extraction.sh run_commande_reassort.sh

# 3. Lancer - C'EST TOUT !
./run_api_extraction.sh
```

**Le script fait automatiquement :**
1. ✅ Détecte Red Hat + dnf
2. ✅ Installe `cifs-utils` si nécessaire
3. ✅ Copie le code dans `~/API-EXTRACTION-PROSUMA-ASTEN`
4. ✅ Configure l'environnement Python
5. ✅ Installe les dépendances Python
6. ✅ Lance l'extracteur

### Extractions automatiques

```bash
# Commandes réassort (hier → aujourd'hui, en attente de livraison)
./run_commande_reassort.sh

# Planification cron (tous les jours à 8h00)
crontab -e
# Ajouter :
0 8 * * * cd ~/API-EXTRACTION-PROSUMA-ASTEN && ./run_commande_reassort.sh >> ~/extraction.log 2>&1
```

---

## 🔍 Détection et installation automatiques

### Scénarios gérés automatiquement

| Situation | Action automatique |
|-----------|-------------------|
| Code source dans le répertoire courant | ✅ Installation locale automatique |
| Installation locale existe déjà | ✅ Utilisation directe |
| Montage réseau existe | ✅ Utilisation du montage |
| Rien trouvé | ⚠️ Guide d'installation affiché |

### Gestionnaires de paquets supportés

| Distribution | Gestionnaire | Commande utilisée |
|--------------|--------------|-------------------|
| Red Hat 8+ | `dnf` | `sudo dnf install -y cifs-utils` |
| Red Hat 7 | `yum` | `sudo yum install -y cifs-utils` |
| CentOS 8+ | `dnf` | `sudo dnf install -y cifs-utils` |
| CentOS 7 | `yum` | `sudo yum install -y cifs-utils` |
| Fedora | `dnf` | `sudo dnf install -y cifs-utils` |
| Ubuntu/Debian | `apt-get` | `sudo apt-get install -y cifs-utils` |

---

## 📊 Workflow automatique

```
┌─────────────────────────────────────────┐
│  ./run_api_extraction.sh                │
└──────────────┬──────────────────────────┘
               │
               ↓
        ┌──────────────┐
        │ Détecte l'OS │
        └──────┬───────┘
               │
     ┌─────────┴─────────┬─────────────┐
     │                   │             │
     ↓                   ↓             ↓
┌─────────┐       ┌──────────┐   ┌──────────┐
│  Linux  │       │  Windows │   │  macOS   │
└────┬────┘       └─────┬────┘   └────┬─────┘
     │                  │             │
     ↓                  ↓             ↓
┌─────────────┐   ┌─────────────┐  ┌──────────┐
│Détecte distro│   │Utilise UNC  │  │Utilise   │
│Red Hat/Ubuntu│   │réseau direct│  │/Volumes/ │
└──────┬───────┘   └─────┬───────┘  └────┬─────┘
       │                 │                │
       ↓                 │                │
┌──────────────┐         │                │
│Installe deps │         │                │
│(dnf/apt-get) │         │                │
└──────┬───────┘         │                │
       │                 │                │
       ↓                 ↓                ↓
┌───────────────────────────────────────────┐
│  Vérifie/crée installation locale         │
│  ~/API-EXTRACTION-PROSUMA-ASTEN           │
└──────────────┬────────────────────────────┘
               │
               ↓
┌──────────────────────────────────────────┐
│  Configure Python + dépendances          │
└──────────────┬───────────────────────────┘
               │
               ↓
┌──────────────────────────────────────────┐
│  LANCE L'EXTRACTEUR                      │
└──────────────────────────────────────────┘
```

---

## 📁 Chemins utilisés selon l'OS

### Linux (votre cas)

**Priorité de recherche :**
1. `~/API-EXTRACTION-PROSUMA-ASTEN` (local) ⭐ PRÉFÉRÉ
2. `/mnt/share/FOFANA/.../EXTRACTION_PROSUMA` (montage)
3. `$(pwd)` (répertoire courant)

**Si rien trouvé :**
- Copie automatique vers `~/API-EXTRACTION-PROSUMA-ASTEN`

### Windows

**Chemins :**
- `//10.0.70.169/share/...` (réseau UNC)
- `/c/Users/Public/EXTRACTION_PROSUMA` (local)

### macOS

**Chemins :**
- `/Volumes/share/...` (volume réseau)
- `~/API-EXTRACTION-PROSUMA-ASTEN` (local)

---

## 🔄 Mises à jour automatiques

À chaque lancement, le script :

### Linux
- ✅ Vérifie la présence de `cifs-utils`
- ✅ Vérifie l'installation locale
- ✅ Vérifie Python et pip
- ✅ Met à jour les dépendances Python

### Windows
- ✅ Vérifie l'accès réseau
- ✅ Vérifie Python et pip
- ✅ Met à jour les dépendances Python

---

## 📝 Scripts modifiés

| Script | Modifications |
|--------|---------------|
| `run_api_extraction.sh` | ✅ Détection auto + Installation auto |
| `run_commande_reassort.sh` | ✅ Détection auto + Installation auto |

### Nouvelles fonctions ajoutées

```bash
detect_os()                    # Détecte Linux/Windows/macOS
detect_linux_distro()          # Détecte Red Hat/Ubuntu/Fedora/Debian
install_system_dependencies()  # Installe cifs-utils avec dnf/yum/apt-get
configure_project_path()       # Configure et installe automatiquement
```

---

## 🎯 Cas d'usage spécifiques

### Cas 1 : Première installation sur Red Hat

```bash
# Sur votre PC Windows, copiez les fichiers vers le serveur Red Hat
scp -r EXTRACTION_PROSUMA fofana@proextrasten:~/

# Sur le serveur Red Hat
cd ~/EXTRACTION_PROSUMA
chmod +x *.sh
./run_api_extraction.sh

# Le script fait TOUT automatiquement :
# - Détecte Red Hat
# - Installe cifs-utils avec dnf
# - Copie dans ~/API-EXTRACTION-PROSUMA-ASTEN
# - Configure Python
# - Lance l'extracteur
```

### Cas 2 : Mise à jour du code

```bash
# Sur le serveur, écrasez simplement les fichiers
cd ~/EXTRACTION_PROSUMA
# Copiez les nouveaux fichiers

# Relancez le script
./run_api_extraction.sh

# Le script détecte l'installation existante et met à jour
```

### Cas 3 : Exécution planifiée (cron)

```bash
# Configuration cron pour extraction automatique quotidienne
crontab -e

# Ajouter cette ligne (exécution à 8h00 tous les jours)
0 8 * * * cd ~/API-EXTRACTION-PROSUMA-ASTEN && ./run_commande_reassort.sh >> ~/logs/extraction_$(date +\%Y\%m\%d).log 2>&1

# Créer le dossier logs
mkdir -p ~/logs
```

---

## 🐛 Dépannage automatique

### Le script détecte et corrige automatiquement

| Problème détecté | Solution automatique |
|------------------|----------------------|
| `cifs-utils` manquant | Installation avec dnf/yum/apt-get |
| Pas d'installation locale | Copie automatique depuis le répertoire courant |
| Python manquant | Message d'erreur avec instructions |
| Dépendances Python manquantes | Installation automatique avec pip |

### Messages à surveiller

```bash
# ✅ TOUT VA BIEN
✅ Installation locale trouvée
✅ cifs-utils déjà installé
✅ Environnement virtuel activé

# ⚠️  ATTENTION
⚠️  Installation manuelle requise: sudo dnf install cifs-utils
⚠️  Aucune installation trouvée

# ❌ ERREUR
❌ Python n'est pas installé
❌ Impossible de créer l'environnement virtuel
```

---

## 📈 Avantages de la version 3.0

| Fonctionnalité | v2.0 | v3.0 |
|----------------|------|------|
| Détection OS | ✅ | ✅ |
| Détection distribution Linux | ❌ | ✅ |
| Installation dépendances auto | ❌ | ✅ |
| Support dnf (Red Hat 8+) | ❌ | ✅ |
| Support yum (Red Hat 7) | ❌ | ✅ |
| Installation locale auto | ❌ | ✅ |
| Un seul script à lancer | ❌ | ✅ |
| Vérifications à chaque lancement | ❌ | ✅ |

---

## 🎓 Exemples d'utilisation

### Exemple 1 : Première utilisation (Red Hat)

```bash
[fofana@proextrasten EXTRACTION_PROSUMA]$ chmod +x run_api_extraction.sh
[fofana@proextrasten EXTRACTION_PROSUMA]$ ./run_api_extraction.sh

🐧 Système détecté: Linux (redhat-dnf)

🔧 Vérification des dépendances système...
   📦 Distribution: Red Hat/CentOS/Fedora (dnf)
   ⚙️  Installation de cifs-utils avec dnf...
   ✅ cifs-utils installé

✅ Code source détecté - Installation locale automatique...
📂 Copie vers /home/fofana/API-EXTRACTION-PROSUMA-ASTEN...
✅ Installation terminée: /home/fofana/API-EXTRACTION-PROSUMA-ASTEN

============================================================
           API EXTRACTION PROSUMA - EXTRACTEUR UNIFIÉ
============================================================

📂 Chemin réseau partagé: /home/fofana/API-EXTRACTION-PROSUMA-ASTEN

🔍 Vérification de l'accessibilité du dossier réseau...
✅ Dossier réseau partagé accessible

...
[Menu interactif s'affiche]
```

### Exemple 2 : Utilisation suivante

```bash
[fofana@proextrasten ~]$ cd ~/API-EXTRACTION-PROSUMA-ASTEN
[fofana@proextrasten API-EXTRACTION-PROSUMA-ASTEN]$ ./run_api_extraction.sh

🐧 Système détecté: Linux (redhat-dnf)

🔧 Vérification des dépendances système...
   📦 Distribution: Red Hat/CentOS/Fedora (dnf)
   ✅ cifs-utils déjà installé

✅ Installation locale trouvée: /home/fofana/API-EXTRACTION-PROSUMA-ASTEN

============================================================
           API EXTRACTION PROSUMA - EXTRACTEUR UNIFIÉ
============================================================

...
[Lancement direct de l'extracteur]
```

---

## 💡 Conseils pro

### Pour Red Hat / CentOS

```bash
# Vérifier votre version de Red Hat
cat /etc/redhat-release

# Vérifier que dnf est disponible
command -v dnf && echo "dnf disponible" || echo "utiliser yum"

# Voir les logs d'exécution
tail -f ~/extraction.log
```

### Pour automatisation complète

```bash
# Script cron avec notification email
0 8 * * * cd ~/API-EXTRACTION-PROSUMA-ASTEN && ./run_commande_reassort.sh >> ~/logs/extraction.log 2>&1 || echo "Erreur extraction" | mail -s "Erreur API Extraction" votre@email.com
```

---

## 📞 Support

### En cas de problème

1. **Vérifiez les logs**
   ```bash
   cat ~/extraction.log
   ```

2. **Vérifiez la détection OS**
   ```bash
   echo $OSTYPE
   cat /etc/redhat-release  # Sur Red Hat
   ```

3. **Installation manuelle de cifs-utils si échec auto**
   ```bash
   sudo dnf install -y cifs-utils      # Red Hat 8+
   sudo yum install -y cifs-utils      # Red Hat 7
   sudo apt-get install -y cifs-utils  # Ubuntu
   ```

4. **Réinstallation propre**
   ```bash
   rm -rf ~/API-EXTRACTION-PROSUMA-ASTEN
   ./run_api_extraction.sh
   ```

---

## ✅ Checklist de vérification

- [ ] Script exécutable : `chmod +x run_api_extraction.sh`
- [ ] Python installé : `python3 --version`
- [ ] Lancement réussi : `./run_api_extraction.sh`
- [ ] Installation locale créée : `ls ~/API-EXTRACTION-PROSUMA-ASTEN`
- [ ] Extracteur fonctionnel : Tester une extraction
- [ ] Cron configuré (optionnel) : `crontab -l`

---

**🎉 Version 3.0 - TOUT-EN-UN avec auto-configuration !**

**👽 Créé par Alien pour ASTEN - API Extraction Prosuma**  
**📅 26 Novembre 2025**  
**🚀 Un seul script, zéro configuration manuelle !**

