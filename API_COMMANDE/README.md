# 🚀 API Prosuma RPOS - Extracteur de Commandes

## 📋 Description
Script Python pour extraire les commandes fournisseurs via l'API Prosuma RPOS avec pagination automatique et export CSV.

## ✨ Fonctionnalités
- ✅ **Pagination automatique** : Récupère toutes les données (pas de limite)
- ✅ **En-têtes exacts** : 35 colonnes dans l'ordre précis demandé
- ✅ **Envoi réseau automatique** : Fichier copié vers le dossier partagé
- ✅ **Filtrage par statut** : Configurable via `config.env`
- ✅ **Gestion des erreurs** : Continue même si certains magasins échouent
- ✅ **Logs détaillés** : Suivi complet du processus

## 📁 Structure des fichiers
```
API_COMMANDE/
├── api_commande.py          # Script principal
├── config.env               # Configuration
├── magasins.json           # URLs des serveurs par magasin
├── requirements.txt        # Dépendances Python
├── run_api_commande.bat    # Script Windows
├── copy_to_network.sh      # Script de copie réseau
├── EXPORT_API_FINAL/       # Dossier des exports
└── prosuma_api_extraction.log # Logs
```

## 🔧 Configuration
Modifiez `config.env` pour :
- **Dates** : `DATE_START` et `DATE_END`
- **Statut** : `STATUT_COMMANDE` (ex: 'en attente de livraison')
- **Magasins** : `SHOP_CODES` et `SHOP_MAPPING`
- **Réseau** : `DOWNLOAD_FOLDER`

## 🚀 Utilisation

### Sur macOS/Linux :
```bash
source env/bin/activate
python3 api_commande.py
```

### Sur Windows :
```cmd
run_api_commande.bat
```

## 📊 En-têtes CSV
Le fichier CSV contient exactement 35 colonnes dans cet ordre :
1. id
2. Magasin (numéro du magasin, ex: 230)
3. Code communication
4. Référence commande
5. Référence commande externe
... (voir le script pour la liste complète)

## 🌐 Envoi réseau
Les fichiers sont automatiquement copiés vers :
`/Volumes/SHARE/FOFANA/Etats Natacha/Commande/PRESENTATION_COMMANDE/ASTEN/{NOM_MAGASIN}/`

## 📝 Logs
Tous les logs sont sauvegardés dans `prosuma_api_extraction.log` avec :
- Progression de la pagination
- Nombre de commandes récupérées
- Erreurs et avertissements
- Temps d'exécution

## 🔍 Dépannage
- **Erreur 401** : Vérifiez les identifiants dans `config.env`
- **Erreur réseau** : Vérifiez que le partage réseau est monté
- **Fichier vide** : Vérifiez les dates dans `config.env`

