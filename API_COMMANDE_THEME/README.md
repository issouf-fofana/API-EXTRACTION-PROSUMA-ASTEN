# Extracteur API Prosuma - Commandes par Thème/Promotion

## Description
Cet extracteur récupère les commandes par thème/promotion via l'API Prosuma RPOS en utilisant l'endpoint `/external_order`.

## Fonctionnalités
- ✅ Extraction des commandes par thème/promotion
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
run_api_commande_theme.bat
```

### macOS/Linux
```bash
python3 api_commande_theme.py
```

## Données extraites

### Colonnes CSV
- **Informations de base** : ID, Magasin, Référence commande
- **Références** : Référence externe, Nom pré-commande
- **Dates** : Date commande, Date validation, Date livraison
- **Statut** : Statut de la commande
- **Fournisseur** : Nom, Code, Email, Temps de livraison
- **Personnel** : Créé par, Validé par
- **Métadonnées** : Date de création, Date de modification

### Exemple de données
```csv
id;Magasin;Référence commande;Référence externe;Nom pré-commande;Date commande;Statut;Fournisseur
d01dc87b-15bc-4306-a70d-6cf01f95121f;230;11859685;P16J;P16J;17/04/2025 16:34:09;en attente de livraison;SATOCI
```

## Structure des fichiers
```
API_COMMANDE_THEME/
├── api_commande_theme.py          # Script principal
├── config.env                     # Configuration
├── magasins.json                  # Configuration des magasins
├── requirements.txt               # Dépendances Python
├── run_api_commande_theme.bat     # Script Windows
├── README.md                      # Documentation
├── copy_to_network.sh             # Script de copie réseau
└── EXPORT_COMMANDE_THEME/         # Dossier des exports locaux
    └── export_commande_theme_*.csv
```

## Logs
Les logs sont sauvegardés dans `prosuma_api_commande_theme.log`.

## Support
Pour toute question ou problème, consultez les logs ou contactez l'équipe technique.

