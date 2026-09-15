import os

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus import Image as RLImage

from config import Config


def get_proportional_image(image_path, max_w, max_h):
    """
    Returns a ReportLab Image flowable scaled to fit within max_w and max_h,
    strictly maintaining the original image's aspect ratio.
    """
    if not image_path or not os.path.exists(image_path):
        return None
    try:
        with PILImage.open(image_path) as pimg:
            orig_w, orig_h = pimg.size
        if orig_w <= 0 or orig_h <= 0:
            return None
        aspect = orig_w / orig_h
        target_w = max_w
        target_h = max_w / aspect
        if target_h > max_h:
            target_h = max_h
            target_w = max_h * aspect
        rl_img = RLImage(image_path, width=target_w, height=target_h)
        rl_img.hAlign = "CENTER"
        return rl_img
    except Exception as e:
        print(f"[PDFService] Error loading image {image_path}: {e}")
        return None


def generate_evaluation_pdf(evaluation):
    """
    Generates an official agricultural quality assessment PDF for an evaluation.
    Conforms to government/APMC procurement documentation standards:
    - Page 1: Official 1-page executive procurement certificate with primary sample angle.
    - Page 2+: High-resolution Multi-Angle Visual Assessment Log (Annexure) when multiple angles exist.
    - All photos strictly preserve original aspect ratios without squashing, congestion, or distortion.
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

    notice_box_style = ParagraphStyle(
        "NoticeBox",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#166534")
    )

    annexure_title_style = ParagraphStyle(
        "AnnexureTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#0f5132"),
        alignment=1
    )

    annexure_sub_style = ParagraphStyle(
        "AnnexureSub",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#4b5563"),
        alignment=1
    )

    card_header_style = ParagraphStyle(
        "CardHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#0f5132"),
        alignment=1
    )

    card_stats_style = ParagraphStyle(
        "CardStats",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#374151"),
        alignment=1
    )

    card_badge_style = ParagraphStyle(
        "CardBadge",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9.5,
        alignment=1
    )

    elements = []

    # =========================================================================
    # PAGE 1: OFFICIAL PROCUREMENT ASSESSMENT CERTIFICATE
    # =========================================================================

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
            Paragraph("<b>STATUS:</b> <font color='#0f5132'><b>OFFICIALLY VERIFIED</b></font>", cell_bold_style)
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

    # 5. Annotated Image Section on Page 1
    eval_images = list(evaluation.images) if evaluation.images else []
    total_imgs = evaluation.total_images or len(eval_images) or 1

    if total_imgs <= 1:
        # Single image evaluation: Display single image with aspect ratio preserved
        single_path = eval_images[0].annotated_image_path if eval_images else evaluation.annotated_image_path
        elements.append(Paragraph("<b>AI ANNOTATED ASSESSMENT IMAGE</b>", section_header_style))
        img_flow = get_proportional_image(single_path, max_w=460, max_h=130)
        if img_flow:
            elements.append(img_flow)
            elements.append(Spacer(1, 4))
    elif total_imgs in (2, 3) and len(eval_images) == total_imgs:
        # 2 or 3 images: display side-by-side cleanly with aspect ratios preserved
        elements.append(Paragraph(f"<b>AI ANNOTATED ASSESSMENT IMAGES ({total_imgs} Sample Perspectives)</b>", section_header_style))
        col_w = 539.0 / total_imgs
        img_cells = []
        for img_rec in sorted(eval_images, key=lambda x: x.image_order):
            img_flow = get_proportional_image(img_rec.annotated_image_path, max_w=col_w - 14, max_h=110)
            cell_content = [
                Paragraph(f"<b>Angle #{img_rec.image_order}</b> ({img_rec.total_onions} bulbs)", cell_bold_style),
                Spacer(1, 2)
            ]
            if img_flow:
                cell_content.append(img_flow)
            img_cells.append(cell_content)
        
        strip_table = Table([img_cells], colWidths=[col_w] * total_imgs)
        strip_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(strip_table)
        elements.append(Spacer(1, 4))
    else:
        # Multi-angle batch (4+ angles): Show primary perspective sample on Page 1
        # and full comprehensive photo log in the Annexure
        primary_path = eval_images[0].annotated_image_path if eval_images else evaluation.annotated_image_path
        elements.append(Paragraph(f"<b>AI ANNOTATED ASSESSMENT — PRIMARY SAMPLE PERSPECTIVE (Angle 1 of {total_imgs})</b>", section_header_style))
        img_flow = get_proportional_image(primary_path, max_w=440, max_h=115)
        if img_flow:
            elements.append(img_flow)
            elements.append(Spacer(1, 3))
        
        # Informative notice directing viewer to the Annexure
        notice_data = [
            [
                Paragraph(
                    f"<b>MULTI-ANGLE BATCH NOTICE:</b> Consignment evaluated across <b>{total_imgs} photographic angles</b> "
                    f"({evaluation.total_onions} total bulbs). To preserve optical clarity and avoid visual congestion, "
                    f"all individual angle photographs with bounding boxes and defect breakdowns are cataloged in the <b>Multi-Angle Annexure (Pages 2+)</b>.",
                    notice_box_style
                )
            ]
        ]
        notice_table = Table(notice_data, colWidths=[539])
        notice_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0fdf4")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#86efac")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(notice_table)
        elements.append(Spacer(1, 4))

    # 6. Quality Summary Box
    summary_box_data = [
        [Paragraph("<b>QUALITY SUMMARY</b>", section_header_style)],
        [Paragraph(evaluation.quality_summary or "Quality assessment successfully completed.", summary_text_style)]
    ]
    summary_table = Table(summary_box_data, colWidths=[539])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 5))

    # 7. Officer Verification & Disclaimer
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
                "Digitally Authenticated<br/>"
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
    elements.append(Spacer(1, 3))

    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e5e7eb"), spaceBefore=2, spaceAfter=3))
    elements.append(Paragraph(
        "<b>Disclaimer:</b> AI-assisted evaluation. Final procurement decisions remain subject to applicable procurement procedures and officer verification.",
        disclaimer_style
    ))

    # =========================================================================
    # MULTI-ANGLE VISUAL ASSESSMENT LOG (ANNEXURE) - PAGES 2+
    # =========================================================================
    if total_imgs > 1 and len(eval_images) > 0:
        elements.append(PageBreak())

        # Annexure Header Banner
        elements.append(Paragraph("ONIONGRADE AI — MULTI-ANGLE INSPECTION ANNEXURE", annexure_title_style))
        elements.append(Paragraph("OFFICIAL PHOTOGRAPHIC QUALITY AUDIT & PER-ANGLE BULB DETECTION LOG", annexure_sub_style))
        elements.append(Spacer(1, 5))

        # Annexure Meta Bar
        annex_meta_data = [
            [
                Paragraph(f"<b>REPORT ID:</b> {report_id}", cell_bold_style),
                Paragraph(f"<b>FARMER:</b> {farmer_user.name if farmer_user else 'N/A'}", cell_bold_style),
                Paragraph(f"<b>TOTAL ANGLES:</b> {total_imgs} Sample Angles", cell_bold_style),
                Paragraph(f"<b>TOTAL BULBS:</b> {evaluation.total_onions}", cell_bold_style)
            ]
        ]
        annex_meta_table = Table(annex_meta_data, colWidths=[134, 135, 135, 135])
        annex_meta_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0fdf4")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#bbf7d0")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(annex_meta_table)
        elements.append(Spacer(1, 8))

        def build_angle_card(img_rec):
            defect_cnt = (img_rec.rotten_count or 0) + (img_rec.sprouted_count or 0)
            damaged_cnt = img_rec.damaged_count or 0
            if defect_cnt == 0 and damaged_cnt == 0:
                verdict_html = "<font color='#0f5132'><b>STATUS: 100% Grade A (Healthy)</b></font>"
                badge_bg = colors.HexColor("#f0fdf4")
            elif defect_cnt == 0:
                verdict_html = f"<font color='#0284c7'><b>STATUS: Standard Grade ({damaged_cnt} URS)</b></font>"
                badge_bg = colors.HexColor("#f0f9ff")
            else:
                verdict_html = f"<font color='#b91c1c'><b>DEFECT DETECTED: {defect_cnt} Rejected Bulb(s)</b></font>"
                badge_bg = colors.HexColor("#fef2f2")

            img_flow = get_proportional_image(img_rec.annotated_image_path, max_w=248, max_h=126)
            if not img_flow:
                img_flow = Paragraph("<i>Image preview unavailable</i>", cell_value_style)

            card_data = [
                [Paragraph(f"<b>Angle Sample #{img_rec.image_order}</b> &nbsp;|&nbsp; <b>{img_rec.total_onions} Bulbs Detected</b>", card_header_style)],
                [Paragraph(f"Healthy: <b>{img_rec.healthy_count}</b> &bull; Damaged: <b>{img_rec.damaged_count}</b> &bull; Rotten: <b>{img_rec.rotten_count}</b> &bull; Sprouted: <b>{img_rec.sprouted_count}</b>", card_stats_style)],
                [img_flow],
                [Paragraph(verdict_html, card_badge_style)]
            ]
            card_table = Table(card_data, colWidths=[263])
            card_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#f8fafc")),
                ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#ffffff")),
                ("BACKGROUND", (0, 3), (-1, 3), badge_bg),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#e2e8f0")),
                ("LINEBELOW", (0, 1), (-1, 1), 0.5, colors.HexColor("#e2e8f0")),
                ("LINEBELOW", (0, 2), (-1, 2), 0.5, colors.HexColor("#e2e8f0")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]))
            return card_table

        def build_batch_summary_card():
            tot = evaluation.total_onions or 1
            g_pct = round((evaluation.grade_a_count / tot) * 100, 1)
            u_pct = round((evaluation.urs_count / tot) * 100, 1)
            r_pct = round((evaluation.rejected_count / tot) * 100, 1)
            
            summary_card_data = [
                [Paragraph("<b>CONSOLIDATED BATCH AUDIT</b>", card_header_style)],
                [Paragraph(f"Sample Perspectives: <b>{total_imgs} Angles Evaluated</b>", card_stats_style)],
                [
                    Paragraph(
                        f"<b>Total Bulbs Evaluated:</b> {evaluation.total_onions}<br/>"
                        f"<b>Grade A (Healthy):</b> {evaluation.grade_a_count} ({g_pct}%)<br/>"
                        f"<b>URS (Under Standard):</b> {evaluation.urs_count} ({u_pct}%)<br/>"
                        f"<b>Rejected (Defective):</b> {evaluation.rejected_count} ({r_pct}%)<br/>"
                        f"<b>Batch Quality Score:</b> <b>{q_score_str}</b><br/>"
                        f"<b>Overall Classification:</b> <font color='#0f5132'><b>{evaluation.overall_result}</b></font>",
                        cell_value_style
                    )
                ],
                [Paragraph("<font color='#0f5132'><b>OFFICIAL AI QUALITY CERTIFICATION</b></font>", card_badge_style)]
            ]
            sum_table = Table(summary_card_data, colWidths=[263])
            sum_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ecfdf5")),
                ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#f8fafc")),
                ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#ffffff")),
                ("BACKGROUND", (0, 3), (-1, 3), colors.HexColor("#f0fdf4")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#10b981")),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#bbf7d0")),
                ("LINEBELOW", (0, 1), (-1, 1), 0.5, colors.HexColor("#e2e8f0")),
                ("LINEBELOW", (0, 2), (-1, 2), 0.5, colors.HexColor("#e2e8f0")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]))
            return sum_table

        sorted_images = sorted(eval_images, key=lambda x: x.image_order)
        rows_of_cards = []
        for i in range(0, len(sorted_images), 2):
            left_card = build_angle_card(sorted_images[i])
            if i + 1 < len(sorted_images):
                right_card = build_angle_card(sorted_images[i + 1])
            else:
                right_card = build_batch_summary_card()
            rows_of_cards.append([left_card, right_card])

        grid_table = Table(rows_of_cards, colWidths=[267, 267])
        grid_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ]))
        elements.append(grid_table)
        elements.append(Spacer(1, 6))

        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceBefore=2, spaceAfter=3))
        elements.append(Paragraph(
            "<b>Annexure Note:</b> This multi-angle photo audit log provides official visual documentation for APMC procurement records. "
            "Each onion bulb is sequentially indexed and validated across batch sample perspectives by OnionGrade AI.",
            disclaimer_style
        ))

    # Build PDF
    doc.build(elements)
    file_size = os.path.getsize(pdf_path) if os.path.exists(pdf_path) else 0

    return pdf_filename, pdf_path, file_size
