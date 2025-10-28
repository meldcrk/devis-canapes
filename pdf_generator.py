"""
Module de génération de PDF pour les devis de canapés
Crée un PDF professionnel avec schéma et détails prix
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from io import BytesIO
from datetime import datetime

def generer_pdf_devis(config, prix_details):
    """
    Génère un PDF de devis professionnel
    
    Paramètres:
        config: dict avec toutes les configurations du canapé
        prix_details: dict avec les détails de prix
    
    Retourne:
        BytesIO contenant le PDF
    """
    
    # Création du buffer pour le PDF
    buffer = BytesIO()
    
    # Création du canvas PDF
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # ==================
    # PAGE 1 - SCHÉMA
    # ==================
    
    # En-tête
    c.setFont("Helvetica-Bold", 24)
    c.drawString(2*cm, height - 2*cm, "DEVIS CANAPÉ SUR MESURE")
    
    c.setFont("Helvetica", 10)
    c.drawString(2*cm, height - 2.5*cm, f"Date: {datetime.now().strftime('%d/%m/%Y')}")
    c.drawString(2*cm, height - 3*cm, f"Client: {config['client']['nom']}")
    if config['client']['email']:
        c.drawString(2*cm, height - 3.5*cm, f"Email: {config['client']['email']}")
    
    # Ligne de séparation
    c.line(2*cm, height - 4*cm, width - 2*cm, height - 4*cm)
    
    # Section "Configuration"
    y_pos = height - 5*cm
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2*cm, y_pos, "CONFIGURATION DU CANAPÉ")
    
    y_pos -= 0.8*cm
    c.setFont("Helvetica", 11)
    
    # Type de canapé
    c.drawString(2*cm, y_pos, f"Type: {config['type_canape']}")
    y_pos -= 0.6*cm
    
    # Dimensions
    dims = config['dimensions']
    c.drawString(2*cm, y_pos, f"Dimensions:")
    y_pos -= 0.5*cm
    c.setFont("Helvetica", 10)
    c.drawString(3*cm, y_pos, f"• Largeur (Tx): {dims['tx']} cm")
    y_pos -= 0.5*cm
    if dims['ty']:
        c.drawString(3*cm, y_pos, f"• Hauteur gauche (Ty): {dims['ty']} cm")
        y_pos -= 0.5*cm
    if dims['tz']:
        c.drawString(3*cm, y_pos, f"• Hauteur droite (Tz): {dims['tz']} cm")
        y_pos -= 0.5*cm
    c.drawString(3*cm, y_pos, f"• Profondeur: {dims['profondeur']} cm")
    y_pos -= 0.8*cm
    
    # Accoudoirs
    c.setFont("Helvetica", 11)
    c.drawString(2*cm, y_pos, "Accoudoirs:")
    y_pos -= 0.5*cm
    c.setFont("Helvetica", 10)
    accoudoirs = []
    if config['accoudoirs']['gauche']:
        accoudoirs.append("Gauche")
    if config['accoudoirs']['droit']:
        accoudoirs.append("Droit")
    if config['accoudoirs']['bas']:
        accoudoirs.append("Bas")
    c.drawString(3*cm, y_pos, "• " + ", ".join(accoudoirs) if accoudoirs else "• Aucun")
    y_pos -= 0.8*cm
    
    # Dossiers
    c.setFont("Helvetica", 11)
    c.drawString(2*cm, y_pos, "Dossiers:")
    y_pos -= 0.5*cm
    c.setFont("Helvetica", 10)
    dossiers = []
    if config['dossiers']['gauche']:
        dossiers.append("Gauche")
    if config['dossiers']['bas']:
        dossiers.append("Bas")
    if config['dossiers']['droit']:
        dossiers.append("Droit")
    c.drawString(3*cm, y_pos, "• " + ", ".join(dossiers) if dossiers else "• Aucun")
    y_pos -= 0.8*cm
    
    # Méridienne
    if config['meridienne']['side']:
        c.setFont("Helvetica", 11)
        c.drawString(2*cm, y_pos, "Méridienne:")
        y_pos -= 0.5*cm
        c.setFont("Helvetica", 10)
        c.drawString(3*cm, y_pos, f"• Côté: {config['meridienne']['side']}")
        y_pos -= 0.5*cm
        c.drawString(3*cm, y_pos, f"• Longueur: {config['meridienne']['longueur']} cm")
        y_pos -= 0.8*cm
    
    # Coussins et mousse
    c.setFont("Helvetica", 11)
    c.drawString(2*cm, y_pos, "Coussins & Mousse:")
    y_pos -= 0.5*cm
    c.setFont("Helvetica", 10)
    c.drawString(3*cm, y_pos, f"• Type coussins: {config['coussins']}")
    y_pos -= 0.5*cm
    c.drawString(3*cm, y_pos, f"• Mousse: {config['mousse']['type']}")
    y_pos -= 0.5*cm
    c.drawString(3*cm, y_pos, f"• Épaisseur: {config['mousse']['epaisseur']} cm")
    y_pos -= 0.8*cm
    
    # Couleurs
    c.setFont("Helvetica", 11)
    c.drawString(2*cm, y_pos, "Couleurs:")
    y_pos -= 0.5*cm
    c.setFont("Helvetica", 10)
    for partie, couleur in config['couleurs'].items():
        c.drawString(3*cm, y_pos, f"• {partie.capitalize()}: {couleur}")
        y_pos -= 0.5*cm
    
    # Zone pour le schéma (placeholder)
    y_pos -= 1*cm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, y_pos, "SCHÉMA DU CANAPÉ")
    y_pos -= 0.5*cm
    
    # Rectangle pour le schéma
    c.setStrokeColor(colors.grey)
    c.setFillColor(colors.lightgrey)
    c.rect(2*cm, y_pos - 8*cm, width - 4*cm, 8*cm, fill=1)
    
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 10)
    c.drawCentredString(width/2, y_pos - 4*cm, "Le schéma sera inséré ici")
    c.drawCentredString(width/2, y_pos - 4.5*cm, "(Généré par le code Python)")
    
    # Pied de page
    c.setFont("Helvetica", 8)
    c.drawCentredString(width/2, 1*cm, "Page 1/2 - Devis valable 30 jours")
    
    # ==================
    # PAGE 2 - PRIX
    # ==================
    
    c.showPage()  # Nouvelle page
    
    # En-tête page 2
    c.setFont("Helvetica-Bold", 24)
    c.drawString(2*cm, height - 2*cm, "DÉTAIL DU PRIX")
    
    c.setFont("Helvetica", 10)
    c.drawString(2*cm, height - 2.5*cm, f"Client: {config['client']['nom']}")
    
    # Ligne de séparation
    c.line(2*cm, height - 3*cm, width - 2*cm, height - 3*cm)
    
    # Préparation des données pour le tableau
    table_data = [
        ['DÉSIGNATION', 'PRIX (€)']
    ]
    
    for item, prix in prix_details['details'].items():
        table_data.append([item, f"{prix:.2f}"])
    
    # Ligne vide
    table_data.append(['', ''])
    
    # Sous-total
    table_data.append(['SOUS-TOTAL HT', f"{prix_details['sous_total']:.2f}"])
    
    # TVA
    table_data.append(['TVA (20%)', f"{prix_details['tva']:.2f}"])
    
    # Ligne vide
    table_data.append(['', ''])
    
    # Total
    table_data.append(['TOTAL TTC', f"{prix_details['total_ttc']:.2f}"])
    
    # Création du tableau
    table = Table(table_data, colWidths=[12*cm, 4*cm])
    
    # Style du tableau
    style = TableStyle([
        # En-tête
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        
        # Corps du tableau
        ('BACKGROUND', (0, 1), (-1, -4), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        
        # Sous-total
        ('FONTNAME', (0, -3), (-1, -3), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -3), (-1, -3), 11),
        
        # TVA
        ('FONTNAME', (0, -2), (-1, -2), 'Helvetica'),
        
        # Total
        ('BACKGROUND', (0, -1), (-1, -1), colors.darkgreen),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 14),
        ('ALIGN', (0, -1), (-1, -1), 'CENTER'),
        
        # Bordures
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BOX', (0, 0), (-1, -1), 2, colors.black),
    ])
    
    table.setStyle(style)
    
    # Position du tableau
    table.wrapOn(c, width, height)
    table.drawOn(c, 2*cm, height - 4*cm - len(table_data)*0.6*cm)
    
    # Conditions de paiement
    y_pos = height - 4*cm - len(table_data)*0.6*cm - 2*cm
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, y_pos, "CONDITIONS DE PAIEMENT")
    
    y_pos -= 0.8*cm
    c.setFont("Helvetica", 10)
    c.drawString(2*cm, y_pos, "• Acompte de 30% à la commande")
    y_pos -= 0.5*cm
    c.drawString(2*cm, y_pos, "• Solde à la livraison")
    y_pos -= 0.5*cm
    c.drawString(2*cm, y_pos, "• Délai de fabrication: 4 à 6 semaines")
    y_pos -= 0.5*cm
    c.drawString(2*cm, y_pos, "• Garantie: 2 ans pièces et main d'œuvre")
    
    # Notes importantes
    y_pos -= 1.5*cm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2*cm, y_pos, "NOTES IMPORTANTES:")
    
    y_pos -= 0.6*cm
    c.setFont("Helvetica", 9)
    c.drawString(2*cm, y_pos, "• Les dimensions peuvent varier de ±2cm")
    y_pos -= 0.4*cm
    c.drawString(2*cm, y_pos, "• Les couleurs peuvent légèrement différer selon l'écran")
    y_pos -= 0.4*cm
    c.drawString(2*cm, y_pos, "• Installation gratuite dans un rayon de 50km")
    
    # Signature
    y_pos -= 2*cm
    c.line(2*cm, y_pos, 8*cm, y_pos)
    c.line(width - 8*cm, y_pos, width - 2*cm, y_pos)
    
    y_pos -= 0.5*cm
    c.setFont("Helvetica", 9)
    c.drawString(2*cm, y_pos, "Signature du client")
    c.drawString(width - 8*cm, y_pos, "Signature de l'entreprise")
    
    y_pos -= 0.3*cm
    c.drawString(2*cm, y_pos, "Date: _________________")
    c.drawString(width - 8*cm, y_pos, f"Date: {datetime.now().strftime('%d/%m/%Y')}")
    
    # Pied de page
    c.setFont("Helvetica", 8)
    c.drawCentredString(width/2, 1*cm, "Page 2/2 - Merci de votre confiance")
    
    # ==================
    # FINALISATION
    # ==================
    
    c.save()
    buffer.seek(0)
    return buffer