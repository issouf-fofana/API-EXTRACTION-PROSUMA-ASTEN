# Extracteur API Prosuma - Retours de Marchandises

## Description
Cet extracteur récupère les retours de marchandises via l'API Prosuma RPOS en utilisant l'endpoint `/delivery_return`.

## Fonctionnalités
- ✅ Extraction des retours de marchandises
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
run_api_retour_marchandise.bat
```

### macOS/Linux
```bash
python3 api_retour_marchandise.py
```

## Données extraites

### Colonnes CSV
- **Informations de base** : ID, Magasin, Numéro de retour, Date de retour
- **Création** : Créé par, Date de validation, Validé
- **Statut** : Statut de commande, Nom du retour
- **Fournisseur** : Nom, Code, Email, Téléphone
- **Adresse fournisseur** : Adresse, Ville, Code postal, Pays
- **Commande associée** : Référence commande
- **Dates** : Date de création, Date de modification

### Exemple de données
```csv
id;Magasin;Numéro de retour;Date de retour;Fournisseur;Statut de commande
d87e1d68-0111-4df1-9cee-035380a59714;230;67228230;16/10/2025 15:12:11;FOURNISSEUR CENTRALE;Pas de commande associée
```

## Structure des fichiers
```
API_RETOUR_MARCHANDISE/
├── api_retour_marchandise.py      # Script principal
├── config.env                    # Configuration
├── magasins.json                 # Configuration des magasins
├── requirements.txt              # Dépendances Python
├── run_api_retour_marchandise.bat # Script Windows
├── README.md                     # Documentation
├── copy_to_network.sh            # Script de copie réseau
└── EXPORT_RETOUR_MARCHANDISE/    # Dossier des exports locaux
    └── export_retour_marchandise_*.csv
```

## Logs
Les logs sont sauvegardés dans `prosuma_api_retour_marchandise.log`.

## Support
Pour toute question ou problème, consultez les logs ou contactez l'équipe technique.








