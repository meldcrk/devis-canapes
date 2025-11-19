"""
Application Streamlit pour générer des devis de canapés sur mesure
Compatible Streamlit Cloud - Utilise canapematplot.py
"""

import streamlit as st
import matplotlib.pyplot as plt
from io import BytesIO
from PIL import Image

# Import des modules personnalisés
from pricing import calculer_prix_total
from pdf_generator import generer_pdf_devis

# Import des fonctions de génération de schémas depuis canapematplot
from canapematplot import (
    render_LNF, render_LF_variant, render_U2f_variant,
    render_U, render_U1F_v1, render_U1F_v2, render_U1F_v3, render_U1F_v4,
    render_Simple1
)

# Configuration de la page
st.set_page_config(
    page_title="Générateur de Devis Canapés",
    page_icon="🛋️",
    layout="wide"
)

def generer_schema_canape(type_canape, tx, ty, tz, profondeur, 
                          acc_left, acc_right, acc_bas,
                          dossier_left, dossier_bas, dossier_right,
                          meridienne_side, meridienne_len, coussins="auto"):
    """
    Génère le schéma du canapé en utilisant les fonctions de canapematplot.py
    et retourne une figure matplotlib
    """
    fig = plt.figure(figsize=(12, 8))
    
    try:
        if "Simple" in type_canape:
            render_Simple1(
                tx=tx,
                profondeur=profondeur,
                dossier=dossier_bas,
                acc_left=acc_left,
                acc_right=acc_right,
                meridienne_side=meridienne_side,
                meridienne_len=meridienne_len,
                coussins=coussins,
                window_title="Canapé Simple"
            )
            
        elif "L - Sans Angle" in type_canape:
            render_LNF(
                tx=tx,
                ty=ty,
                profondeur=profondeur,
                dossier_left=dossier_left,
                dossier_bas=dossier_bas,
                acc_left=acc_left,
                acc_bas=acc_bas,
                meridienne_side=meridienne_side,
                meridienne_len=meridienne_len,
                coussins=coussins,
                variant="auto",
                window_title="Canapé L - Sans Angle"
            )
            
        elif "L - Avec Angle" in type_canape:
            render_LF_variant(
                tx=tx,
                ty=ty,
                profondeur=profondeur,
                dossier_left=dossier_left,
                dossier_bas=dossier_bas,
                acc_left=acc_left,
                acc_bas=acc_bas,
                meridienne_side=meridienne_side,
                meridienne_len=meridienne_len,
                coussins=coussins,
                window_title="Canapé L - Avec Angle"
            )
            
        elif "U - Sans Angle" in type_canape:
            render_U(
                tx=tx,
                ty_left=ty,
                tz_right=tz,
                profondeur=profondeur,
                dossier_left=dossier_left,
                dossier_bas=dossier_bas,
                dossier_right=dossier_right,
                acc_left=acc_left,
                acc_bas=acc_bas,
                acc_right=acc_right,
                coussins=coussins,
                variant="auto",
                window_title="Canapé U - Sans Angle"
            )
            
        elif "U - 1 Angle" in type_canape:
            # Par défaut utiliser v1, mais vous pouvez ajouter un sélecteur
            render_U1F_v1(
                tx=tx,
                ty=ty,
                tz=tz,
                profondeur=profondeur,
                dossier_left=dossier_left,
                dossier_bas=dossier_bas,
                dossier_right=dossier_right,
                acc_left=acc_left,
                acc_right=acc_right,
                meridienne_side=meridienne_side,
                meridienne_len=meridienne_len,
                coussins=coussins,
                window_title="Canapé U - 1 Angle"
            )
            
        elif "U - 2 Angles" in type_canape:
            render_U2f_variant(
                tx=tx,
                ty_left=ty,
                tz_right=tz,
                profondeur=profondeur,
                dossier_left=dossier_left,
                dossier_bas=dossier_bas,
                dossier_right=dossier_right,
                acc_left=acc_left,
                acc_bas=acc_bas,
                acc_right=acc_right,
                meridienne_side=meridienne_side,
                meridienne_len=meridienne_len,
                coussins=coussins,
                window_title="Canapé U - 2 Angles"
            )
        
        # Récupérer la figure actuelle créée par matplotlib
        fig = plt.gcf()
        return fig
        
    except Exception as e:
        plt.close()
        raise Exception(f"Erreur lors de la génération du schéma : {str(e)}")

# Titre principal
st.title("🛋️ Générateur de Devis Canapés Sur Mesure")
st.markdown("---")

