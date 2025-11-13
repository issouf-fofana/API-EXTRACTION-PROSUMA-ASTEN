# Extracteur API Prosuma - Inventaires

## Description
Cet extracteur récupère les inventaires via l'API Prosuma RPOS en utilisant l'endpoint `/inventory`.

## Fonctionnalités
- ✅ Extraction des inventaires
- ✅ Filtrage par date (hier → aujourd'hui par défaut)
- ✅ Pagination automatique
- ✅ Export CSV avec colonnes détaillées
- ✅ Envoi automatique vers le dossier partagé réseau
- ✅ Support multi-magasins

## Configuration

### Fichier config.env
```env
# Identifiants
PROSUMA_USER=votre_utilisateur
PROSUMA_PASSWORD=votre_mot_de_passe

# Magasins à traiter
SHOP_CODES=230,292,294,364,415

# Mapping des magasins
SHOP_MAPPING=230:PRIMA,292:CKM,294:SOL BENI,364:CUV7DEC,415:MBADON

# Dossier partagé réseau
DOWNLOAD_FOLDER=//10.0.70.169/share/FOFANA/Etats Natacha/Commande/PRESENTATION_COMMANDE/ASTEN

# Dates (optionnel - par défaut: hier → aujourd'hui)
DATE_START=2025-10-15
DATE_END=2025-10-16
```

## Utilisation

### Windows
```batch
run_api_inventaire.bat
```

### macOS/Linux
```bash
python3 api_inventaire.py
```

## Données extraites

### Colonnes CSV
- **Informations de base** : ID, Magasin, Numéro d'inventaire, Nom de l'inventaire
- **Dates** : Date de l'inventaire, Date de fermeture, Date de création, Date de modification
- **Type et statut** : Type d'inventaire, Statut, Statut affiché
- **Utilisateurs** : Créé par, Fermé par
- **Détails** : Description, Commentaires

### Exemple de données
```csv
id;Magasin;Numéro d'inventaire;Nom de l'inventaire;Date de l'inventaire;Type d'inventaire;Statut
4c7c57e3-0651-43cb-a295-2c2e7eb09b30;230;358;INVENTAIRE SURGELE SEPT 2025;30/09/2025 15:18:01;Partiel;Clôturé
```

## Structure des fichiers
```
API_INVENTAIRE/
├── api_inventaire.py         # Script principal
├── config.env               # Configuration
├── magasins.json            # Configuration des magasins
├── requirements.txt         # Dépendances Python
├── run_api_inventaire.bat   # Script Windows
├── README.md                # Documentation
├── copy_to_network.sh       # Script de copie réseau
└── EXPORT_INVENTAIRE/       # Dossier des exports locaux
    └── export_inventaire_*.csv
```

## Logs
Les logs sont sauvegardés dans `prosuma_api_inventaire.log`.

## Support
Pour toute question ou problème, consultez les logs ou contactez l'équipe technique.








