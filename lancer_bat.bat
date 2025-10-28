# ==========================================
# FICHIER 1: lancer_app.bat (WINDOWS)
# ==========================================
# Créez un fichier nommé "lancer_app.bat" avec ce contenu :

@echo off
echo ========================================
echo   Lancement du Generateur de Devis
echo ========================================
echo.
echo Demarrage de l'application...
echo.

cd /d "%~dp0"
streamlit run app.py

pause


# ==========================================
# FICHIER 2: lancer_app.sh (MAC/LINUX)
# ==========================================
# Créez un fichier nommé "lancer_app.sh" avec ce contenu :

#!/bin/bash

echo "========================================"
echo "  Lancement du Générateur de Devis"
echo "========================================"
echo ""
echo "Démarrage de l'application..."
echo ""

cd "$(dirname "$0")"
streamlit run app.py


# ==========================================
# INSTRUCTIONS D'UTILISATION
# ==========================================

# WINDOWS:
# 1. Double-cliquez sur "lancer_app.bat"
# 2. L'application s'ouvre automatiquement !

# MAC/LINUX:
# 1. Rendez le fichier exécutable (une seule fois) :
#    chmod +x lancer_app.sh
# 2. Double-cliquez sur "lancer_app.sh"
#    ou tapez dans le terminal : ./lancer_app.sh

# ==========================================
# RACCOURCI BUREAU (WINDOWS)
# ==========================================
# Pour créer un raccourci sur le bureau :
# 1. Clic droit sur "lancer_app.bat"
# 2. Créer un raccourci
# 3. Glissez le raccourci sur le bureau
# 4. (Optionnel) Clic droit > Propriétés > Changer l'icône

# Vous pouvez télécharger une icône de canapé sur :
# https://www.flaticon.com (recherchez "sofa")