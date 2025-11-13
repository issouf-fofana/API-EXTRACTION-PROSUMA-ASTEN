# Extracteur API Prosuma - Pré-commandes Fournisseurs

## Description
Cet extracteur récupère les pré-commandes fournisseurs via l'API Prosuma RPOS en utilisant l'endpoint `/supplier_pre_order`.

## Fonctionnalités
- ✅ Extraction des pré-commandes fournisseurs
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
run_api_pre_commande.bat
```

### macOS/Linux
```bash
python3 api_pre_commande.py
```

## Données extraites

### Colonnes CSV
- **Informations de base** : ID, Magasin, Nom de la pré-commande
- **Dates** : Date de création, Date de modification
- **Statut** : Statut de la pré-commande
- **Description** : Description de la pré-commande
- **Fournisseur** : Nom, Code, Email, Téléphone
- **Adresse fournisseur** : Adresse, Ville, Code postal, Pays

### Exemple de données
```csv
id;Magasin;Nom de la pré-commande;Date de création;Fournisseur
2654c98b-822c-4e3b-b152-dc96e5ef1bf8;230;FOURNISSEUR CENTRALE;16/10/2025 14:22:40;FOURNISSEUR CENTRALE
```

## Structure des fichiers
```
API_PRE_COMMANDE/
├── api_pre_commande.py      # Script principal
├── config.env              # Configuration
├── magasins.json           # Configuration des magasins
├── requirements.txt        # Dépendances Python
├── run_api_pre_commande.bat # Script Windows
├── README.md               # Documentation
├── copy_to_network.sh      # Script de copie réseau
└── EXPORT_PRE_COMMANDE/    # Dossier des exports locaux
    └── export_pre_commande_*.csv
```

## Logs
Les logs sont sauvegardés dans `prosuma_api_pre_commande.log`.

## Support
Pour toute question ou problème, consultez les logs ou contactez l'équipe technique.








