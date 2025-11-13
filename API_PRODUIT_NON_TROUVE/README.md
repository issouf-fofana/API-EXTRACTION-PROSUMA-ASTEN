# Extracteur API Prosuma - Produits Non Trouvés

Ce script permet d'extraire les événements de produits non trouvés des magasins Prosuma via l'API `event_line`.

## 🚀 Fonctionnalités

- **Extraction complète** : Récupère tous les événements de produits non trouvés avec pagination automatique
- **Multi-magasins** : Traite tous les magasins configurés simultanément
- **Filtrage intelligent** : Identifie automatiquement les événements liés aux produits non trouvés
- **Export CSV** : Génère des fichiers CSV avec toutes les informations des événements
- **Envoi réseau** : Copie automatiquement les fichiers vers le dossier partagé
- **Gestion d'erreurs** : Continue même si certains magasins échouent

## 📋 Prérequis

- Python 3.7 ou supérieur
- Accès réseau aux serveurs Prosuma
- Identifiants de connexion valides

## ⚙️ Configuration

### 1. Fichier `config.env`

```env
# Identifiants de connexion
PROSUMA_USER=votre_utilisateur
PROSUMA_PASSWORD=votre_mot_de_passe

# Magasins à traiter (codes séparés par des virgules)
SHOP_CODES=230,292,294,364,415

# Mapping des magasins (format: code:nom,code:nom)
SHOP_MAPPING=230:PRIMA,292:CKM,294:SOL BENI,364:CUV7DEC,415:MBADON

# Dossier de destination réseau
DOWNLOAD_FOLDER=//10.0.70.169/share/FOFANA/Etats Natacha/Commande/PRESENTATION_COMMANDE/ASTEN
```

### 2. Fichier `magasins.json`

Contient les URLs des serveurs pour chaque magasin :

```json
{
  "230": {
    "url": "https://pos3-prod-prosuma.prosuma.pos",
    "name": "PRIMA"
  },
  "292": {
    "url": "https://pos9-prod-prosuma.prosuma.pos",
    "name": "CKM"
  }
}
```

## 🖥️ Utilisation

### Sur Windows

1. Double-cliquer sur `run_api_produit_non_trouve.bat`
2. Le script va :
   - Créer l'environnement virtuel si nécessaire
   - Installer les dépendances
   - Lancer l'extraction
   - Copier les fichiers vers le réseau

### Sur macOS/Linux

```bash
# Installation des dépendances
pip install -r requirements.txt

# Lancement de l'extraction
python3 api_produit_non_trouve.py
```

## 📊 Données extraites

Le script extrait les informations suivantes pour chaque événement de produit non trouvé :

- **Informations de base** : ID, type d'événement, description
- **Date et heure** : Date de l'événement, création, modification
- **Informations du ticket** : Numéro, série, ID, code barre/EAN
- **Personnel** : Caissier, formation, garant
- **Métadonnées** : Extras, statut de suppression

## 🔍 Filtrage des événements

Le script filtre automatiquement les événements liés aux produits non trouvés en recherchant ces mots-clés :

- "produit non trouvé"
- "product not found"
- "code inconnu"
- "unknown code"
- "ean inconnu"
- "unknown ean"
- "code barre inconnu"
- "unknown barcode"
- "produit introuvable"
- "code invalide"
- "invalid code"
- "scan error"
- "erreur scan"
- "barcode error"
- "erreur code barre"

## 📁 Structure des fichiers

```
API_PRODUIT_NON_TROUVE/
├── api_produit_non_trouve.py              # Script principal
├── config.env                             # Configuration
├── magasins.json                          # URLs des serveurs
├── requirements.txt                       # Dépendances Python
├── run_api_produit_non_trouve.bat         # Script Windows
├── README.md                              # Documentation
├── copy_to_network.sh                     # Script de synchronisation
└── EXPORT_PRODUIT_NON_TROUVE/             # Dossier des exports locaux
    └── export_produit_non_trouve_XXX_YYYYMMDD_HHMMSS.csv
```

## 🔧 Dépannage

### Erreur de connexion
- Vérifier les identifiants dans `config.env`
- Vérifier la connectivité réseau aux serveurs Prosuma

### Erreur de permissions
- Vérifier l'accès en écriture au dossier partagé
- Exécuter en tant qu'administrateur si nécessaire

### Magasin non trouvé
- Vérifier que le code magasin existe dans `magasins.json`
- Vérifier que l'utilisateur a accès à ce magasin

### Aucun événement trouvé
- Vérifier que le magasin a des événements de produits non trouvés
- Vérifier les mots-clés de filtrage dans le code

## 📈 Exemple de sortie

```
2025-01-15 19:30:15 - INFO - Extracteur API Produits Non Trouvés Prosuma initialisé pour KMIAN
2025-01-15 19:30:15 - INFO - Magasins configurés: ['230', '292', '294', '364', '415']
2025-01-15 19:30:16 - INFO - Test de connexion à l'API: https://pos3-prod-prosuma.prosuma.pos
2025-01-15 19:30:17 - INFO - ✅ Connexion API réussie: https://pos3-prod-prosuma.prosuma.pos
2025-01-15 19:30:18 - INFO - Récupération page 1...
2025-01-15 19:30:19 - INFO -   Page 1/5: 1000 événements (total: 4500)
2025-01-15 19:30:20 - INFO - ✅ 4500 event_lines récupérées au total pour le magasin 230
2025-01-15 19:30:21 - INFO - 🔍 125 événements de produits non trouvés identifiés
2025-01-15 19:30:22 - INFO - ✅ Fichier CSV créé: ./EXPORT_PRODUIT_NON_TROUVE/export_produit_non_trouve_230_20250115_193022.csv
2025-01-15 19:30:23 - INFO - ✅ Fichier copié vers le réseau: //10.0.70.169/share/.../PRIMA/export_produit_non_trouve_230_20250115_193022.csv
```

## 🎯 Avantages de l'API

- **Rapidité** : Beaucoup plus rapide que le scraping
- **Fiabilité** : Pas de dépendance à l'interface web
- **Complétude** : Accès à toutes les données sans limitation d'affichage
- **Pagination** : Gestion automatique des grandes quantités de données
- **Filtrage intelligent** : Identification automatique des événements pertinents
- **Maintenance** : Moins sensible aux changements d'interface

