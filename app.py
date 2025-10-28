"""
Application Streamlit pour générer des devis de canapés sur mesure
Simple à utiliser - Pas besoin de connaissances Python !
"""

import streamlit as st
import turtle
from io import BytesIO
from PIL import Image
import tempfile
import os

# Import de vos modules (à créer)
from pricing import calculer_prix_total
from pdf_generator import generer_pdf_devis

# Configuration de la page
st.set_page_config(
    page_title="Générateur de Devis Canapés",
    page_icon="🛋️",
    layout="wide"
)

# Titre principal
st.title("🛋️ Générateur de Devis Canapés Sur Mesure")
st.markdown("---")

# ====================
# FORMULAIRE PRINCIPAL
# ====================

col1, col2 = st.columns([1, 2])

with col1:
    st.header("📋 Configuration du Canapé")
    
    # TYPE DE CANAPÉ
    st.subheader("1. Type de Canapé")
    type_canape = st.selectbox(
        "Sélectionnez le type",
        ["Simple (S)", "L - Sans Angle", "L - Avec Angle (LF)", 
         "U - Sans Angle", "U - 1 Angle (U1F)", "U - 2 Angles (U2F)"],
        help="Choisissez la forme du canapé"
    )
    
    # DIMENSIONS
    st.subheader("2. Dimensions (en cm)")
    
    if "Simple" in type_canape:
        tx = st.number_input("Largeur (Tx)", min_value=100, max_value=600, value=280, step=10)
        ty = tz = None
    elif "L" in type_canape:
        tx = st.number_input("Largeur bas (Tx)", min_value=100, max_value=600, value=350, step=10)
        ty = st.number_input("Hauteur gauche (Ty)", min_value=100, max_value=600, value=250, step=10)
        tz = None
    else:  # U
        tx = st.number_input("Largeur bas (Tx)", min_value=100, max_value=600, value=450, step=10)
        ty = st.number_input("Hauteur gauche (Ty)", min_value=100, max_value=600, value=300, step=10)
        tz = st.number_input("Hauteur droite (Tz)", min_value=100, max_value=600, value=280, step=10)
    
    profondeur = st.number_input("Profondeur", min_value=50, max_value=120, value=70, step=5)
    
    # ACCOUDOIRS
    st.subheader("3. Accoudoirs")
    acc_left = st.checkbox("Accoudoir Gauche", value=True)
    acc_right = st.checkbox("Accoudoir Droit", value=True)
    if "L" not in type_canape and "Simple" not in type_canape:
        acc_bas = st.checkbox("Accoudoir Bas", value=True)
    else:
        acc_bas = st.checkbox("Accoudoir Bas", value=True) if "L" in type_canape else False
    
    # DOSSIERS
    st.subheader("4. Dossiers")
    dossier_left = st.checkbox("Dossier Gauche", value=True) if "Simple" not in type_canape else False
    dossier_bas = st.checkbox("Dossier Bas", value=True)
    dossier_right = st.checkbox("Dossier Droit", value=True) if ("U" in type_canape or "L" not in type_canape) else False
    
    # MÉRIDIENNE
    st.subheader("5. Méridienne (optionnel)")
    has_meridienne = st.checkbox("Ajouter une méridienne")
    if has_meridienne:
        meridienne_side = st.selectbox("Côté", ["Gauche (g)", "Droite (d)", "Bas (b)"])
        meridienne_len = st.number_input("Longueur (cm)", min_value=30, max_value=200, value=100, step=10)
        # Conversion pour le code
        meridienne_side = meridienne_side[0].split()[0].lower()
    else:
        meridienne_side = None
        meridienne_len = 0
    
    # COUSSINS
    st.subheader("6. Coussins")
    type_coussins = st.selectbox(
        "Type de coussins",
        ["auto", "65", "80", "90", "valise", "valise p (petits)", "valise g (grands)", 
         "valise s (même taille)", "p:s", "g:s"],
        help="Auto = optimisation automatique"
    )
    
    # TRAVERSINS
    st.subheader("7. Traversins (optionnel)")
    has_traversins = st.checkbox("Ajouter des traversins")
    if has_traversins:
        traversins_list = st.multiselect(
            "Position",
            ["Gauche (g)", "Droite (d)", "Bas (b)"]
        )
        traversins = ",".join([t[0].split()[0].lower() for t in traversins_list]) if traversins_list else None
    else:
        traversins = None
    
    # MOUSSE ET TISSU
    st.subheader("8. Mousse & Tissu")
    type_mousse = st.selectbox("Type de mousse", ["D25", "D30", "HR35", "HR45"])
    epaisseur = st.number_input("Épaisseur (cm)", min_value=15, max_value=35, value=25, step=5)
    
    # COULEURS
    st.subheader("9. Couleurs")
    couleur_assise = st.text_input("Assise", value="gris très clair presque blanc")
    couleur_acc = st.text_input("Accoudoirs", value="gris")
    couleur_dossier = st.text_input("Dossiers", value="gris clair")
    couleur_coussins = st.text_input("Coussins", value="taupe")
    
    couleurs = {
        "assise": couleur_assise,
        "accoudoirs": couleur_acc,
        "dossiers": couleur_dossier,
        "coussins": couleur_coussins
    }
    
    # OPTIONS SUPPLÉMENTAIRES
    st.subheader("10. Options")
    nb_coussins_deco = st.number_input("Coussins déco", min_value=0, max_value=10, value=0)
    nb_traversins_supp = st.number_input("Traversins supplémentaires", min_value=0, max_value=5, value=0)
    has_surmatelas = st.checkbox("Surmatelas")
    
    # INFORMATIONS CLIENT
    st.subheader("11. Informations Client")
    nom_client = st.text_input("Nom du client")
    email_client = st.text_input("Email (optionnel)")

