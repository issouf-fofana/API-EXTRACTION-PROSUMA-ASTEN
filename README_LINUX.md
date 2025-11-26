# Guide d'installation et d'utilisation sur Linux

Ce guide vous explique comment configurer et utiliser l'extracteur API Prosuma sur un serveur Linux.

## 🐧 Configuration sur Linux

Sur Linux, les chemins réseau Windows UNC (`//10.0.70.169/...`) ne fonctionnent pas directement. Vous avez **deux options** :

### Option 1 : Installation locale (RECOMMANDÉ) ✅

Copiez le code sur votre serveur Linux pour un accès rapide et sans dépendance réseau.

#### Étape 1 : Rendre le script exécutable

```bash
chmod +x setup_linux_local.sh
```

#### Étape 2 : Lancer l'installation

```bash
./setup_linux_local.sh
```

Le script va :
- Créer le dossier `~/API-EXTRACTION-PROSUMA-ASTEN`
- Copier tous les fichiers nécessaires
- Vérifier l'installation

#### Étape 3 : Utiliser l'extracteur

```bash
cd ~/API-EXTRACTION-PROSUMA-ASTEN
chmod +x run_api_extraction.sh run_commande_reassort.sh
./run_api_extraction.sh
```

### Option 2 : Montage réseau SMB/CIFS

Montez le partage réseau Windows directement sur Linux.

#### Étape 1 : Installer cifs-utils

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y cifs-utils

# CentOS/RHEL
sudo yum install -y cifs-utils

# Fedora
sudo dnf install -y cifs-utils
```

#### Étape 2 : Rendre le script exécutable

```bash
chmod +x setup_linux_mount.sh
```

#### Étape 3 : Monter le partage

```bash
./setup_linux_mount.sh
```

Le script va demander :
- Votre nom d'utilisateur réseau
- Votre mot de passe

#### Étape 4 : Utiliser l'extracteur

```bash
# Le code sera accessible à /mnt/share/FOFANA/...
./run_api_extraction.sh
```

#### Montage automatique au démarrage (optionnel)

Pour monter automatiquement le partage au démarrage, créez un fichier credentials :

```bash
sudo nano /etc/smbcredentials
```

Ajoutez vos identifiants :

```
username=VOTRE_USERNAME
password=VOTRE_PASSWORD
```

Protégez le fichier :

```bash
sudo chmod 600 /etc/smbcredentials
```

Ajoutez dans `/etc/fstab` :

```bash
//10.0.70.169/share/FOFANA/Etats Natacha/SCRIPT/EXTRACTION_PROSUMA /mnt/share/FOFANA/Etats Natacha/SCRIPT/EXTRACTION_PROSUMA cifs credentials=/etc/smbcredentials,uid=1000,gid=1000,file_mode=0755,dir_mode=0755 0 0
```

Testez le montage :

```bash
sudo mount -a
```

## 🔧 Configuration personnalisée

Si vos chemins sont différents, éditez `config_paths.sh` :

```bash
nano config_paths.sh
```

Modifiez les variables selon votre environnement :

```bash
# Chemin local sur Linux
LINUX_LOCAL_PATH="$HOME/API-EXTRACTION-PROSUMA-ASTEN"

# Point de montage réseau
LINUX_MOUNT_PATH="/mnt/share/FOFANA/Etats Natacha/SCRIPT/EXTRACTION_PROSUMA"

# Informations réseau
NETWORK_IP="10.0.70.169"
NETWORK_SHARE="share"
NETWORK_PATH="FOFANA/Etats Natacha/SCRIPT/EXTRACTION_PROSUMA"
```

## 🚀 Utilisation

### Script interactif (menu)

```bash
./run_api_extraction.sh
```

### Script automatique (commandes réassort)

```bash
./run_commande_reassort.sh
```

### Planification avec cron

Pour exécuter automatiquement tous les jours à 8h00 :

```bash
# Éditer la crontab
crontab -e

# Ajouter cette ligne
0 8 * * * cd ~/API-EXTRACTION-PROSUMA-ASTEN && ./run_commande_reassort.sh >> ~/extraction.log 2>&1
```

## 🐛 Dépannage

### Erreur : "Le dossier réseau partagé n'est pas accessible"

**Cause** : Le script ne trouve pas le code source.

**Solutions** :
1. Utilisez l'installation locale (Option 1, recommandé)
2. Vérifiez que le partage est monté : `mount | grep share`
3. Vérifiez les chemins dans `config_paths.sh`
4. Exécutez depuis le dossier du projet : `cd ~/API-EXTRACTION-PROSUMA-ASTEN`

### Erreur : "mount error(13): Permission denied"

**Cause** : Identifiants incorrects ou permissions insuffisantes.

**Solutions** :
1. Vérifiez vos identifiants réseau
2. Vérifiez que vous avez accès au partage depuis Windows
3. Contactez votre administrateur réseau

### Erreur : "bash: ./run_api_extraction.sh: Permission denied"

**Cause** : Le script n'est pas exécutable.

**Solution** :
```bash
chmod +x run_api_extraction.sh run_commande_reassort.sh
chmod +x setup_linux_*.sh config_paths.sh
```

### Le script détecte mal l'OS

**Solution** : Forcez la détection en exportant une variable :

```bash
export OSTYPE="linux-gnu"
./run_api_extraction.sh
```

### Environnement virtuel Python ne se crée pas

**Cause** : Module venv manquant.

**Solution** :
```bash
# Ubuntu/Debian
sudo apt-get install python3-venv

# CentOS/RHEL
sudo yum install python3-virtualenv
```

## 📊 Structure des chemins

### Chemin détecté sur Linux
```
🐧 Système détecté: Linux
   → Utilisation du chemin local: /home/fofana/API-EXTRACTION-PROSUMA-ASTEN
```

### Chemin détecté sur Windows
```
🪟 Système détecté: Windows
   → Utilisation du chemin réseau UNC: //10.0.70.169/share/...
```

### Chemin détecté sur macOS
```
🍎 Système détecté: macOS
   → Utilisation du volume réseau: /Volumes/share/...
```

## 🔄 Mise à jour du code

### Installation locale

Relancez simplement l'installation :

```bash
./setup_linux_local.sh
```

Ou copiez manuellement les nouveaux fichiers :

```bash
rsync -av --delete /source/path/ ~/API-EXTRACTION-PROSUMA-ASTEN/
```

### Montage réseau

Le code est toujours à jour automatiquement car il pointe vers le réseau.

## 📝 Logs et exports

### Localisation des exports

Les fichiers CSV sont exportés vers :
- **Réseau** : `/mnt/share/FOFANA/EXPORT/` (si monté)
- **Local** : `~/API-EXTRACTION-PROSUMA-ASTEN/EXPORT_*/`

### Logs d'exécution

```bash
# Voir les derniers logs
tail -f ~/extraction.log

# Voir tous les logs
less ~/extraction.log
```

## 💡 Conseils

1. **Préférez l'installation locale** pour de meilleures performances
2. **Sauvegardez** votre `config.env` avant mise à jour
3. **Utilisez cron** pour les extractions automatiques
4. **Vérifiez les logs** régulièrement
5. **Testez d'abord** avec un seul magasin

## 🆘 Support

En cas de problème :
1. Vérifiez les logs : `~/extraction.log`
2. Vérifiez la connectivité : `ping 10.0.70.169`
3. Vérifiez Python : `python3 --version`
4. Contactez Alien (créateur du script)

---

**Créé par Alien pour l'extraction des APIs Prosuma ASTEN** 🚀

