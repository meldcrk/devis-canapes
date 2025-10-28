"""
Module de génération de devis PDF
Utilise reportlab pour créer des PDF professionnels
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from io import BytesIO
from datetime import datetime


def generer_pdf_devis(config, prix_details):
    """
    Génère un PDF de devis professionnel
    
    Args:
        config: Dictionnaire avec la configuration du canapé
        prix_details: Dictionnaire avec les détails de prix
    
    Returns:
        BytesIO: Buffer contenant le PDF
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                           rightMargin=2*cm, leftMargin=2*cm,
                           topMargin=2*cm, bottomMargin=2*cm)
    
    # Conteneur pour les éléments du PDF
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Style personnalisé pour le titre
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    # Style pour les sous-titres
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#34495E'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    # En-tête
    titre = Paragraph("🛋️ DEVIS - CANAPÉ SUR MESURE", title_style)
    elements.append(titre)
    elements.append(Spacer(1, 0.5*cm))
    
    # Date et numéro de devis
    date_devis = datetime.now().strftime("%d/%m/%Y")
    numero_devis = f"DEV-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    info_devis = [
        ['Numéro de devis:', numero_devis],
        ['Date:', date_devis],
        ['Valable jusqu\'au:', datetime.now().strftime("%d/%m/%Y")]
    ]
    
    table_info = Table(info_devis, colWidths=[5*cm, 8*cm])
    table_info.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(table_info)
    elements.append(Spacer(1, 1*cm))
    
    # Informations client
    if config['client']['nom']:
        elements.append(Paragraph("INFORMATIONS CLIENT", subtitle_style))
        
        client_info = [
            ['Nom:', config['client']['nom']],
        ]
        if config['client']['email']:
            client_info.append(['Email:', config['client']['email']])
        
        table_client = Table(client_info, colWidths=[5*cm, 8*cm])
        table_client.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(table_client)
        elements.append(Spacer(1, 1*cm))
    
    # Configuration du canapé
    elements.append(Paragraph("CONFIGURATION DU CANAPÉ", subtitle_style))
    
    config_data = [
        ['Type de canapé:', config['type_canape']],
        ['Largeur (Tx):', f"{config['dimensions']['tx']} cm"],
    ]
    
    if config['dimensions']['ty']:
        config_data.append(['Hauteur gauche (Ty):', f"{config['dimensions']['ty']} cm"])
    if config['dimensions']['tz']:
        config_data.append(['Hauteur droite (Tz):', f"{config['dimensions']['tz']} cm"])
    
    config_data.append(['Profondeur:', f"{config['dimensions']['profondeur']} cm"])
    
    table_config = Table(config_data, colWidths=[6*cm, 7*cm])
    table_config.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ECF0F1')),
    ]))
    elements.append(table_config)
    elements.append(Spacer(1, 1*cm))
    
    # Détail des prix
    elements.append(Paragraph("DÉTAIL DU DEVIS", subtitle_style))
    
    # Préparer les données du tableau
    prix_data = [['Désignation', 'Prix (€)']]
    
    for item, prix in prix_details['details'].items():
        prix_data.append([item, f"{prix:.2f} €"])
    
    # Ligne de sous-total
    prix_data.append(['', ''])
    prix_data.append(['SOUS-TOTAL HT', f"{prix_details['sous_total']:.2f} €"])
    prix_data.append(['TVA (20%)', f"{prix_details['tva']:.2f} €"])
    prix_data.append(['', ''])
    
    # Ligne de total
    prix_data.append(['TOTAL TTC', f"{prix_details['total_ttc']:.2f} €"])
    
    # Créer le tableau
    table_prix = Table(prix_data, colWidths=[12*cm, 4*cm])
    
    # Style du tableau
    table_style = [
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -4), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ]
    
    # Style pour le sous-total
    sous_total_row = len(prix_data) - 4
    table_style.extend([
        ('FONTNAME', (0, sous_total_row), (-1, sous_total_row + 1), 'Helvetica-Bold'),
        ('LINEABOVE', (0, sous_total_row), (-1, sous_total_row), 1, colors.black),
    ])
    
    # Style pour le total
    total_row = len(prix_data) - 1
    table_style.extend([
        ('FONTNAME', (0, total_row), (-1, total_row), 'Helvetica-Bold'),
        ('FONTSIZE', (0, total_row), (-1, total_row), 14),
        ('BACKGROUND', (0, total_row), (-1, total_row), colors.HexColor('#2ECC71')),
        ('TEXTCOLOR', (0, total_row), (-1, total_row), colors.whitesmoke),
        ('LINEABOVE', (0, total_row), (-1, total_row), 2, colors.black),
    ])
    
    table_prix.setStyle(TableStyle(table_style))
    elements.append(table_prix)
    elements.append(Spacer(1, 2*cm))
    
    # Pied de page avec conditions
    conditions_style = ParagraphStyle(
        'Conditions',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    
    conditions_text = """
    <b>Conditions générales :</b><br/>
    • Devis valable 30 jours<br/>
    • Acompte de 30% à la commande<br/>
    • Délai de fabrication : 4 à 6 semaines<br/>
    • Livraison et installation incluses<br/>
    """
    
    elements.append(Paragraph(conditions_text, conditions_style))
    
    # Générer le PDF
    doc.build(elements)
    
    # Retourner le buffer
    buffer.seek(0)
    return buffer