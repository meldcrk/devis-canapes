"""
Module de calcul des prix pour les canapés sur mesure
Simple et facile à modifier !
"""

# ==================
# TARIFS DE BASE
# ==================

PRIX_COUSSINS = {
    '65': 35,
    '80': 44,
    '90': 48,
    'valise': 70  # Prix pour tous les types de valise
}

PRIX_SUPPORTS = {
    'assise': 250,
    'angle': 250
}

PRIX_COMPOSANTS = {
    'accoudoir': 225,
    'dossier': 250,
    'coussin_deco': 15,
    'traversin': 30,
    'surmatelas': 80
}

# Prix de la mousse au m³
PRIX_MOUSSE_M3 = {
    'D25': 162.5,
    'D30': 163.0,
    'HR35': 163.7,
    'HR45': 164.7
}

# Prix du tissu au mètre linéaire
PRIX_TISSU_ML = {
    'standard': 74,  # Pour largeur ≤ 140 cm
    'large': 105     # Pour largeur > 140 cm
}

def calculer_prix_mousse_tissu(longueur_cm, largeur_cm, hauteur_cm, type_mousse):
    """
    Calcule le prix de la mousse + tissu pour une banquette
    
    Paramètres:
        longueur_cm: longueur en cm
        largeur_cm: largeur en cm
        hauteur_cm: hauteur (épaisseur) en cm
        type_mousse: 'D25', 'D30', 'HR35', ou 'HR45'
    
    Retourne:
        dict avec prix_mousse, prix_tissu, total
    """
    # Conversion en mètres pour le calcul
    longueur_m = longueur_cm / 100
    largeur_m = largeur_cm / 100
    hauteur_m = hauteur_cm / 100
    
    # Prix de la mousse (volume en m³ × prix au m³)
    volume_m3 = longueur_m * largeur_m * hauteur_m
    prix_mousse = volume_m3 * PRIX_MOUSSE_M3[type_mousse]
    
    # Prix du tissu (selon la largeur de la housse)
    # Largeur de la housse = largeur + 2 × épaisseur
    largeur_housse_cm = largeur_cm + (2 * hauteur_cm)
    
    if largeur_housse_cm > 140:
        prix_tissu = longueur_m * PRIX_TISSU_ML['large']
    else:
        prix_tissu = longueur_m * PRIX_TISSU_ML['standard']
    
    return {
        'prix_mousse': round(prix_mousse, 2),
        'prix_tissu': round(prix_tissu, 2),
        'total': round(prix_mousse + prix_tissu, 2)
    }

def estimer_nb_banquettes(type_canape):
    """
    Estime le nombre de banquettes selon le type de canapé
    """
    if 'Simple' in type_canape:
        return 1
    elif 'L' in type_canape:
        return 2  # Gauche + Bas
    elif 'U' in type_canape:
        return 3  # Gauche + Bas + Droite
    return 1

def estimer_nb_angles(type_canape):
    """
    Estime le nombre d'angles selon le type de canapé
    """
    if 'U2F' in type_canape:
        return 2
    elif 'U1F' in type_canape or 'LF' in type_canape:
        return 1
    return 0

def estimer_nb_coussins(type_coussins, longueur_totale):
    """
    Estime le nombre de coussins approximatif
    (sera ajusté avec le schéma réel)
    """
    if type_coussins == 'auto':
        taille_moyenne = 75
    elif type_coussins in ['65', '80', '90']:
        taille_moyenne = int(type_coussins)
    else:  # valise
        taille_moyenne = 75
    
    return max(1, int(longueur_totale / taille_moyenne))

