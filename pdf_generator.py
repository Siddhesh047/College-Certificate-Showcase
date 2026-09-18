import io
import hashlib
from datetime import datetime, timezone
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

def generate_portfolio_pdf(student):
    """
    Generates a professional, collegiate-grade Verified Achievement Transcript / Portfolio PDF
    for the given student and returns an io.BytesIO stream.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    header_title_style = ParagraphStyle(
        'HeaderTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0f172a'),
        alignment=TA_CENTER
    )
    
    header_subtitle_style = ParagraphStyle(
        'HeaderSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#2563eb'),
        alignment=TA_CENTER
    )
    
    doc_type_style = ParagraphStyle(
        'DocType',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#1e40af'),
        alignment=TA_CENTER
    )

    label_style = ParagraphStyle(
        'FieldLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#64748b')
    )

    value_style = ParagraphStyle(
        'FieldValue',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#0f172a')
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.white,
        alignment=TA_LEFT
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#1e293b'),
        alignment=TA_LEFT
    )

    table_cell_center = ParagraphStyle(
        'TableCellCenter',
        parent=table_cell_style,
        alignment=TA_CENTER
    )

    footer_style = ParagraphStyle(
        'FooterNote',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor('#94a3b8'),
        alignment=TA_CENTER
    )

    story = []

    # 1. Header Banner
    story.append(Paragraph("CELESTIAL INSTITUTE OF TECHNOLOGY & SCIENCE", header_title_style))
    story.append(Spacer(1, 3))
    story.append(Paragraph("Accredited 'A++' Grade | Center for Academic & Co-Curricular Excellence", header_subtitle_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph("OFFICIAL VERIFIED ACHIEVEMENT TRANSCRIPT & PORTFOLIO", doc_type_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2563eb'), spaceAfter=12))

    # 2. Student Information Box
    approved_certs = student.approved_certificates
    total_pts = student.total_points
    issue_date_str = datetime.now(timezone.utc).strftime('%B %d, %Y')
    
    # Hash for authenticity verification
    raw_hash_source = f"{student.id}-{student.email}-{total_pts}-{len(approved_certs)}-{issue_date_str}"
    verification_hash = hashlib.sha256(raw_hash_source.encode()).hexdigest()[:16].upper()

    info_data = [
        [
            Paragraph("<b>Student Name:</b>", label_style),
            Paragraph(student.name, value_style),
            Paragraph("<b>Roll / Student ID:</b>", label_style),
            Paragraph(student.student_id_no or "N/A", value_style)
        ],
        [
            Paragraph("<b>Department:</b>", label_style),
            Paragraph(student.department, value_style),
            Paragraph("<b>Email:</b>", label_style),
            Paragraph(student.email, value_style)
        ],
        [
            Paragraph("<b>Verified Achievements:</b>", label_style),
            Paragraph(f"<b>{len(approved_certs)} Verified</b>", value_style),
            Paragraph("<b>Cumulative Score:</b>", label_style),
            Paragraph(f"<b><font color='#16a34a'>{total_pts} Points</font></b>", value_style)
        ],
        [
            Paragraph("<b>Report Generated On:</b>", label_style),
            Paragraph(issue_date_str, value_style),
            Paragraph("<b>Verification ID:</b>", label_style),
            Paragraph(f"<code>CEL-{verification_hash}</code>", value_style)
        ]
    ]

    info_table = Table(info_data, colWidths=[1.4*inch, 2.3*inch, 1.4*inch, 2.1*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#f1f5f9')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 14))

    # 3. Verified Achievements Table
    story.append(Paragraph("<b>VERIFIED CREDENTIALS & ACHIEVEMENTS RECORD</b>", ParagraphStyle(
        'SectionHeader', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#1e3a8a')
    )))
    story.append(Spacer(1, 6))

    if not approved_certs:
        story.append(Paragraph("<i>No approved achievements on record yet.</i>", table_cell_style))
    else:
        table_rows = [
            [
                Paragraph("#", table_header_style),
                Paragraph("Achievement Title", table_header_style),
                Paragraph("Category", table_header_style),
                Paragraph("Issuing Authority / Org", table_header_style),
                Paragraph("Issue Date", table_header_style),
                Paragraph("Points", table_header_style)
            ]
        ]

        for idx, cert in enumerate(approved_certs, start=1):
            date_display = cert.issue_date.strftime('%b %d, %Y') if cert.issue_date else 'N/A'
            category_name = cert.category.name if cert.category else 'General'
            points = cert.category.points_weight if cert.category else 0

            table_rows.append([
                Paragraph(str(idx), table_cell_center),
                Paragraph(f"<b>{cert.title}</b>", table_cell_style),
                Paragraph(category_name, table_cell_style),
                Paragraph(cert.issuing_org, table_cell_style),
                Paragraph(date_display, table_cell_center),
                Paragraph(f"+{points}", table_cell_center)
            ])

        # Add total row
        table_rows.append([
            Paragraph("", table_cell_style),
            Paragraph("<b>TOTAL VERIFIED SCORE</b>", table_cell_style),
            Paragraph("", table_cell_style),
            Paragraph("", table_cell_style),
            Paragraph("", table_cell_style),
            Paragraph(f"<b>{total_pts} pts</b>", table_cell_center)
        ])

        cert_table = Table(
            table_rows,
            colWidths=[0.35*inch, 2.55*inch, 1.4*inch, 1.5*inch, 0.85*inch, 0.55*inch]
        )
        
        cert_style_cmds = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
            ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0, 0), (-1, -2), 0.5, colors.HexColor('#e2e8f0')),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e0f2fe')),
            ('LINEABOVE', (0, -1), (-1, -1), 1, colors.HexColor('#0284c7'))
        ]

        # Alternating row colors
        for i in range(1, len(table_rows) - 1):
            if i % 2 == 0:
                cert_style_cmds.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f8fafc')))

        cert_table.setStyle(TableStyle(cert_style_cmds))
        story.append(cert_table)

    story.append(Spacer(1, 25))

    # 4. Signatures & Official Validation Block
    sign_block = [
        [
            Paragraph("<b>Digitally Verified By:</b><br/><br/><i>Dean of Student Affairs</i><br/>Celestial Institute", value_style),
            Paragraph("<b>Institutional Seal:</b><br/><br/><b>[ OFFICIAL DIGITAL STAMP ]</b><br/>Status: VERIFIED VALID", ParagraphStyle('Seal', parent=value_style, alignment=TA_CENTER)),
            Paragraph("<b>Office of Registrar:</b><br/><br/><i>Controller of Examinations</i><br/>Celestial Institute", ParagraphStyle('RightSign', parent=value_style, alignment=TA_RIGHT))
        ]
    ]
    sign_table = Table(sign_block, colWidths=[2.4*inch, 2.4*inch, 2.4*inch])
    sign_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10)
    ]))
    
    story.append(KeepTogether([
        sign_table,
        Spacer(1, 15),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cbd5e1'), spaceAfter=8),
        Paragraph(
            f"This is a system-generated, digitally authenticated document issued under authority of Celestial Institute of Technology. "
            f"Verification Token: <b>CEL-VERIFY-{verification_hash}</b> | Document Ref: #{student.id:04d}-{datetime.now(timezone.utc).strftime('%Y%m%d')}",
            footer_style
        )
    ]))

    doc.build(story)
    buffer.seek(0)
    return buffer