# FORMULAIRE PRINCIPAL
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
    dossier_right = st.checkbox("Dossier Droit", value=True) if ("U" in type_canape) else False
    
    # MÉRIDIENNE
    st.subheader("5. Méridienne (optionnel)")
    has_meridienne = st.checkbox("Ajouter une méridienne")
    if has_meridienne:
        meridienne_options = ["Gauche (g)", "Droite (d)"]
        if "L" in type_canape or "U" in type_canape:
            meridienne_options.append("Bas (b)")
        
        meridienne_side = st.selectbox("Côté", meridienne_options)
        meridienne_len = st.number_input("Longueur (cm)", min_value=30, max_value=200, value=100, step=10)
        meridienne_side = meridienne_side[0].lower()
    else:
        meridienne_side = None
        meridienne_len = 0
    
    # COUSSINS
    st.subheader("6. Coussins")
    type_coussins = st.selectbox(
        "Type de coussins",
        ["auto", "65", "80", "90", "valise", "p", "g"],
        help="Auto = optimisation automatique, valise = tailles variables optimisées"
    )
    
    # MOUSSE ET TISSU
    st.subheader("7. Mousse & Tissu")
    type_mousse = st.selectbox("Type de mousse", ["D25", "D30", "HR35", "HR45"])
    epaisseur = st.number_input("Épaisseur (cm)", min_value=15, max_value=35, value=25, step=5)
    
    # OPTIONS SUPPLÉMENTAIRES
    st.subheader("8. Options")
    nb_coussins_deco = st.number_input("Coussins déco", min_value=0, max_value=10, value=0)
    nb_traversins_supp = st.number_input("Traversins supplémentaires", min_value=0, max_value=5, value=0)
    has_surmatelas = st.checkbox("Surmatelas")
    
    # INFORMATIONS CLIENT
    st.subheader("9. Informations Client")
    nom_client = st.text_input("Nom du client")
    email_client = st.text_input("Email (optionnel)")

# COLONNE DROITE - APERÇU
with col2:
    st.header("👁️ Aperçu du Canapé")
    
    # Bouton de génération
    if st.button("🎨 Générer l'Aperçu", type="primary", use_container_width=True):
        with st.spinner("Génération du schéma en cours..."):
            try:
                # Générer le schéma
                fig = generer_schema_canape(
                    type_canape=type_canape,
                    tx=tx, ty=ty, tz=tz,
                    profondeur=profondeur,
                    acc_left=acc_left,
                    acc_right=acc_right,
                    acc_bas=acc_bas,
                    dossier_left=dossier_left,
                    dossier_bas=dossier_bas,
                    dossier_right=dossier_right,
                    meridienne_side=meridienne_side,
                    meridienne_len=meridienne_len,
                    coussins=type_coussins
                )
                
                st.pyplot(fig)
                plt.close()
                
                st.success("✅ Schéma généré avec succès !")
                
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
                
                # Affichage des prix
                st.markdown("### 📊 Détails du Devis")
                
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
                st.exception(e)  # Affiche la trace complète pour le debug
    
    # Bouton PDF
    st.markdown("---")
    if st.button("📄 Générer le Devis PDF", use_container_width=True):
        if not nom_client:
            st.warning("⚠️ Veuillez renseigner le nom du client")
        else:
            with st.spinner("Création du PDF en cours..."):
                try:
                    config = {
                        'type_canape': type_canape,
                        'dimensions': {'tx': tx, 'ty': ty, 'tz': tz, 'profondeur': profondeur},
                        'options': {
                            'acc_left': acc_left,
                            'acc_right': acc_right,
                            'acc_bas': acc_bas,
                            'dossier_left': dossier_left,
                            'dossier_bas': dossier_bas,
                            'dossier_right': dossier_right,
                            'meridienne_side': meridienne_side,
                            'meridienne_len': meridienne_len,
                            'type_coussins': type_coussins,
                            'type_mousse': type_mousse,
                            'epaisseur': epaisseur
                        },
                        'client': {'nom': nom_client, 'email': email_client}
                    }
                    
                    prix_details = calculer_prix_total(
                        type_canape=type_canape, tx=tx, ty=ty, tz=tz,
                        profondeur=profondeur, type_coussins=type_coussins,
                        type_mousse=type_mousse, epaisseur=epaisseur,
                        acc_left=acc_left, acc_right=acc_right, acc_bas=acc_bas,
                        dossier_left=dossier_left, dossier_bas=dossier_bas,
                        dossier_right=dossier_right, nb_coussins_deco=nb_coussins_deco,
                        nb_traversins_supp=nb_traversins_supp,
                        has_surmatelas=has_surmatelas, has_meridienne=has_meridienne
                    )
                    
                    pdf_buffer = generer_pdf_devis(config, prix_details)
                    
                    st.download_button(
                        label="⬇️ Télécharger le Devis PDF",
                        data=pdf_buffer,
                        file_name=f"devis_canape_{nom_client.replace(' ', '_')}.pdf",
                        mime="application/pdf"
                    )
                    
                    st.success("✅ PDF généré avec succès !")
                    
                except Exception as e:
                    st.error(f"❌ Erreur : {str(e)}")
                    st.exception(e)

# FOOTER
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>🛋️ Générateur de Devis Canapés Sur Mesure v2.0</p>
    <p>Utilise canapematplot.py pour la génération de schémas</p>
</div>
""", unsafe_allow_html=True)