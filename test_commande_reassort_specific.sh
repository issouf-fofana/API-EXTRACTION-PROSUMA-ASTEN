#!/bin/bash

# ============================================================================
# Script de test pour extraire les commandes réassort pour des magasins spécifiques
# Magasins: 110, 230, 292, 294
# ============================================================================

# Configuration
PROJECT_PATH="$(cd "$(dirname "$0")" && pwd)"
ENV_NAME="env_Api_Extraction_Alien"
ENV_PATH="$HOME/$ENV_NAME"

echo "============================================================"
echo "   TEST EXTRACTION - COMMANDES RÉASSORT"
echo "   Magasins: 110, 230, 292, 294"
echo "   Période: Hier à Aujourd'hui"
echo "   Filtre: En attente de livraison"
echo "============================================================"
echo

# Vérifier si Python est installé
if command -v python3 &> /dev/null; then
    PY=python3
elif command -v python &> /dev/null; then
    PY=python
else
    echo "❌ Python n'est pas installé ou pas dans le PATH"
    exit 1
fi

# Activer l'environnement virtuel s'il existe
if [ -f "$ENV_PATH/bin/activate" ]; then
    echo "🔄 Activation de l'environnement virtuel..."
    source "$ENV_PATH/bin/activate"
    echo "✅ Environnement virtuel activé"
    echo
fi

# Calculer les dates (hier et aujourd'hui)
# Format: YYYY-MM-DD
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    DATE_START=$(date -v-1d +%Y-%m-%d)
    DATE_END=$(date +%Y-%m-%d)
else
    # Linux
    DATE_START=$(date -d "yesterday" +%Y-%m-%d)
    DATE_END=$(date +%Y-%m-%d)
fi

# Afficher les dates
echo "📅 Configuration des dates:"
echo "   Date début: $DATE_START (hier)"
echo "   Date fin:    $DATE_END (aujourd'hui)"
echo

# Définir le filtre de statut
STATUT_COMMANDE="en attente de livraison"

echo "🔍 Filtre appliqué: $STATUT_COMMANDE"
echo

# Exporter les variables d'environnement
export DATE_START
export DATE_END
export STATUT_COMMANDE

# Changer vers le répertoire du projet
cd "$PROJECT_PATH" || exit 1

# Créer un script Python temporaire pour tester les magasins spécifiques
cat > test_specific_shops.py << 'EOF'
#!/usr/bin/env python3
"""Script de test pour magasins spécifiques"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from API_COMMANDE_REASSORT.api_commande_reassort import ProsumaAPICommandeReassortExtractor

# Magasins à tester
test_shops = ['110', '230', '292', '294']

try:
    extractor = ProsumaAPICommandeReassortExtractor()
    
    # Filtrer les magasins pour ne garder que ceux à tester
    original_shop_config = extractor.shop_config.copy()
    extractor.shop_config = {code: info for code, info in original_shop_config.items() if code in test_shops}
    extractor.shop_codes = list(extractor.shop_config.keys())
    
    if not extractor.shop_config:
        print(f"❌ Aucun des magasins {test_shops} n'est configuré dans magasins.json")
        sys.exit(1)
    
    print(f"✅ Magasins à tester: {list(extractor.shop_config.keys())}")
    print("=" * 60)
    
    # Extraire pour chaque magasin
    for shop_code in test_shops:
        if shop_code in extractor.shop_config:
            print(f"\n{'='*60}")
            print(f"TEST MAGASIN {shop_code}")
            print(f"{'='*60}")
            extractor.extract_shop(shop_code)
        else:
            print(f"⚠️ Magasin {shop_code} non trouvé dans la configuration")
    
    print("\n" + "=" * 60)
    print("✅ TEST TERMINÉ")
    print("=" * 60)
    
except Exception as e:
    print(f"❌ Erreur fatale: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF

# Lancer le script Python
echo "🚀 Lancement de l'extraction pour les magasins spécifiques..."
echo "============================================================"
echo

python test_specific_shops.py

# Récupérer le code de retour
EXIT_CODE=$?

# Nettoyer le script temporaire
rm -f test_specific_shops.py

echo
echo "============================================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Test terminé avec succès"
else
    echo "❌ Test terminé avec des erreurs (code: $EXIT_CODE)"
fi
echo "============================================================"

# Désactiver l'environnement virtuel si activé
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
fi

exit $EXIT_CODE