# COLONNE DROITE - APERÇU
with col2:
    st.header("👁️ Aperçu du Canapé")
    
    # Bouton de génération
    if st.button("🎨 Générer l'Aperçu", type="primary", use_container_width=True):
        with st.spinner("Génération du schéma en cours..."):
            try:
                # TODO: Intégrer votre code de génération de schéma ici
                # Pour l'instant, on affiche un placeholder
                st.success("✅ Schéma généré avec succès !")
                
                # Placeholder pour l'image
                st.info("📐 Le schéma du canapé apparaîtra ici")
                
                # Affichage des informations techniques
                st.markdown("### 📊 Composition Technique")
                
                # Calcul du prix
                prix_details = calculer_prix_total(
                    type_canape=type_canape,
                    tx=tx, ty=ty, tz=tz,
                    profondeur=profondeur,
                    type_coussins=type_coussins,
                    type_mousse=type_mousse,
                    epaisseur=epaisseur,
                    acc_left=acc_left,
                    acc_right=acc_right,
                    acc_bas=acc_bas,
                    dossier_left=dossier_left,
                    dossier_bas=dossier_bas,
                    dossier_right=dossier_right,
                    nb_coussins_deco=nb_coussins_deco,
                    nb_traversins_supp=nb_traversins_supp,
                    has_surmatelas=has_surmatelas,
                    has_meridienne=has_meridienne
                )
                
                # Affichage du détail des prix
                col_prix1, col_prix2 = st.columns(2)
                
                with col_prix1:
                    st.markdown("**Composants :**")
                    for item, prix in prix_details['details'].items():
                        st.write(f"• {item}: {prix}€")
                
                with col_prix2:
                    st.markdown("**Récapitulatif :**")
                    st.metric("Sous-total", f"{prix_details['sous_total']}€")
                    st.metric("TVA (20%)", f"{prix_details['tva']}€")
                
                st.markdown("---")
                st.markdown(f"### 💰 **TOTAL TTC : {prix_details['total_ttc']}€**")
                
            except Exception as e:
                st.error(f"❌ Erreur lors de la génération : {str(e)}")
    
    # Bouton de génération PDF
    st.markdown("---")
    if st.button("📄 Générer le Devis PDF", use_container_width=True):
        with st.spinner("Création du PDF en cours..."):
            try:
                # Préparation des données
                config = {
                    'type_canape': type_canape,
                    'dimensions': {'tx': tx, 'ty': ty, 'tz': tz, 'profondeur': profondeur},
                    'accoudoirs': {'gauche': acc_left, 'droit': acc_right, 'bas': acc_bas},
                    'dossiers': {'gauche': dossier_left, 'bas': dossier_bas, 'droit': dossier_right},
                    'meridienne': {'side': meridienne_side, 'longueur': meridienne_len},
                    'coussins': type_coussins,
                    'traversins': traversins,
                    'mousse': {'type': type_mousse, 'epaisseur': epaisseur},
                    'couleurs': couleurs,
                    'options': {
                        'coussins_deco': nb_coussins_deco,
                        'traversins_supp': nb_traversins_supp,
                        'surmatelas': has_surmatelas
                    },
                    'client': {'nom': nom_client, 'email': email_client}
                }
                
                # Génération du PDF
                pdf_buffer = generer_pdf_devis(config, prix_details)
                
                # Téléchargement
                st.download_button(
                    label="⬇️ Télécharger le Devis PDF",
                    data=pdf_buffer,
                    file_name=f"devis_canape_{nom_client.replace(' ', '_')}.pdf",
                    mime="application/pdf"
                )
                
                st.success("✅ PDF généré avec succès !")
                
            except Exception as e:
                st.error(f"❌ Erreur lors de la création du PDF : {str(e)}")

# FOOTER
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>🛋️ Générateur de Devis Canapés Sur Mesure v1.0</p>
    <p>Développé pour votre entreprise</p>
</div>
""", unsafe_allow_html=True)