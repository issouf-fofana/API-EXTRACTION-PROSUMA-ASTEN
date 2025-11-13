# API Statistiques de Ventes Prosuma RPOS

## Description
Extracteur API pour récupérer les statistiques de ventes depuis l'API Prosuma RPOS via l'endpoint `/product_line`.

## Fonctionnalités
- ✅ Récupération des lignes de produits (ventes) avec pagination
- ✅ Filtrage par date (hier -> aujourd'hui par défaut)
- ✅ Export CSV avec colonnes détaillées
- ✅ Envoi automatique vers le dossier partagé réseau
- ✅ Support multi-magasins
- ✅ Gestion des erreurs et logging détaillé

## Configuration

### 1. Fichier config.env
```env
PROSUMA_USER=votre_utilisateur
PROSUMA_PASSWORD=votre_mot_de_passe
SHOP_CODES=230,292,294,364,415
SHOP_MAPPING=230:PRIMA,292:CKM,294:SOL BENI,364:CUV7DEC,415:MBADON
DATE_START=2025-01-15
DATE_END=2025-01-16
DOWNLOAD_FOLDER=//10.0.70.169/share/FOFANA/Etats Natacha/Commande/PRESENTATION_COMMANDE/ASTEN
```

### 2. Fichier magasins.json
Configuration des URLs des serveurs pour chaque magasin.

## Installation

### 1. Créer l'environnement virtuel
```bash
python -m venv env
```

### 2. Activer l'environnement virtuel
**Windows:**
```cmd
env\Scripts\activate
```

**macOS/Linux:**
```bash
source env/bin/activate
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

## Utilisation

### Exécution simple
```bash
python api_stats_vente.py
```

### Exécution avec dates personnalisées
Modifier les variables `DATE_START` et `DATE_END` dans `config.env`.

## Structure des données exportées

### Colonnes du fichier CSV
- **id** : Identifiant unique de la ligne
- **Magasin** : Code du magasin
- **Date de vente** : Date et heure de la vente
- **Numéro de ticket** : Numéro du ticket de caisse
- **Série de ticket** : Série du ticket
- **Nom du produit** : Nom du produit vendu
- **EAN du produit** : Code EAN du produit
- **Quantité vendue** : Quantité vendue
- **Prix unitaire** : Prix unitaire de vente
- **Prix total TTC** : Prix total toutes taxes comprises
- **Prix total HT** : Prix total hors taxes
- **TVA** : Montant de la TVA
- **Taux TVA** : Taux de TVA appliqué
- **Remise** : Montant de la remise
- **Prix d'achat** : Prix d'achat du produit
- **Marge** : Marge calculée (prix vente - prix achat)
- **Caissier** : Nom du caissier
- **Formation** : Indique si c'est une vente de formation
- **Méthode de saisie** : Méthode de saisie du produit
- **Numéro de série** : Numéro de série du produit
- **Motif** : Motif de la vente
- **Date de création** : Date de création de la ligne
- **Date de modification** : Date de dernière modification

## Logs
Les logs sont sauvegardés dans `prosuma_api_stats_vente.log` et affichés dans la console.

## Dossiers de destination
- **Local** : `./EXPORT_STATS_VENTE/`
- **Réseau** : `//10.0.70.169/share/FOFANA/Etats Natacha/Commande/PRESENTATION_COMMANDE/ASTEN/{NOM_MAGASIN}/`

## Gestion des erreurs
- Connexion API : Retry automatique
- Magasin non trouvé : Skip et continue
- Erreur réseau : Fichier gardé localement
- Données corrompues : Skip la ligne et continue

## Performance
- Pagination automatique (1000 lignes par page)
- Limite de sécurité : 100 pages maximum (100,000 lignes)
- Filtrage par date pour optimiser les performances
- Gestion mémoire optimisée pour les gros volumes

## Support
En cas de problème, vérifier :
1. Les identifiants dans `config.env`
2. La connectivité réseau
3. Les logs dans `prosuma_api_stats_vente.log`
4. L'accessibilité du dossier partagé réseau








