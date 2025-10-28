"""
Module de calcul des prix pour les canapés sur mesure
Adaptez les prix selon vos tarifs réels !
"""

# TARIFS DE BASE (à personnaliser selon vos prix)
PRIX_MOUSSE = {
    'D25': 1.5,  # €/m²
    'D30': 1.8,
    'HR35': 2.1,
    'HR45': 2.5
}

PRIX_TISSU_M2 = 30  # Prix moyen du tissu par m²
PRIX_MAIN_OEUVRE_BASE = 200  # Prix de base de la main d'œuvre

# Options
PRIX_ACCOUDOIR = 80
PRIX_DOSSIER = 120
PRIX_COUSSIN_DECO = 25
PRIX_TRAVERSIN = 35
PRIX_SURMATELAS = 150
PRIX_MERIDIENNE = 200


def calculer_surface_tissu(type_canape, tx, ty, tz, profondeur):
    """
    Calcule la surface de tissu nécessaire
    """
    if "Simple" in type_canape:
        # Surface approximative : assise + dossier + côtés
        surface = (tx * profondeur / 10000)  # Convertir cm² en m²
        surface += (tx * 60 / 10000)  # Dossier
        surface *= 1.3  # Marge pour couture et chutes
        
    elif "L" in type_canape:
        # Deux parties
        surface = (tx * profondeur / 10000) + (ty * profondeur / 10000)
        surface += ((tx + ty) * 60 / 10000)  # Dossiers
        surface *= 1.4
        
    else:  # U
        # Trois parties
        surface = (tx * profondeur / 10000) + (ty * profondeur / 10000) + (tz * profondeur / 10000)
        surface += ((tx + ty + tz) * 60 / 10000)
        surface *= 1.5
    
    return round(surface, 2)


def calculer_surface_mousse(type_canape, tx, ty, tz, profondeur, epaisseur):
    """
    Calcule le volume de mousse nécessaire
    """
    if "Simple" in type_canape:
        volume = tx * profondeur * epaisseur / 1000000  # cm³ vers m³
    elif "L" in type_canape:
        volume = (tx * profondeur + ty * profondeur) * epaisseur / 1000000
    else:  # U
        volume = (tx * profondeur + ty * profondeur + tz * profondeur) * epaisseur / 1000000
    
    return round(volume, 3)


def calculer_prix_total(type_canape, tx, ty, tz, profondeur, type_coussins, 
                       type_mousse, epaisseur, acc_left, acc_right, acc_bas,
                       dossier_left, dossier_bas, dossier_right,
                       nb_coussins_deco, nb_traversins_supp, 
                       has_surmatelas, has_meridienne):
    """
    Calcule le prix total du canapé avec détails
    """
    details = {}
    
    # 1. Tissu
    surface_tissu = calculer_surface_tissu(type_canape, tx, ty, tz, profondeur)
    prix_tissu = surface_tissu * PRIX_TISSU_M2
    details['Tissu'] = round(prix_tissu, 2)
    
    # 2. Mousse
    volume_mousse = calculer_surface_mousse(type_canape, tx, ty, tz, profondeur, epaisseur)
    prix_mousse = volume_mousse * PRIX_MOUSSE[type_mousse] * 1000  # Convertir en prix/m³
    details['Mousse'] = round(prix_mousse, 2)
    
    # 3. Structure et main d'œuvre
    complexite = 1.0
    if "L" in type_canape:
        complexite = 1.3
    elif "U" in type_canape:
        complexite = 1.6
    
    prix_structure = PRIX_MAIN_OEUVRE_BASE * complexite
    details['Structure et Fabrication'] = round(prix_structure, 2)
    
    # 4. Accoudoirs
    nb_accoudoirs = sum([acc_left, acc_right, acc_bas])
    if nb_accoudoirs > 0:
        details['Accoudoirs'] = nb_accoudoirs * PRIX_ACCOUDOIR
    
    # 5. Dossiers
    nb_dossiers = sum([dossier_left, dossier_bas, dossier_right])
    if nb_dossiers > 0:
        details['Dossiers'] = nb_dossiers * PRIX_DOSSIER
    
    # 6. Coussins déco
    if nb_coussins_deco > 0:
        details['Coussins décoratifs'] = nb_coussins_deco * PRIX_COUSSIN_DECO
    
    # 7. Traversins
    if nb_traversins_supp > 0:
        details['Traversins'] = nb_traversins_supp * PRIX_TRAVERSIN
    
    # 8. Surmatelas
    if has_surmatelas:
        details['Surmatelas'] = PRIX_SURMATELAS
    
    # 9. Méridienne
    if has_meridienne:
        details['Méridienne'] = PRIX_MERIDIENNE
    
    # Calculs finaux
    sous_total = sum(details.values())
    tva = round(sous_total * 0.20, 2)
    total_ttc = round(sous_total + tva, 2)
    
    return {
        'details': details,
        'sous_total': round(sous_total, 2),
        'tva': tva,
        'total_ttc': total_ttc,
        'surface_tissu_m2': surface_tissu,
        'volume_mousse_m3': volume_mousse
    }
