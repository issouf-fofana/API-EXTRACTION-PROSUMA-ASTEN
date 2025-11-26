# 🚀 COMMANDES À EXÉCUTER SUR LE SERVEUR LINUX

## 📋 PROBLÈME ACTUEL

Les fichiers CSV sont enregistrés localement dans `/home/ifofana/API-EXTRACTION-PROSUMA-ASTEN/API_COMMANDE_REASSORT/EXPORT/`  
au lieu d'être envoyés sur le partage réseau `\\10.0.70.169\share\FOFANA\...`

**Cause:** Le partage SMB Windows n'est PAS monté sur le serveur Linux.

---

## 🔧 ÉTAPE 1 : NETTOYER LES DOSSIERS LOCAUX BIZARRES

```bash
cd ~/API-EXTRACTION-PROSUMA-ASTEN
rm -rf '\\10.0.70.169\share\FOFANA'
rm -rf '\\10.0.70.169\share\FOFANA\Etats Natacha\Commande\PRESENTATION_COMMANDE\ASTEN'
rm -rf '\\10.0.70.169\share\FOFANA\Etats Natacha\SCRIPT\LOG'
```

---

## 🔧 ÉTAPE 2 : VÉRIFIER SI LE PARTAGE EST ACCESSIBLE

```bash
# Tester la connectivité
ping -c 3 10.0.70.169

# Tester si SMB est accessible
smbclient -L 10.0.70.169 -N
```

---

## 🔧 ÉTAPE 3 : MONTER LE PARTAGE SMB

### Option A : Montage temporaire (pour tester)

```bash
# Créer le point de montage
sudo mkdir -p /mnt/share

# Monter le partage (remplacez USERNAME et PASSWORD)
sudo mount -t cifs //10.0.70.169/share /mnt/share -o username=VOTRE_USERNAME,password=VOTRE_MOT_DE_PASSE
```

### Option B : Montage permanent (recommandé)

**1. Créer un fichier de credentials sécurisé :**

```bash
sudo nano /root/.smbcredentials
```

**Contenu du fichier :**
```
username=VOTRE_USERNAME
password=VOTRE_MOT_DE_PASSE
```

**2. Sécuriser le fichier :**

```bash
sudo chmod 600 /root/.smbcredentials
```

**3. Modifier /etc/fstab pour montage automatique :**

```bash
sudo nano /etc/fstab
```

**Ajouter cette ligne à la fin :**
```
//10.0.70.169/share  /mnt/share  cifs  credentials=/root/.smbcredentials,uid=1000,gid=1000,iocharset=utf8,_netdev  0  0
```

**4. Monter immédiatement :**

```bash
sudo mount -a
```

---

## 🔧 ÉTAPE 4 : VÉRIFIER QUE LE MONTAGE FONCTIONNE

```bash
# Vérifier que le partage est monté
mount | grep "/mnt/share"

# Lister le contenu du dossier ASTEN
ls -la "/mnt/share/FOFANA/Etats Natacha/Commande/PRESENTATION_COMMANDE/ASTEN/"

# Tester l'écriture
touch "/mnt/share/FOFANA/Etats Natacha/Commande/PRESENTATION_COMMANDE/ASTEN/.test"
rm "/mnt/share/FOFANA/Etats Natacha/Commande/PRESENTATION_COMMANDE/ASTEN/.test"

# Si succès : vous pouvez écrire !
echo "✅ Montage SMB OK !"
```

---

## 🔧 ÉTAPE 5 : RELANCER L'EXTRACTION

Une fois le partage monté, relancez le script :

```bash
cd ~/API-EXTRACTION-PROSUMA-ASTEN
./run_commande_reassort.sh
```

Les fichiers CSV seront automatiquement copiés vers :
```
/mnt/share/FOFANA/Etats Natacha/Commande/PRESENTATION_COMMANDE/ASTEN/{MAGASIN}/
```

Ce qui correspond sur Windows à :
```
\\10.0.70.169\share\FOFANA\Etats Natacha\Commande\PRESENTATION_COMMANDE\ASTEN\{MAGASIN}\
```

---

## 📊 VÉRIFIER LES FICHIERS SUR LE RÉSEAU

### Sur le serveur Linux :

```bash
ls -lh "/mnt/share/FOFANA/Etats Natacha/Commande/PRESENTATION_COMMANDE/ASTEN/"
```

### Sur Windows (Explorateur de fichiers) :

Ouvrir :
```
\\10.0.70.169\share\FOFANA\Etats Natacha\Commande\PRESENTATION_COMMANDE\ASTEN\
```

Vous devriez voir les dossiers :
- CUV7DEC/
- MBADON/
- CASH IVOIRE U LATRILLE/
- etc.

---

## ❓ DÉPANNAGE

### Erreur : "mount error(13): Permission denied"

**Solution :** Vérifiez le nom d'utilisateur et le mot de passe dans `.smbcredentials`

### Erreur : "Host is down"

**Solution :** Vérifiez que le serveur Windows est accessible :
```bash
ping 10.0.70.169
```

### Erreur : "No such file or directory"

**Solution :** Créez le point de montage :
```bash
sudo mkdir -p /mnt/share
```

---

## 🎯 RÉSUMÉ DES COMMANDES ESSENTIELLES

```bash
# 1. Nettoyer les dossiers locaux bizarres
cd ~/API-EXTRACTION-PROSUMA-ASTEN
rm -rf '\\10.0.70.169\share\FOFANA'

# 2. Monter le partage SMB
sudo mkdir -p /mnt/share
sudo mount -t cifs //10.0.70.169/share /mnt/share -o username=VOTRE_USERNAME,password=VOTRE_MOT_DE_PASSE

# 3. Vérifier
mount | grep "/mnt/share"
ls -la "/mnt/share/FOFANA/Etats Natacha/Commande/PRESENTATION_COMMANDE/ASTEN/"

# 4. Relancer l'extraction
cd ~/API-EXTRACTION-PROSUMA-ASTEN
./run_commande_reassort.sh
```

---

**⚠️ IMPORTANT :** Sans le montage SMB, tous les fichiers resteront locaux dans `~/API-EXTRACTION-PROSUMA-ASTEN/API_COMMANDE_REASSORT/EXPORT/`

