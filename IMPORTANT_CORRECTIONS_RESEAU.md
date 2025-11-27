# 🔧 CORRECTIONS IMPORTANTES - ÉCRITURE DIRECTE SUR RÉSEAU

## ✅ Modifications apportées

1. **Écriture DIRECTE sur le réseau** (plus de fichier local)
2. **Forcer `/mnt/share/FOFANA` sur Linux** (ignorer `config.env`)
3. **Supprimer le dossier EXPORT local**

---

## 🚀 ACTIONS À FAIRE SUR LE SERVEUR LINUX

### 1️⃣ Faire le `git pull`

```bash
cd ~/API-EXTRACTION-PROSUMA-ASTEN
git pull
```

### 2️⃣ Vérifier que le partage SMB est monté

```bash
mount | grep /mnt/share
```

**Résultat attendu :**
```
//10.0.70.169/SHARE on /mnt/share type cifs (rw,relatime,vers=3.0,...)
```

**Si le partage N'EST PAS monté :**
```bash
sudo mount -t cifs //10.0.70.169/SHARE /mnt/share -o username=ifofana,password='        @Al',domain=PROSUMA,uid=$(id -u),gid=$(id -g),vers=3.0
```

### 3️⃣ Vérifier que le dossier ASTEN existe sur le réseau

```bash
ls -la /mnt/share/FOFANA/
ls -la "/mnt/share/FOFANA/Etats Natacha/Commande/PRESENTATION_COMMANDE/"
```

**Créer le dossier ASTEN si nécessaire :**
```bash
mkdir -p "/mnt/share/FOFANA/Etats Natacha/Commande/PRESENTATION_COMMANDE/ASTEN"
```

### 4️⃣ Supprimer le dossier EXPORT local (erreurs précédentes)

```bash
cd ~/API-EXTRACTION-PROSUMA-ASTEN/API_COMMANDE_REASSORT
# Lister le contenu
ls -la EXPORT/

# Supprimer tout le dossier EXPORT (ancien système)
rm -rf EXPORT/

# Vérifier
ls -la
```

### 5️⃣ Relancer l'extraction

```bash
cd ~/API-EXTRACTION-PROSUMA-ASTEN
./run_commande_reassort.sh
```

---

## 🔍 Vérification des fichiers CSV sur le réseau

### Depuis le serveur Linux :

```bash
# Lister tous les sous-dossiers dans ASTEN
ls -la "/mnt/share/FOFANA/Etats Natacha/Commande/PRESENTATION_COMMANDE/ASTEN/"

# Exemple : Vérifier le dossier CKM
ls -la "/mnt/share/FOFANA/Etats Natacha/Commande/PRESENTATION_COMMANDE/ASTEN/CKM/"

# Exemple : Vérifier le dossier MBADON
ls -la "/mnt/share/FOFANA/Etats Natacha/Commande/PRESENTATION_COMMANDE/ASTEN/MBADON/"
```

### Depuis Windows :

1. Ouvrir l'explorateur Windows
2. Aller à : `\\10.0.70.169\share\FOFANA\Etats Natacha\Commande\PRESENTATION_COMMANDE\ASTEN`
3. Vérifier que chaque sous-dossier (CKM, MBADON, SOL BENI, etc.) contient les fichiers CSV

---

## ⚠️ En cas de problème

### Erreur : "Le partage SMB n'est PAS monté"

**Solution :**
```bash
sudo mount -t cifs //10.0.70.169/SHARE /mnt/share -o username=ifofana,password='        @Al',domain=PROSUMA,uid=$(id -u),gid=$(id -g),vers=3.0
```

### Erreur : "Permission denied"

**Vérifier les permissions du point de montage :**
```bash
ls -ld /mnt/share
```

**Solution :**
```bash
sudo umount /mnt/share
sudo mount -t cifs //10.0.70.169/SHARE /mnt/share -o username=ifofana,password='        @Al',domain=PROSUMA,uid=$(id -u),gid=$(id -g),vers=3.0
```

### Les fichiers ne s'affichent pas sur Windows

**Attendre quelques secondes** puis **rafraîchir** (F5) dans l'explorateur Windows.

Si toujours rien :
```bash
# Sur le serveur Linux, vérifier que les fichiers existent
ls -la "/mnt/share/FOFANA/Etats Natacha/Commande/PRESENTATION_COMMANDE/ASTEN/"
```

---

## 📊 Exemple de sortie attendue

```
2025-11-27 14:22:07,908 - INFO - [OK] 14 commandes réassort récupérées au total
2025-11-27 14:22:07,908 - INFO - [EXPORT] EXPORT CSV - MAGASIN 292
2025-11-27 14:22:07,909 - INFO - ✅ Dossier réseau trouvé/créé: /mnt/share/FOFANA/Etats Natacha/Commande/PRESENTATION_COMMANDE/ASTEN/CKM
2025-11-27 14:22:07,911 - INFO - ✅✅✅ FICHIER CRÉÉ DIRECTEMENT SUR LE RÉSEAU ✅✅✅
2025-11-27 14:22:07,911 - INFO -    📁 Chemin: /mnt/share/FOFANA/Etats Natacha/Commande/PRESENTATION_COMMANDE/ASTEN/CKM/export_commande_reassort_292_20251127_142207.csv
2025-11-27 14:22:07,911 - INFO -    📊 14 commandes réassort exportées
2025-11-27 14:22:07,911 - INFO -    📊 Taille: 3,616 octets
```

**IMPORTANT:** Les chemins doivent commencer par `/mnt/share/` (Linux) et NON par `\\10.0.70.169\share\` (Windows)

---

## ✅ Résumé

- ✅ Le code écrit maintenant **DIRECTEMENT** sur le réseau
- ✅ Plus de fichiers locaux dans `EXPORT/`
- ✅ Utilise `/mnt/share/FOFANA/...` sur Linux
- ✅ Les fichiers sont accessibles depuis Windows via `\\10.0.70.169\share\...`