def calculer_prix_total(type_canape, tx, ty, tz, profondeur,
                       type_coussins, type_mousse, epaisseur,
                       acc_left, acc_right, acc_bas,
                       dossier_left, dossier_bas, dossier_right,
                       nb_coussins_deco, nb_traversins_supp,
                       has_surmatelas, has_meridienne):
    """
    Calcule le prix total du canapé avec tous les détails
    
    Retourne:
        dict avec 'details', 'sous_total', 'tva', 'total_ttc'
    """
    
    details = {}
    
    # 1. SUPPORTS D'ASSISE
    nb_banquettes = estimer_nb_banquettes(type_canape)
    prix_supports_assise = nb_banquettes * PRIX_SUPPORTS['assise']
    details[f"Supports d'assise ({nb_banquettes} × {PRIX_SUPPORTS['assise']}€)"] = prix_supports_assise
    
    # 2. SUPPORTS D'ANGLE
    nb_angles = estimer_nb_angles(type_canape)
    if nb_angles > 0:
        prix_angles = nb_angles * PRIX_SUPPORTS['angle']
        details[f"Supports d'angle ({nb_angles} × {PRIX_SUPPORTS['angle']}€)"] = prix_angles
    
    # 3. ACCOUDOIRS
    nb_accoudoirs = sum([acc_left, acc_right, acc_bas])
    if nb_accoudoirs > 0:
        prix_accoudoirs = nb_accoudoirs * PRIX_COMPOSANTS['accoudoir']
        details[f"Accoudoirs ({nb_accoudoirs} × {PRIX_COMPOSANTS['accoudoir']}€)"] = prix_accoudoirs
    
    # 4. DOSSIERS
    nb_dossiers = sum([dossier_left, dossier_bas, dossier_right])
    if nb_dossiers > 0:
        prix_dossiers = nb_dossiers * PRIX_COMPOSANTS['dossier']
        details[f"Dossiers ({nb_dossiers} × {PRIX_COMPOSANTS['dossier']}€)"] = prix_dossiers
    
    # 5. COUSSINS
    # Estimation de la longueur totale pour les coussins
    longueur_totale = tx
    if ty:
        longueur_totale += ty
    if tz:
        longueur_totale += tz
    
    nb_coussins = estimer_nb_coussins(type_coussins, longueur_totale)
    
    if type_coussins in PRIX_COUSSINS:
        prix_unitaire = PRIX_COUSSINS[type_coussins]
    elif 'valise' in type_coussins.lower():
        prix_unitaire = PRIX_COUSSINS['valise']
    else:
        prix_unitaire = PRIX_COUSSINS['valise']
    
    prix_coussins = nb_coussins * prix_unitaire
    details[f"Coussins ({nb_coussins} × {prix_unitaire}€)"] = prix_coussins
    
    # 6. MOUSSE ET TISSU PAR BANQUETTE
    prix_mousse_tissu_total = 0
    
    # Banquette gauche (si existe)
    if ty:
        mt = calculer_prix_mousse_tissu(ty, profondeur, epaisseur, type_mousse)
        prix_mousse_tissu_total += mt['total']
        details[f"Mousse+Tissu Gauche ({ty}×{profondeur}×{epaisseur})"] = mt['total']
    
    # Banquette bas
    mt = calculer_prix_mousse_tissu(tx, profondeur, epaisseur, type_mousse)
    prix_mousse_tissu_total += mt['total']
    details[f"Mousse+Tissu Bas ({tx}×{profondeur}×{epaisseur})"] = mt['total']
    
    # Banquette droite (si existe)
    if tz:
        mt = calculer_prix_mousse_tissu(tz, profondeur, epaisseur, type_mousse)
        prix_mousse_tissu_total += mt['total']
        details[f"Mousse+Tissu Droite ({tz}×{profondeur}×{epaisseur})"] = mt['total']
    
    # 7. OPTIONS
    if nb_coussins_deco > 0:
        prix_deco = nb_coussins_deco * PRIX_COMPOSANTS['coussin_deco']
        details[f"Coussins déco ({nb_coussins_deco} × {PRIX_COMPOSANTS['coussin_deco']}€)"] = prix_deco
    
    if nb_traversins_supp > 0:
        prix_trav = nb_traversins_supp * PRIX_COMPOSANTS['traversin']
        details[f"Traversins ({nb_traversins_supp} × {PRIX_COMPOSANTS['traversin']}€)"] = prix_trav
    
    if has_surmatelas:
        details["Surmatelas"] = PRIX_COMPOSANTS['surmatelas']
    
    # CALCUL TOTAL
    sous_total = sum(details.values())
    tva = round(sous_total * 0.20, 2)
    total_ttc = round(sous_total + tva, 2)
    
    return {
        'details': details,
        'sous_total': sous_total,
        'tva': tva,
        'total_ttc': total_ttc
    }