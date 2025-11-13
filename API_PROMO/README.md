# Extracteur API Prosuma - Promotions

Ce script permet d'extraire toutes les promotions des magasins Prosuma via l'API REST.

## 🚀 Fonctionnalités

- **Extraction complète** : Récupère toutes les promotions avec pagination automatique
- **Multi-magasins** : Traite tous les magasins configurés simultanément
- **Export CSV** : Génère des fichiers CSV avec toutes les informations des promotions
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

1. Double-cliquer sur `run_api_promo.bat`
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
python3 api_promo.py
```

## 📊 Données extraites

Le script extrait les informations suivantes pour chaque promotion :

- **Informations de base** : ID, nom, description, type, statut
- **Période de validité** : Date de début, date de fin
- **Prix et réductions** : Prix de base, prix promotionnel, pourcentage de réduction
- **Conditions** : Quantités min/max, produits concernés, catégories, marques
- **Restrictions** : Clients concernés, jours de la semaine, heures de validité
- **Gestion** : Créateur, dates de création/modification, limites d'utilisation
- **Configuration** : Code promotion, conditions, exclusions, priorité

## 📁 Structure des fichiers

```
API_PROMO/
├── api_promo.py              # Script principal
├── config.env                # Configuration
├── magasins.json             # URLs des serveurs
├── requirements.txt          # Dépendances Python
├── run_api_promo.bat         # Script Windows
├── README.md                 # Documentation
├── copy_to_network.sh        # Script de synchronisation
└── EXPORT_PROMOS/            # Dossier des exports locaux
    └── export_promos_XXX_YYYYMMDD_HHMMSS.csv
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

## 📈 Exemple de sortie

```
2025-01-15 19:30:15 - INFO - Extracteur API Promotions Prosuma initialisé pour KMIAN
2025-01-15 19:30:15 - INFO - Magasins configurés: ['230', '292', '294', '364', '415']
2025-01-15 19:30:16 - INFO - Test de connexion à l'API: https://pos3-prod-prosuma.prosuma.pos
2025-01-15 19:30:17 - INFO - ✅ Connexion API réussie: https://pos3-prod-prosuma.prosuma.pos
2025-01-15 19:30:18 - INFO - Récupération page 1...
2025-01-15 19:30:19 - INFO -   Page 1/3: 1000 promotions (total: 2500)
2025-01-15 19:30:20 - INFO - ✅ 2500 promotions récupérées au total pour le magasin 230
2025-01-15 19:30:21 - INFO - ✅ Fichier CSV créé: ./EXPORT_PROMOS/export_promos_230_20250115_193021.csv
2025-01-15 19:30:22 - INFO - ✅ Fichier copié vers le réseau: //10.0.70.169/share/.../PRIMA/export_promos_230_20250115_193021.csv
```

## 🎯 Avantages de l'API

- **Rapidité** : Beaucoup plus rapide que le scraping
- **Fiabilité** : Pas de dépendance à l'interface web
- **Complétude** : Accès à toutes les données sans limitation d'affichage
- **Pagination** : Gestion automatique des grandes quantités de données
- **Maintenance** : Moins sensible aux changements d'interface



