# Extracteur API Prosuma - Réceptions de Commandes

## Description
Cet extracteur récupère les réceptions de commandes via l'API Prosuma RPOS en utilisant l'endpoint `/delivery`.

## Types de réceptions
- **BON DE RÉCEPTION** : Quand `order` contient une référence de commande (8 caractères numériques)
- **FACTURE** : Quand `order` est null ou vide

## Fonctionnalités
- ✅ Extraction des réceptions de commandes
- ✅ Distinction automatique BON DE RÉCEPTION / FACTURE
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
run_api_reception.bat
```

### macOS/Linux
```bash
python3 api_reception.py
```

## Données extraites

### Colonnes CSV
- **Informations de base** : ID, Magasin, Type de réception
- **Références** : Numéro de réception, Référence commande
- **Dates** : Date de réception, Date de validation
- **Validation** : Validé par, Validé (Oui/Non)
- **Montants** : Quantité totale, Prix total HT
- **Statut** : Statut commande, Nom de la réception
- **Fournisseur** : Nom, Code, Email
- **Métadonnées** : Date de création, Date de modification

### Exemple de données
```csv
id;Magasin;Type de réception;Numéro de réception;Référence commande;Date de réception;Validé
0000ba8d-66eb-4a5f-acc4-df78bf08ce21;230;FACTURE;1200082350;;28/04/2025;Oui
```

## Structure des fichiers
```
API_RECEPTION/
├── api_reception.py          # Script principal
├── config.env               # Configuration
├── magasins.json            # Configuration des magasins
├── requirements.txt         # Dépendances Python
├── run_api_reception.bat    # Script Windows
├── README.md                # Documentation
├── copy_to_network.sh       # Script de copie réseau
└── EXPORT_RECEPTION/        # Dossier des exports locaux
    └── export_reception_*.csv
```

## Logs
Les logs sont sauvegardés dans `prosuma_api_reception.log`.

## Support
Pour toute question ou problème, consultez les logs ou contactez l'équipe technique.

