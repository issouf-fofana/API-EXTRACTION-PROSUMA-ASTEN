# 🚀 Guide de démarrage rapide - API Extraction Prosuma

## ⚡ Démarrage ultra-rapide

### Sur Windows 🪟

```bash
# Double-cliquez sur :
run_api_extraction.sh
# OU
./run_api_extraction.sh
```

### Sur Linux 🐧

```bash
# 1. Installation (première fois uniquement)
chmod +x setup_linux_local.sh
./setup_linux_local.sh

# 2. Utilisation
cd ~/API-EXTRACTION-PROSUMA-ASTEN
chmod +x run_api_extraction.sh
./run_api_extraction.sh
```

### Sur macOS 🍎

```bash
# Si le partage réseau est monté :
./run_api_extraction.sh

# Sinon, copiez le code localement d'abord
```

---

## 🎯 Que fait le script automatiquement ?

Le script détecte votre OS et :

### ✅ Windows
- Utilise le chemin réseau UNC : `//10.0.70.169/share/...`
- Fonctionne directement sans configuration

### ✅ Linux
- Cherche le code local : `~/API-EXTRACTION-PROSUMA-ASTEN`
- Sinon, cherche un montage : `/mnt/share/...`
- Sinon, utilise le dossier courant

### ✅ macOS
- Cherche le volume : `/Volumes/share/...`
- Sinon, cherche le code local : `~/API-EXTRACTION-PROSUMA-ASTEN`

---

## 📋 Résolution de problèmes en 3 étapes

### Problème : "Le dossier réseau n'est pas accessible"

**Solution selon votre OS :**

#### Windows
```bash
# Vérifiez que le partage est accessible
explorer \\10.0.70.169\share

# OU mappez un lecteur réseau (Z:) puis :
cd /z/FOFANA/Etats\ Natacha/SCRIPT/EXTRACTION_PROSUMA
./run_api_extraction.sh
```

#### Linux
```bash
# Option 1 : Installation locale (RECOMMANDÉ)
chmod +x setup_linux_local.sh
./setup_linux_local.sh

# Option 2 : Montage réseau
chmod +x setup_linux_mount.sh
./setup_linux_mount.sh
```

#### macOS
```bash
# Dans le Finder : Aller > Se connecter au serveur
# smb://10.0.70.169/share
# Puis :
cd /Volumes/share/FOFANA/Etats\ Natacha/SCRIPT/EXTRACTION_PROSUMA
./run_api_extraction.sh
```

---

## 🎨 Scripts disponibles

| Script | Description | Quand l'utiliser |
|--------|-------------|------------------|
| `run_api_extraction.sh` | Menu interactif, toutes les APIs | Usage manuel |
| `run_commande_reassort.sh` | Extraction automatique réassort | Planification (cron/task scheduler) |
| `setup_linux_local.sh` | Installation locale sur Linux | Première installation Linux |
| `setup_linux_mount.sh` | Montage réseau sur Linux | Si vous préférez le réseau |
| `config_paths.sh` | Configuration des chemins | Personnalisation |

---

## 📁 Configuration personnalisée

Si vos chemins sont différents, éditez `config_paths.sh` :

```bash
nano config_paths.sh  # Linux/macOS
notepad config_paths.sh  # Windows
```

Modifiez selon vos besoins :

```bash
# Linux
LINUX_LOCAL_PATH="$HOME/MON_CHEMIN_PERSO"

# Windows
WINDOWS_UNC_PATH="//MON_SERVEUR/mon_partage/..."
```

---

## 🔄 Workflow typique

### Utilisation manuelle (tous les jours)

```bash
# Windows
./run_api_extraction.sh
# Choisir l'option → Sélectionner dates → Go!

# Linux
cd ~/API-EXTRACTION-PROSUMA-ASTEN
./run_api_extraction.sh
```

### Utilisation automatique (planifiée)

**Linux (cron) :**
```bash
# Exécuter tous les jours à 8h00
crontab -e
# Ajouter :
0 8 * * * cd ~/API-EXTRACTION-PROSUMA-ASTEN && ./run_commande_reassort.sh >> ~/extraction.log 2>&1
```

**Windows (Task Scheduler) :**
```powershell
# Créer une tâche planifiée qui exécute :
C:\Windows\System32\bash.exe -c "cd //10.0.70.169/share/... && ./run_commande_reassort.sh"
```

---

## 📊 Où trouver les fichiers CSV ?

Les exports sont sauvegardés dans :

```
Réseau partagé:
└── //10.0.70.169/share/FOFANA/EXPORT/
    ├── EXPORT_COMMANDE/
    ├── EXPORT_COMMANDE_DIRECTE/
    ├── EXPORT_COMMANDE_REASSORT/
    ├── EXPORT_BASE_ARTICLE/
    ├── EXPORT_ARTICLE_PROMO/
    ├── EXPORT_PROMO/
    ├── EXPORT_PRODUIT_NON_TROUVE/
    ├── EXPORT_COMMANDE_THEME/
    ├── EXPORT_RECEPTION/
    ├── EXPORT_PRE_COMMANDE/
    ├── EXPORT_RETOUR_MARCHANDISE/
    ├── EXPORT_INVENTAIRE/
    ├── EXPORT_STATS_VENTE/
    └── EXPORT_MOUVEMENT_STOCK/
```

---

## 💡 Astuces pro

### 1. Exécution silencieuse (sans interaction)

```bash
# Définir les dates via variables d'environnement
export USE_DEFAULT_DATES="true"
./run_api_extraction.sh
```

### 2. Filtrer par statut

```bash
# Pour les commandes en attente uniquement
export STATUT_COMMANDE="en attente de livraison"
./run_commande_reassort.sh
```

### 3. Personnaliser les dates

```bash
export USE_DEFAULT_DATES="false"
export CUSTOM_START_DATE="2025-01-01"
export CUSTOM_END_DATE="2025-01-15"
./run_api_extraction.sh
```

### 4. Logs détaillés

```bash
# Rediriger la sortie vers un fichier log
./run_api_extraction.sh 2>&1 | tee extraction_$(date +%Y%m%d).log
```

---

## 🆘 Aide rapide

### Le script ne démarre pas

```bash
# Sur Linux/macOS, assurez-vous qu'il est exécutable
chmod +x run_api_extraction.sh

# Ou exécutez avec bash explicitement
bash run_api_extraction.sh
```

### Python introuvable

```bash
# Installer Python 3.8+
# Ubuntu/Debian
sudo apt-get install python3 python3-venv python3-pip

# Windows : Téléchargez depuis https://python.org
```

### Erreur de permissions

```bash
# Linux : Donnez les permissions
chmod -R 755 ~/API-EXTRACTION-PROSUMA-ASTEN

# Windows : Exécutez en tant qu'administrateur
```

---

## 🎓 Ressources supplémentaires

- **Documentation complète** : `README_LINUX.md`
- **API spécifiques** : `API_*/README.md`
- **Permissions** : `README_PERMISSIONS.md`
- **Configuration** : `config_paths.sh`

---

## 📞 Support

En cas de problème :
1. Vérifiez que vous êtes sur le bon OS
2. Consultez les logs
3. Relancez l'installation locale (Linux)
4. Contactez Alien 👽

---

**🚀 Créé avec ❤️ par Alien pour ASTEN - API Extraction Prosuma**

