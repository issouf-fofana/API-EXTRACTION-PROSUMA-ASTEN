# 📋 CONFIGURATION DU PARTAGE RÉSEAU SUR LINUX

## ✅ MODIFICATIONS APPLIQUÉES

Le code Python a été modifié pour **détecter automatiquement l'OS** et utiliser le bon format de chemin :

### 🪟 Windows
- Chemin : `\\10.0.70.169\share\FOFANA\Etats Natacha\Commande\PRESENTATION_COMMANDE\ASTEN\{MAGASIN}`
- Format automatique : backslashes `\`

### 🐧 Linux
- Chemin : `/mnt/share/FOFANA/Etats Natacha/Commande/PRESENTATION_COMMANDE/ASTEN/{MAGASIN}`
- Format automatique : slashes `/`

### 🍎 macOS
- Chemin : `/Volumes/share/FOFANA/Etats Natacha/Commande/PRESENTATION_COMMANDE/ASTEN/{MAGASIN}`
- Format automatique : slashes `/`

---

## 🔧 CONFIGURATION NÉCESSAIRE SUR LINUX

Pour que l'extraction fonctionne correctement sur Linux, vous devez **monter le partage SMB Windows** :

### 1️⃣ Installation des outils (déjà géré par le script .sh)

Le script `run_commande_reassort.sh` installe automatiquement `cifs-utils` selon votre distribution :
- **Red Hat/CentOS/Fedora** : `sudo dnf install cifs-utils`
- **Debian/Ubuntu** : `sudo apt-get install cifs-utils`

### 2️⃣ Montage manuel du partage (UNE SEULE FOIS)

#### Option A : Montage simple (demande le mot de passe à chaque fois)

```bash
# Créer le point de montage
sudo mkdir -p /mnt/share

# Monter le partage SMB
sudo mount -t cifs //10.0.70.169/share /mnt/share -o username=VOTRE_USERNAME
```

#### Option B : Montage automatique au démarrage (recommandé pour le serveur)

**1. Créer un fichier de credentials :**

```bash
sudo nano /root/.smbcredentials
```

**2. Ajouter vos identifiants :**

```
username=VOTRE_USERNAME
password=VOTRE_MOT_DE_PASSE
```

**3. Sécuriser le fichier :**

```bash
sudo chmod 600 /root/.smbcredentials
```

**4. Modifier /etc/fstab :**

```bash
sudo nano /etc/fstab
```

**5. Ajouter cette ligne à la fin :**

```
//10.0.70.169/share  /mnt/share  cifs  credentials=/root/.smbcredentials,uid=1000,gid=1000,iocharset=utf8  0  0
```

**6. Monter immédiatement :**

```bash
sudo mount -a
```

**7. Vérifier que ça fonctionne :**

```bash
ls -la /mnt/share/FOFANA/
```

---

## 📊 STRUCTURE DES DOSSIERS SUR LE RÉSEAU

Après l'extraction, les fichiers CSV seront automatiquement enregistrés dans :

```
/mnt/share/FOFANA/Etats Natacha/Commande/PRESENTATION_COMMANDE/ASTEN/
├── AGEN/
│   └── commande_reassort_AGEN_20251126.csv
├── AUCH/
│   └── commande_reassort_AUCH_20251126.csv
├── BORDEAUX/
│   └── commande_reassort_BORDEAUX_20251126.csv
└── ... (un dossier par magasin)
```

**⚠️ Important :** Le script crée automatiquement les dossiers manquants si le partage est monté correctement.

---

## 🧪 VÉRIFICATION RAPIDE

Pour vérifier que tout fonctionne, exécutez ces commandes sur votre serveur Linux :

```bash
# 1. Vérifier que cifs-utils est installé
rpm -qa | grep cifs-utils  # Red Hat/CentOS
# ou
dpkg -l | grep cifs-utils  # Debian/Ubuntu

# 2. Vérifier que le partage est monté
mount | grep "/mnt/share"

# 3. Vérifier l'accès au dossier ASTEN
ls -la "/mnt/share/FOFANA/Etats Natacha/Commande/PRESENTATION_COMMANDE/ASTEN/"

# 4. Tester l'écriture
touch "/mnt/share/FOFANA/Etats Natacha/Commande/PRESENTATION_COMMANDE/ASTEN/.test"
rm "/mnt/share/FOFANA/Etats Natacha/Commande/PRESENTATION_COMMANDE/ASTEN/.test"
```

---

## ❓ DÉPANNAGE

### Problème : "Le dossier réseau n'est pas accessible"

**Solution :** Vérifiez que le partage est bien monté :
```bash
mount | grep "/mnt/share"
```

Si vide, montez le partage :
```bash
sudo mount -t cifs //10.0.70.169/share /mnt/share -o username=VOTRE_USERNAME
```

### Problème : "Permission denied"

**Solution :** Vérifiez les permissions du point de montage :
```bash
sudo chmod 777 /mnt/share
```

Ou montez avec l'option uid/gid :
```bash
sudo mount -t cifs //10.0.70.169/share /mnt/share -o username=VOTRE_USERNAME,uid=$(id -u),gid=$(id -g)
```

### Problème : "Host is down" ou "Connection refused"

**Solution :** Vérifiez que le serveur Windows est accessible :
```bash
ping 10.0.70.169
```

---

## 📝 RÉSUMÉ DES CHANGEMENTS DANS LE CODE

### Fichiers modifiés :
1. **`API_COMMANDE_REASSORT/api_commande_reassort.py`**
   - Ajout de la fonction `get_os_type()` pour détecter l'OS
   - Adaptation des chemins dans `__init__()` selon l'OS
   - Modification de `get_network_path_for_shop()` pour gérer Linux/macOS/Windows
   - Modification de `get_log_network_path()` pour gérer Linux/macOS/Windows
   - Modification de `extract_all()` pour afficher l'OS détecté

2. **`config.env`**
   - Ajout de commentaires pour expliquer les chemins multi-OS

---

## 🚀 PROCÉDURE DE DÉPLOIEMENT

**Sur votre PC Windows :**
```bash
git add .
git commit -m "Adaptation multi-OS pour les exports réseau vers ASTEN/{MAGASIN}"
git push
```

**Sur votre serveur Linux :**
```bash
cd /home/ifofana/API-EXTRACTION-PROSUMA-ASTEN
git pull

# Tester immédiatement
./run_commande_reassort.sh
```

---

## ✅ CRON JOB CONFIGURÉ

Le cron job est déjà configuré pour s'exécuter tous les jours à **13h40** :
```cron
40 13 * * * cd /home/ifofana/API-EXTRACTION-PROSUMA-ASTEN && ./run_commande_reassort.sh >> /home/ifofana/logs/extraction_$(date +\%Y\%m\%d).log 2>&1
```

Les logs d'extraction sont conservés dans `/home/ifofana/logs/`.

---

**📞 En cas de problème, vérifiez d'abord que le montage SMB fonctionne correctement !**

