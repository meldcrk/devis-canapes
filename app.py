"""
Application Streamlit pour générer des devis de canapés sur mesure
Compatible Streamlit Cloud - Sans turtle !
"""

import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from io import BytesIO
from PIL import Image

# Import de vos modules
from pricing import calculer_prix_total
from pdf_generator import generer_pdf_devis

# Configuration de la page
st.set_page_config(
    page_title="Générateur de Devis Canapés",
    page_icon="🛋️",
    layout="wide"
)

# Fonction pour dessiner le canapé avec matplotlib
def dessiner_canape(type_canape, tx, ty, tz, profondeur, acc_left, acc_right, acc_bas, 
                    dossier_left, dossier_bas, dossier_right, meridienne_side, meridienne_len):
    """
    Dessine un schéma simple du canapé avec matplotlib
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Couleurs
    color_assise = '#E8E8E8'
    color_acc = '#A0A0A0'
    color_dossier = '#C0C0C0'
    
    # Échelle
    scale = 0.01  # 1cm = 0.01 unité
    
    if "Simple" in type_canape:
        # Canapé simple
        # Assise
        rect_assise = patches.Rectangle((0, 0), tx*scale, profondeur*scale, 
                                        linewidth=2, edgecolor='black', facecolor=color_assise)
        ax.add_patch(rect_assise)
        
        # Dossier
        if dossier_bas:
            rect_dossier = patches.Rectangle((0, profondeur*scale), tx*scale, 10*scale,
                                            linewidth=2, edgecolor='black', facecolor=color_dossier)
            ax.add_patch(rect_dossier)
        
        # Accoudoirs
        if acc_left:
            rect_acc_l = patches.Rectangle((-10*scale, 0), 10*scale, profondeur*scale,
                                          linewidth=2, edgecolor='black', facecolor=color_acc)
            ax.add_patch(rect_acc_l)
        if acc_right:
            rect_acc_r = patches.Rectangle((tx*scale, 0), 10*scale, profondeur*scale,
                                          linewidth=2, edgecolor='black', facecolor=color_acc)
            ax.add_patch(rect_acc_r)
    
    elif "L" in type_canape:
        # Canapé en L
        # Partie horizontale (bas)
        rect_h = patches.Rectangle((0, 0), tx*scale, profondeur*scale,
                                   linewidth=2, edgecolor='black', facecolor=color_assise)
        ax.add_patch(rect_h)
        
        # Partie verticale (gauche)
        rect_v = patches.Rectangle((0, profondeur*scale), profondeur*scale, ty*scale,
                                   linewidth=2, edgecolor='black', facecolor=color_assise)
        ax.add_patch(rect_v)
        
        # Dossiers
        if dossier_bas:
            rect_d_b = patches.Rectangle((0, profondeur*scale), tx*scale, 10*scale,
                                        linewidth=2, edgecolor='black', facecolor=color_dossier)
            ax.add_patch(rect_d_b)
        if dossier_left:
            rect_d_l = patches.Rectangle((-10*scale, profondeur*scale), 10*scale, ty*scale,
                                        linewidth=2, edgecolor='black', facecolor=color_dossier)
            ax.add_patch(rect_d_l)
    
    else:  # U
        # Canapé en U
        # Partie bas
        rect_b = patches.Rectangle((0, 0), tx*scale, profondeur*scale,
                                   linewidth=2, edgecolor='black', facecolor=color_assise)
        ax.add_patch(rect_b)
        
        # Partie gauche
        rect_l = patches.Rectangle((0, profondeur*scale), profondeur*scale, ty*scale,
                                   linewidth=2, edgecolor='black', facecolor=color_assise)
        ax.add_patch(rect_l)
        
        # Partie droite
        rect_r = patches.Rectangle((tx*scale - profondeur*scale, profondeur*scale), 
                                   profondeur*scale, tz*scale,
                                   linewidth=2, edgecolor='black', facecolor=color_assise)
        ax.add_patch(rect_r)
        
        # Dossiers
        if dossier_bas:
            rect_d_b = patches.Rectangle((profondeur*scale, profondeur*scale), 
                                        (tx-2*profondeur)*scale, 10*scale,
                                        linewidth=2, edgecolor='black', facecolor=color_dossier)
            ax.add_patch(rect_d_b)
    
    # Méridienne (cercle pour indiquer)
    if meridienne_side:
        if meridienne_side == 'g':
            circle = plt.Circle((-5*scale, profondeur*scale/2), 3*scale, color='red', alpha=0.5)
            ax.add_patch(circle)
            ax.text(-5*scale, profondeur*scale/2 + 5*scale, 'Méridienne', ha='center')
        elif meridienne_side == 'd':
            circle = plt.Circle(((tx+5)*scale, profondeur*scale/2), 3*scale, color='red', alpha=0.5)
            ax.add_patch(circle)
            ax.text((tx+5)*scale, profondeur*scale/2 + 5*scale, 'Méridienne', ha='center')
    
    # Configuration des axes
    ax.set_aspect('equal')
    ax.set_xlim(-20*scale, (tx+20)*scale)
    ax.set_ylim(-20*scale, max(profondeur, ty if ty else 0, tz if tz else 0)*scale + 30*scale)
    ax.grid(True, alpha=0.3)
    ax.set_xlabel('Dimensions en cm (échelle)')
    ax.set_title(f'Schéma du Canapé - {type_canape}', fontsize=14, fontweight='bold')
    
    return fig

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
    dossier_right = st.checkbox("Dossier Droit", value=True) if ("U" in type_canape or "L" not in type_canape) else False
    
    # MÉRIDIENNE
    st.subheader("5. Méridienne (optionnel)")
    has_meridienne = st.checkbox("Ajouter une méridienne")
    if has_meridienne:
        meridienne_side = st.selectbox("Côté", ["Gauche (g)", "Droite (d)", "Bas (b)"])
        meridienne_len = st.number_input("Longueur (cm)", min_value=30, max_value=200, value=100, step=10)
        meridienne_side = meridienne_side[0].lower()
    else:
        meridienne_side = None
        meridienne_len = 0
    
    # COUSSINS
    st.subheader("6. Coussins")
    type_coussins = st.selectbox(
        "Type de coussins",
        ["auto", "65", "80", "90", "valise"],
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
        traversins = ",".join([t[0].lower() for t in traversins_list]) if traversins_list else None
    else:
        traversins = None
    
    # MOUSSE ET TISSU
    st.subheader("8. Mousse & Tissu")
    type_mousse = st.selectbox("Type de mousse", ["D25", "D30", "HR35", "HR45"])
    epaisseur = st.number_input("Épaisseur (cm)", min_value=15, max_value=35, value=25, step=5)
    
    # OPTIONS SUPPLÉMENTAIRES
    st.subheader("9. Options")
    nb_coussins_deco = st.number_input("Coussins déco", min_value=0, max_value=10, value=0)
    nb_traversins_supp = st.number_input("Traversins supplémentaires", min_value=0, max_value=5, value=0)
    has_surmatelas = st.checkbox("Surmatelas")
    
    # INFORMATIONS CLIENT
    st.subheader("10. Informations Client")
    nom_client = st.text_input("Nom du client")
    email_client = st.text_input("Email (optionnel)")

# COLONNE DROITE - APERÇU
with col2:
    st.header("👁️ Aperçu du Canapé")
    
    # Bouton de génération
    if st.button("🎨 Générer l'Aperçu", type="primary", use_container_width=True):
        with st.spinner("Génération du schéma en cours..."):
            try:
                # Dessiner le canapé
                fig = dessiner_canape(
                    type_canape, tx, ty, tz, profondeur,
                    acc_left, acc_right, acc_bas,
                    dossier_left, dossier_bas, dossier_right,
                    meridienne_side, meridienne_len
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

# FOOTER
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>🛋️ Générateur de Devis Canapés Sur Mesure v1.0</p>
</div>
""", unsafe_allow_html=True)