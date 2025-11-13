# API PROSUMA RPOS - Structure Unifiée

## 🎯 **Vue d'ensemble**
Cette structure unifiée contient **10 APIs d'extraction** pour Prosuma RPOS avec un **environnement virtuel unique** et un **menu centralisé**.

## 📁 **Structure du projet**
```
API_PROSUMA_RPOS/
├── env/                          # 🌟 ENVIRONNEMENT VIRTUEL UNIFIÉ
├── requirements.txt              # Dépendances Python unifiées
├── run_all_extractions.bat      # 🚀 SCRIPT PRINCIPAL (Menu)
├── copy_to_network.sh           # Script de déploiement réseau
├── README_UNIFIED.md            # Cette documentation
│
├── API_COMMANDE/                # 1️⃣ Commandes fournisseurs
│   ├── api_commande.py
│   ├── config.env
│   └── magasins.json
│
├── API_ARTICLE/                 # 2️⃣ Articles/Produits
│   ├── api_article.py
│   ├── config.env
│   └── magasins.json
│
├── API_PROMO/                   # 3️⃣ Promotions
│   ├── api_promo.py
│   ├── config.env
│   └── magasins.json
│
├── API_PRODUIT_NON_TROUVE/      # 4️⃣ Produits non trouvés
│   ├── api_produit_non_trouve.py
│   ├── config.env
│   └── magasins.json
│
├── API_COMMANDE_THEME/          # 5️⃣ Commandes par thème/promotion
│   ├── api_commande_theme.py
│   ├── config.env
│   └── magasins.json
│
├── API_RECEPTION/               # 6️⃣ Réceptions de commandes
│   ├── api_reception.py
│   ├── config.env
│   └── magasins.json
│
├── API_PRE_COMMANDE/            # 7️⃣ Pré-commandes fournisseurs
│   ├── api_pre_commande.py
│   ├── config.env
│   └── magasins.json
│
├── API_RETOUR_MARCHANDISE/      # 8️⃣ Retours de marchandises
│   ├── api_retour_marchandise.py
│   ├── config.env
│   └── magasins.json
│
├── API_INVENTAIRE/              # 9️⃣ Inventaires
│   ├── api_inventaire.py
│   ├── config.env
│   └── magasins.json
│
└── API_STATS_VENTE/             # 🔟 Statistiques de ventes
    ├── api_stats_vente.py
    ├── config.env
    └── magasins.json
```

## 🚀 **Utilisation**

### **1. Installation (une seule fois)**
```bash
# Aller dans le dossier API_PROSUMA_RPOS
cd API_PROSUMA_RPOS

# Activer l'environnement virtuel unifié
source env/bin/activate  # macOS/Linux
# ou
env\Scripts\activate     # Windows

# Installer les dépendances (déjà fait)
pip install -r requirements.txt
```

### **2. Exécution**
```bash
# Windows - Menu interactif
run_all_extractions.bat

# macOS/Linux - Exécution directe
python API_COMMANDE/api_commande.py
python API_STATS_VENTE/api_stats_vente.py
# etc...
```

## 📊 **APIs Disponibles**

| # | API | Endpoint | Description | Données |
|---|-----|----------|-------------|---------|
| 1 | **API_COMMANDE** | `/supplier_order/` | Commandes fournisseurs | Commandes, statuts, fournisseurs |
| 2 | **API_ARTICLE** | `/product/` | Articles/Produits | Catalogue, stocks, prix |
| 3 | **API_PROMO** | `/promotion/` | Promotions | Promotions actives, dates |
| 4 | **API_PRODUIT_NON_TROUVE** | `/event_line/` | Produits non trouvés | Événements de scan |
| 5 | **API_COMMANDE_THEME** | `/external_order/` | Commandes par thème | Commandes externes |
| 6 | **API_RECEPTION** | `/delivery/` | Réceptions | Bons de réception, factures |
| 7 | **API_PRE_COMMANDE** | `/supplier_pre_order/` | Pré-commandes | Pré-commandes fournisseurs |
| 8 | **API_RETOUR_MARCHANDISE** | `/delivery_return/` | Retours | Retours de marchandises |
| 9 | **API_INVENTAIRE** | `/inventory/` | Inventaires | Inventaires, contrôles |
| 10 | **API_STATS_VENTE** | `/product_line/` | Statistiques de ventes | Lignes de vente, CA, quantités |

## ⚙️ **Configuration**

### **Fichiers de configuration par API**
Chaque API a son propre `config.env` avec :
- **Identifiants** : `PROSUMA_USER`, `PROSUMA_PASSWORD`
- **Magasins** : `SHOP_CODES`, `SHOP_MAPPING`
- **Dates** : `DATE_START`, `DATE_END` (optionnel)
- **Réseau** : `DOWNLOAD_FOLDER`

### **Magasins configurés**
- **230** : PRIMA (pos3-prod-prosuma.prosuma.pos)
- **292** : CKM (pos9-prod-prosuma.prosuma.pos)
- **294** : SOL BENI (pos2-prod-prosuma.prosuma.pos)
- **364** : CUV7DEC (pos17-prod-prosuma.prosuma.pos)
- **415** : MBADON (pos16-prod-prosuma.prosuma.pos)

## 📈 **Avantages de la structure unifiée**

### ✅ **Avantages**
- **Un seul environnement virtuel** pour toutes les APIs
- **Menu centralisé** pour lancer les extractions
- **Maintenance simplifiée** (une seule installation)
- **Cohérence** entre toutes les APIs
- **Gestion centralisée** des dépendances

### 🔧 **Maintenance**
- **Mise à jour des dépendances** : `pip install -r requirements.txt`
- **Ajout d'une nouvelle API** : Créer le dossier + ajouter au menu
- **Configuration** : Modifier les `config.env` individuels

## 🌐 **Déploiement réseau**

### **Copie automatique**
```bash
# Exécuter le script de copie
./copy_to_network.sh
```

### **Chemins réseau supportés**
- `/Volumes/SHARE/FOFANA/Etats Natacha/SCRIPT/extraction prosuma/`
- `//10.0.70.169/share/FOFANA/Etats Natacha/SCRIPT/extraction prosuma/`
- `/mnt/share/FOFANA/Etats Natacha/SCRIPT/extraction prosuma/`

## 📋 **Résumé des données extraites**

### **Volume de données (exemple magasin 230)**
- **Commandes fournisseurs** : ~8,600 commandes
- **Articles** : ~127,000 produits
- **Promotions** : ~560 promotions
- **Produits non trouvés** : ~1,400,000 événements
- **Commandes par thème** : ~1,400 commandes
- **Réceptions** : ~7,500 réceptions
- **Pré-commandes** : ~750 pré-commandes
- **Retours** : ~430 retours
- **Inventaires** : ~360 inventaires
- **Statistiques de ventes** : ~3,500,000 lignes de vente

### **Formats de sortie**
- **CSV** avec séparateur `;`
- **Encodage UTF-8**
- **Colonnes détaillées** selon le type d'API
- **Envoi automatique** vers le réseau

## 🆘 **Support**

### **Logs**
- Chaque API génère ses propres logs
- Fichiers `.log` dans chaque dossier API
- Niveau de détail configurable

### **Gestion des erreurs**
- **Connexion API** : Retry automatique
- **Magasin inaccessible** : Skip et continue
- **Erreur réseau** : Fichier gardé localement
- **Données corrompues** : Skip la ligne et continue

---

**🎉 Structure unifiée opérationnelle !**
**Toutes les APIs utilisent le même environnement virtuel et sont accessibles via un menu centralisé.**








