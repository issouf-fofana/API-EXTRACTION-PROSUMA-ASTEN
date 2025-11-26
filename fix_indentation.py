#!/usr/bin/env python3
"""
Script pour corriger automatiquement les indentations dans api_commande_reassort.py
"""

import os

file_path = "API_COMMANDE_REASSORT/api_commande_reassort.py"

print(f"[*] Correction des indentations dans {file_path}...")

# Lire le fichier
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"[*] Fichier lu : {len(lines)} lignes")

# Sauvegarder l'original
backup_path = file_path + '.backup'
with open(backup_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)
print(f"[*] Sauvegarde creee : {backup_path}")

# Vérifier et afficher les lignes problématiques
print("\n[*] Verification des lignes critiques :")
critical_lines = [73, 74, 84, 85, 99, 100, 103, 104]

for line_num in critical_lines:
    if line_num <= len(lines):
        line = lines[line_num - 1]
        spaces = len(line) - len(line.lstrip())
        print(f"   Ligne {line_num}: {spaces} espaces | {line.rstrip()[:60]}")

# Corrections spécifiques
corrections_made = 0

# Ligne 74 : doit avoir 20 espaces (5 niveaux * 4 espaces)
if len(lines) >= 74:
    line = lines[73]  # Index 73 pour ligne 74
    stripped = line.lstrip()
    if stripped.startswith('log_file = os.path.join(log_network_path'):
        # S'assurer qu'il y a 20 espaces
        if not line.startswith(' ' * 20 + 'log_file'):
            lines[73] = ' ' * 20 + stripped
            corrections_made += 1
            print(f"[OK] Ligne 74 corrigee (20 espaces)")

# Ligne 85 : doit avoir 16 espaces (4 niveaux * 4 espaces) pour 'else:'
if len(lines) >= 85:
    line = lines[84]  # Index 84 pour ligne 85
    stripped = line.lstrip()
    if 'else:' in stripped and not stripped.startswith('#'):
        if not line.startswith(' ' * 16 + 'else:'):
            lines[84] = ' ' * 16 + 'else:\n'
            corrections_made += 1
            print(f"[OK] Ligne 85 corrigee (16 espaces)")

# Ligne 86 : log_file = None sous le else, doit avoir 20 espaces
if len(lines) >= 86:
    line = lines[85]  # Index 85 pour ligne 86
    stripped = line.lstrip()
    if stripped.startswith('log_file = None'):
        if not line.startswith(' ' * 20 + 'log_file'):
            lines[85] = ' ' * 20 + stripped
            corrections_made += 1
            print(f"[OK] Ligne 86 corrigee (20 espaces)")

# Ligne 100 : doit avoir 16 espaces (4 niveaux * 4 espaces)
if len(lines) >= 100:
    line = lines[99]  # Index 99 pour ligne 100
    stripped = line.lstrip()
    if stripped.startswith('log_file = os.path.join(self.base_dir'):
        if not line.startswith(' ' * 16 + 'log_file'):
            lines[99] = ' ' * 16 + stripped
            corrections_made += 1
            print(f"[OK] Ligne 100 corrigee (16 espaces)")

# Ligne 104 : doit avoir 12 espaces (3 niveaux * 4 espaces)
if len(lines) >= 104:
    line = lines[103]  # Index 103 pour ligne 104
    stripped = line.lstrip()
    if stripped.startswith('logging.basicConfig'):
        if not line.startswith(' ' * 12 + 'logging'):
            lines[103] = ' ' * 12 + stripped
            corrections_made += 1
            print(f"[OK] Ligne 104 corrigee (12 espaces)")

# Écrire le fichier corrigé
if corrections_made > 0:
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print(f"\n[OK] {corrections_made} correction(s) appliquee(s)")
    print(f"[OK] Fichier corrige : {file_path}")
else:
    print("\n[OK] Aucune correction necessaire - le fichier est deja correct")

print("\n[*] Verification apres correction :")
for line_num in critical_lines:
    if line_num <= len(lines):
        line = lines[line_num - 1]
        spaces = len(line) - len(line.lstrip())
        print(f"   Ligne {line_num}: {spaces} espaces | {line.rstrip()[:60]}")

print("\n[OK] Termine ! Vous pouvez maintenant faire git push.")

