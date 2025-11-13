# 🛍️ API Prosuma RPOS - Extracteur d'Articles

## 📋 Description
Script Python pour extraire tous les articles/produits via l'API Prosuma RPOS avec pagination automatique et export CSV.

## ✨ Fonctionnalités
- ✅ **Pagination automatique** : Récupère tous les articles (pas de limite)
- ✅ **En-têtes complets** : 40+ colonnes avec toutes les informations produits
- ✅ **Envoi réseau automatique** : Fichier copié vers le dossier partagé
- ✅ **Gestion des erreurs** : Continue même si certains magasins échouent
- ✅ **Logs détaillés** : Suivi complet du processus
- ✅ **Multi-magasins** : Traite tous les magasins configurés

## 📁 Structure des fichiers
```
API_ARTICLE/
├── api_article.py          # Script principal
├── config.env              # Configuration
├── magasins.json          # URLs des serveurs par magasin
├── requirements.txt       # Dépendances Python
├── run_api_article.bat    # Script Windows
├── EXPORT_ARTICLES/       # Dossier des exports
└── prosuma_api_articles.log # Logs
```

## 🔧 Configuration
Modifiez `config.env` pour :
- **Identifiants** : `PROSUMA_USER` et `PROSUMA_PASSWORD`
- **Magasins** : `SHOP_CODES` et `SHOP_MAPPING`
- **Réseau** : `DOWNLOAD_FOLDER`

## 🚀 Utilisation

### Sur macOS/Linux :
```bash
# Créer l'environnement virtuel
python3 -m venv env
source env/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'extraction
python3 api_article.py
```

### Sur Windows :
```cmd
run_api_article.bat
```

## 📊 En-têtes CSV
Le fichier CSV contient 40+ colonnes avec toutes les informations produits :
1. id
2. Magasin (numéro du magasin, ex: 230)
3. EAN
4. Nom
5. Label 1
6. Label 2
7. Code court
8. Prix de vente
9. Prix promo
10. Prix magasin
... (voir le script pour la liste complète)

## 🌐 Envoi réseau
Les fichiers sont automatiquement copiés vers :
`/Volumes/SHARE/FOFANA/Etats Natacha/Commande/PRESENTATION_COMMANDE/ASTEN/{NOM_MAGASIN}/`

## 📝 Logs
Tous les logs sont sauvegardés dans `prosuma_api_articles.log` avec :
- Progression de la pagination
- Nombre d'articles récupérés
- Types d'articles trouvés
- Erreurs et avertissements
- Temps d'exécution

## 🔍 Dépannage
- **Erreur 401** : Vérifiez les identifiants dans `config.env`
- **Erreur réseau** : Vérifiez que le partage réseau est monté
- **Fichier vide** : Vérifiez que le magasin a des articles
- **Timeout** : Augmentez le timeout dans le script si nécessaire

## 📈 Performance
- **Pagination** : 1000 articles par page (maximum de l'API)
- **Mémoire** : Optimisé pour traiter des milliers d'articles
- **Réseau** : Gestion des erreurs de connexion
- **Logs** : Suivi en temps réel du progrès

