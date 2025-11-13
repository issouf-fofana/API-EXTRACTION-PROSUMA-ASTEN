#!/usr/bin/env python3
"""
Script pour créer un fichier CSV d'exemple avec des événements de produits non trouvés
"""

import csv
import os
from datetime import datetime

def create_sample_csv():
    """Crée un fichier CSV d'exemple avec des événements de produits non trouvés"""
    
    # Créer le dossier de destination
    os.makedirs('./EXPORT_PRODUIT_NON_TROUVE', exist_ok=True)
    
    # Nom du fichier CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"export_produit_non_trouve_230_{timestamp}.csv"
    filepath = os.path.join('./EXPORT_PRODUIT_NON_TROUVE', filename)
    
    # En-têtes pour les produits non trouvés
    headers = [
        "id",
        "Magasin",
        "Type d'événement",
        "Description",
        "Date de l'événement",
        "Numéro de ticket",
        "Série de ticket",
        "ID du ticket",
        "Code barre/EAN",
        "Caissier",
        "Formation",
        "Garant",
        "Extras",
        "Date de création",
        "Date de modification",
        "Date de suppression",
        "Supprimé"
    ]
    
    # Données d'exemple
    sample_data = [
        [
            "82ffc578-1957-47ae-a63a-f1ca3c6198da",
            "230",
            "Produit non trouvé",
            "Code barre inconnu",
            "16/10/2025 10:30:15",
            "4253",
            "2",
            "d65f3b41-78f2-4e50-a6a3-3c6871913824",
            "91230011002000004253",
            "Marie Dupont",
            "Formation standard",
            "Superviseur",
            "Code barre: 1234567890123",
            "16/10/2025 10:30:15",
            "16/10/2025 10:30:15",
            "",
            "Non"
        ],
        [
            "91aab689-2a68-58bf-b74b-f2db4d7309eb",
            "230",
            "Code inconnu",
            "EAN non reconnu",
            "16/10/2025 11:45:22",
            "4254",
            "2",
            "e76g4c52-89g3-5f61-b7b4-4d7982024935",
            "91230011002000004254",
            "Jean Martin",
            "Formation standard",
            "Superviseur",
            "EAN: 9876543210987",
            "16/10/2025 11:45:22",
            "16/10/2025 11:45:22",
            "",
            "Non"
        ],
        [
            "a2bbc790-3b79-69cf-c85c-g3ec5e8410afc",
            "230",
            "Scan error",
            "Erreur de lecture code barre",
            "16/10/2025 14:20:08",
            "4255",
            "2",
            "f87h5d63-9ah4-6g72-c8c5-5e8093135046",
            "91230011002000004255",
            "Sophie Bernard",
            "Formation avancée",
            "Manager",
            "Code barre endommagé",
            "16/10/2025 14:20:08",
            "16/10/2025 14:20:08",
            "",
            "Non"
        ]
    ]
    
    # Créer le fichier CSV
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        
        # Écrire l'en-tête
        writer.writerow(headers)
        
        # Écrire les données d'exemple
        for row in sample_data:
            writer.writerow(row)
    
    print(f"✅ Fichier CSV d'exemple créé: {filepath}")
    print(f"   {len(sample_data)} événements d'exemple")
    print(f"   {len(headers)} colonnes par événement")
    
    return filepath

if __name__ == "__main__":
    create_sample_csv()

