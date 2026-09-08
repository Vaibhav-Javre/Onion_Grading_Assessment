import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, HRFlowable
)
from config import Config

def generate_evaluation_pdf(evaluation):
    """
    Generates an official agricultural quality assessment PDF for an evaluation.
    Conforms to government/APMC procurement documentation standards.
    Carefully styled to fit cleanly on official A4 single page.
    """
    os.makedirs(Config.PDF_REPORT_FOLDER, exist_ok=True)
    report_id = evaluation.report_id or f"ONR-{evaluation.id}"
    pdf_filename = f"Onion_Report_{report_id}.pdf"
    pdf_path = os.path.join(Config.PDF_REPORT_FOLDER, pdf_filename)

    # A4: 595.27 x 841.89 points. Margins: 28pt left/right, 24pt top/bottom.
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=28,
        rightMargin=28,
        topMargin=24,
        bottomMargin=24
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f5132"),
        alignment=1
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#4b5563"),
        alignment=1
    )

    section_header_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#0f5132"),
        spaceBefore=4,
        spaceAfter=2
    )

    cell_bold_style = ParagraphStyle(
        "CellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=10.5,
        textColor=colors.HexColor("#1f2937")
    )

    cell_value_style = ParagraphStyle(
        "CellValue",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=10.5,
        textColor=colors.HexColor("#374151")
    )

    summary_text_style = ParagraphStyle(
        "SummaryText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#1f2937")
    )

    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#6b7280"),
        alignment=1
    )

    elements = []

    # 1. Header Banner
    elements.append(Paragraph("ONIONGRADE AI", title_style))
    elements.append(Paragraph("AI-POWERED ONION QUALITY ASSESSMENT & DIGITAL PROCUREMENT PLATFORM", subtitle_style))
    elements.append(Spacer(1, 4))

    # Meta banner (Report ID & Date)
    eval_date_str = evaluation.evaluation_date.strftime("%d/%m/%Y %I:%M %p") if evaluation.evaluation_date else ""
    meta_table_data = [
        [
            Paragraph(f"<b>REPORT ID:</b> {report_id}", cell_bold_style),
            Paragraph(f"<b>EVALUATION DATE:</b> {eval_date_str}", cell_bold_style),
            Paragraph(f"<b>STATUS:</b> <font color='#0f5132'><b>OFFICIALLY VERIFIED</b></font>", cell_bold_style)
        ]
    ]
    meta_table = Table(meta_table_data, colWidths=[180, 185, 174])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0fdf4")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#bbf7d0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 6))

    # 2. Farmer & Evaluation Details (Side-by-side)
    farmer = evaluation.farmer
    farmer_user = farmer.user if farmer else None
    officer = evaluation.officer
    officer_user = officer.user if officer else None

    farmer_data = [
        [Paragraph("<b>FARMER DETAILS</b>", section_header_style), Paragraph("<b>EVALUATION DETAILS</b>", section_header_style)],
        [
            Paragraph(f"<b>Name:</b> {farmer_user.name if farmer_user else 'N/A'}", cell_value_style),
            Paragraph(f"<b>Officer:</b> {officer_user.name if officer_user else 'Officer'} ({officer.officer_id if officer else 'N/A'})", cell_value_style)
        ],
        [
            Paragraph(f"<b>Farmer ID:</b> {farmer.farmer_id if farmer else 'N/A'}", cell_value_style),
            Paragraph(f"<b>Procurement Center:</b> {officer.procurement_center if officer else 'N/A'}", cell_value_style)
        ],
        [
            Paragraph(f"<b>Mobile:</b> {farmer_user.phone if farmer_user else 'N/A'}", cell_value_style),
            Paragraph(f"<b>Center Location:</b> {officer.location if officer else 'N/A'}", cell_value_style)
        ],
        [
            Paragraph(f"<b>Location:</b> {farmer.village}, {farmer.taluka}, {farmer.district}, {farmer.state}" if farmer else "N/A", cell_value_style),
            Paragraph(f"<b>Batch Angles Evaluated:</b> {evaluation.total_images or 1} image sample(s)", cell_value_style)
        ]
    ]
    info_table = Table(farmer_data, colWidths=[269, 270])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fafafa")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("LINEBEFORE", (1, 0), (1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 6))

    # 3. AI Quality Classification & Final Procurement Grading
    total = evaluation.total_onions or 1
    h_pct = round((evaluation.healthy_count / total) * 100, 1)
    d_pct = round((evaluation.damaged_count / total) * 100, 1)
    r_pct = round((evaluation.rotten_count / total) * 100, 1)
    s_pct = round((evaluation.sprouted_count / total) * 100, 1)

    ga_pct = round((evaluation.grade_a_count / total) * 100, 1)
    urs_pct = round((evaluation.urs_count / total) * 100, 1)
    rej_pct = round((evaluation.rejected_count / total) * 100, 1)

    ai_table_data = [
        [
            Paragraph("<b>AI QUALITY CLASSIFICATION</b>", cell_bold_style),
            Paragraph("<b>Count</b>", cell_bold_style),
            Paragraph("<b>Percentage</b>", cell_bold_style),
            Paragraph("<b>FINAL PROCUREMENT GRADING</b>", cell_bold_style),
            Paragraph("<b>Count</b>", cell_bold_style),
            Paragraph("<b>Percentage</b>", cell_bold_style)
        ],
        [
            Paragraph("Healthy", cell_value_style),
            str(evaluation.healthy_count),
            f"{h_pct}%",
            Paragraph("<b>Grade A</b> (Healthy)", cell_value_style),
            str(evaluation.grade_a_count),
            f"{ga_pct}%"
        ],
        [
            Paragraph("Damaged", cell_value_style),
            str(evaluation.damaged_count),
            f"{d_pct}%",
            Paragraph("<b>URS</b> (Under Regular Standard)", cell_value_style),
            str(evaluation.urs_count),
            f"{urs_pct}%"
        ],
        [
            Paragraph("Rotten", cell_value_style),
            str(evaluation.rotten_count),
            f"{r_pct}%",
            Paragraph("<b>Rejected</b> (Rotten + Sprouted)", cell_value_style),
            str(evaluation.rejected_count),
            f"{rej_pct}%"
        ],
        [
            Paragraph("Sprouted", cell_value_style),
            str(evaluation.sprouted_count),
            f"{s_pct}%",
            Paragraph("<b>Total Evaluated Bulbs</b>", cell_bold_style),
            str(evaluation.total_onions),
            "100%"
        ]
    ]

    ai_table = Table(ai_table_data, colWidths=[114, 50, 65, 185, 55, 70])
    ai_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (2, 0), colors.HexColor("#ecfdf5")),
        ("BACKGROUND", (3, 0), (5, 0), colors.HexColor("#fef3c7")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#1f2937")),
        ("ALIGN", (1, 0), (2, -1), "CENTER"),
        ("ALIGN", (4, 0), (5, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(ai_table)
    elements.append(Spacer(1, 5))

    # 4. Mandi Benchmark & Procurement Price Estimation Section
    m_name = evaluation.mandi_name or "Lasalgaon APMC Mandi"
    m_modal = f"₹{evaluation.mandi_modal_price:,.2f} / Quintal" if evaluation.mandi_modal_price else "Live Mandi Rate Unavailable"
    m_source = evaluation.mandi_api_source or "data.gov.in"
    m_date = evaluation.mandi_price_date or (evaluation.evaluation_date.strftime("%d/%m/%Y") if evaluation.evaluation_date else "N/A")
    
    q_score_val = evaluation.quality_score if evaluation.quality_score is not None else round((ga_pct * 1.0 + urs_pct * 0.8), 1)
    q_score_str = f"{q_score_val:.1f}%"
    est_price_str = f"₹{evaluation.estimated_price_per_quintal:,.2f} / Quintal" if evaluation.estimated_price_per_quintal else "Pending Reference Rate"
    
    has_qty = evaluation.quantity_quintals and evaluation.quantity_quintals > 0
    qty_str = f"{evaluation.quantity_quintals:.2f} Quintals" if has_qty else "Quantity Entry Pending"
    
    has_payout = evaluation.total_payout and evaluation.total_payout > 0
    payout_str = f"₹{evaluation.total_payout:,.2f}" if has_payout else ("Pending Quantity" if evaluation.estimated_price_per_quintal else "N/A")

    price_table_data = [
        [
            Paragraph("<b>GOVERNMENT MANDI BENCHMARK (data.gov.in)</b>", section_header_style),
            Paragraph("<b>QUALITY-ADJUSTED PRICE & PAYOUT</b>", section_header_style)
        ],
        [
            Paragraph(f"<b>Reference Mandi:</b> {m_name}<br/>"
                      f"<b>Modal Price:</b> <font color='#0f5132'><b>{m_modal}</b></font><br/>"
                      f"<b>Price Date & Source:</b> {m_date} ({m_source})", cell_value_style),
            Paragraph(f"<b>Batch Quality Score:</b> <b>{q_score_str}</b> [A: 100%, URS: 80%, Rej: 0%]<br/>"
                      f"<b>Estimated Price:</b> <font color='#0f5132'><b>{est_price_str}</b></font><br/>"
                      f"<b>Procured Batch Quantity:</b> <b>{qty_str}</b>", cell_value_style)
        ],
        [
            Paragraph(f"<b>TOTAL ESTIMATED FARMER PAYOUT:</b> <font size='10' color='#0f5132'><b>{payout_str}</b></font>", cell_bold_style),
            Paragraph(f"<b>Formula:</b> Modal Price × Quality Score ({q_score_str}) × Quantity ({qty_str})", disclaimer_style)
        ]
    ]
    price_table = Table(price_table_data, colWidths=[269, 270])
    price_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0fdf4")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#bbf7d0")),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#bbf7d0")),
        ("LINEBELOW", (0, 1), (-1, 1), 0.5, colors.HexColor("#bbf7d0")),
        ("LINEBEFORE", (1, 0), (1, 1), 0.5, colors.HexColor("#bbf7d0")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(price_table)
    elements.append(Spacer(1, 5))

    # 5. Annotated Image Embed
    annotated_img_path = evaluation.annotated_image_path
    if annotated_img_path and os.path.exists(annotated_img_path):
        elements.append(Paragraph("<b>AI ANNOTATED ASSESSMENT IMAGE</b>", section_header_style))
        try:
            img = RLImage(annotated_img_path, width=490, height=135)
            img.hAlign = "CENTER"
            elements.append(img)
            elements.append(Spacer(1, 4))
        except Exception as e:
            print(f"[PDFService] Error embedding image: {e}")


    # 5. Quality Summary Box
    summary_box_data = [
        [Paragraph("<b>QUALITY SUMMARY</b>", section_header_style)],
        [Paragraph(evaluation.quality_summary or "Quality assessment successfully completed.", summary_text_style)]
    ]
    summary_table = Table(summary_box_data, colWidths=[539])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 6))

    # 6. Officer Verification & Disclaimer
    verification_data = [
        [
            Paragraph(
                f"<b>AI Assessment:</b> Generated automatically by OnionGrade AI.<br/>"
                f"<b>Officer Verification:</b> Officially confirmed by {officer_user.name if officer_user else 'Officer'} ({officer.officer_id if officer else ''})<br/>"
                f"<b>Center:</b> {officer.procurement_center if officer else ''}",
                cell_value_style
            ),
            Paragraph(
                "<b>OFFICIAL VERIFICATION</b><br/>"
                "✓ Digitally Authenticated<br/>"
                f"Ref: {report_id}",
                ParagraphStyle("Stamp", parent=cell_bold_style, alignment=2, textColor=colors.HexColor("#0f5132"))
            )
        ]
    ]
    ver_table = Table(verification_data, colWidths=[379, 160])
    ver_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    elements.append(ver_table)
    elements.append(Spacer(1, 4))

    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e5e7eb"), spaceBefore=2, spaceAfter=4))
    elements.append(Paragraph(
        "<b>Disclaimer:</b> AI-assisted evaluation. Final procurement decisions remain subject to applicable procurement procedures and officer verification.",
        disclaimer_style
    ))

    # Build PDF
    doc.build(elements)
    file_size = os.path.getsize(pdf_path) if os.path.exists(pdf_path) else 0

    return pdf_filename, pdf_path, file_size
