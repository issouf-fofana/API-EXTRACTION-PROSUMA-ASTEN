#!/usr/bin/env python3
"""
Script pour FORCER les bonnes indentations dans api_commande_reassort.py
"""

file_path = "API_COMMANDE_REASSORT/api_commande_reassort.py"

print(f"[*] Lecture du fichier {file_path}...")

# Lire le fichier
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"[*] {len(lines)} lignes lues")

# Sauvegarder
backup_path = file_path + '.backup2'
with open(backup_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)
print(f"[*] Sauvegarde: {backup_path}")

# Forcer les bonnes indentations sur les lignes spécifiques
modifications = []

# Ligne 73-74 : if et log_file
if len(lines) >= 74:
    # Ligne 73 (index 72) : if avec 16 espaces
    if 'if os.path.exists(log_network_path)' in lines[72]:
        expected_73 = ' ' * 16 + 'if os.path.exists(log_network_path) and os.access(log_network_path, os.W_OK):\n'
        if lines[72] != expected_73:
            lines[72] = expected_73
            modifications.append(73)
    
    # Ligne 74 (index 73) : log_file avec 20 espaces
    if 'log_file = os.path.join(log_network_path' in lines[73]:
        stripped = lines[73].lstrip()
        expected_74 = ' ' * 20 + stripped
        if lines[73] != expected_74:
            lines[73] = expected_74
            modifications.append(74)

# Ligne 84-85 : else et log_file
if len(lines) >= 85:
    # Ligne 84 (index 83) : else avec 16 espaces
    if 'else:' in lines[83] and 'except' not in lines[83]:
        expected_84 = ' ' * 16 + 'else:\n'
        if lines[83] != expected_84:
            lines[83] = expected_84
            modifications.append(84)
    
    # Ligne 85 (index 84) : log_file = None avec 20 espaces
    if 'log_file = None' in lines[84]:
        expected_85 = ' ' * 20 + 'log_file = None\n'
        if lines[84] != expected_85:
            lines[84] = expected_85
            modifications.append(85)

# Ligne 100 : log_file après except
if len(lines) >= 100:
    if 'log_file = os.path.join(self.base_dir' in lines[99]:
        stripped = lines[99].lstrip()
        expected_100 = ' ' * 16 + stripped
        if lines[99] != expected_100:
            lines[99] = expected_100
            modifications.append(100)

# Ligne 104 : logging.basicConfig
if len(lines) >= 104:
    if 'logging.basicConfig' in lines[103]:
        stripped = lines[103].lstrip()
        expected_104 = ' ' * 12 + stripped
        if lines[103] != expected_104:
            lines[103] = expected_104
            modifications.append(104)

# Sauvegarder si modifications
if modifications:
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print(f"\n[OK] {len(modifications)} ligne(s) modifiee(s): {modifications}")
else:
    print("\n[OK] Aucune modification necessaire")

# Afficher les lignes critiques
print("\n[*] Verification finale:")
critical_lines = {73: 16, 74: 20, 84: 16, 85: 20, 100: 16, 104: 12}

for line_num, expected_spaces in critical_lines.items():
    if line_num <= len(lines):
        line = lines[line_num - 1]
        actual_spaces = len(line) - len(line.lstrip())
        status = "[OK]" if actual_spaces == expected_spaces else "[ERREUR]"
        print(f"   Ligne {line_num}: {actual_spaces} espaces (attendu: {expected_spaces}) {status}")
        if actual_spaces != expected_spaces:
            print(f"      Contenu: {line.rstrip()[:70]}")

print("\n[*] Termine!")
print("[*] Faites maintenant: git add . && git commit -m 'Fix indent' && git push")

