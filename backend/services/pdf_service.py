import os
from datetime import datetime

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
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

_DEVANAGARI_FONTS_REGISTERED = False


def register_devanagari_fonts():
    """Registers TrueType fonts for Devanagari script (Hindi & Marathi)."""
    global _DEVANAGARI_FONTS_REGISTERED
    if _DEVANAGARI_FONTS_REGISTERED:
        return True

    try:
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        local_regular = os.path.join(backend_dir, "fonts", "mangal.ttf")
        local_bold = os.path.join(backend_dir, "fonts", "mangalb.ttf")

        reg_path = local_regular if os.path.exists(local_regular) else "C:/Windows/Fonts/mangal.ttf"
        bold_path = local_bold if os.path.exists(local_bold) else "C:/Windows/Fonts/mangalb.ttf"

        if os.path.exists(reg_path):
            pdfmetrics.registerFont(TTFont("Devanagari", reg_path))
            if os.path.exists(bold_path):
                pdfmetrics.registerFont(TTFont("Devanagari-Bold", bold_path))
            else:
                pdfmetrics.registerFont(TTFont("Devanagari-Bold", reg_path))
            pdfmetrics.registerFontFamily("Devanagari", normal="Devanagari", bold="Devanagari-Bold")
            _DEVANAGARI_FONTS_REGISTERED = True
            return True
    except Exception as e:
        print(f"[PDFService] Error registering Devanagari fonts: {e}")

    return False


TRANSLATIONS = {
    "en": {
        "title": "ONIONGRADE AI",
        "subtitle": "AI-POWERED ONION QUALITY ASSESSMENT & DIGITAL PROCUREMENT PLATFORM",
        "report_id": "REPORT ID",
        "eval_date": "EVALUATION DATE",
        "status_label": "STATUS",
        "status_val": "OFFICIALLY VERIFIED",
        "farmer_details": "FARMER DETAILS",
        "eval_details": "EVALUATION DETAILS",
        "name": "Name",
        "officer": "Officer",
        "farmer_id": "Farmer ID",
        "proc_center": "Procurement Center",
        "mobile": "Mobile",
        "center_loc": "Center Location",
        "location": "Location",
        "batch_angles": "Batch Angles Evaluated",
        "image_samples": "image sample(s)",
        "ai_classification": "AI QUALITY CLASSIFICATION",
        "final_grading": "FINAL PROCUREMENT GRADING",
        "count": "Count",
        "percentage": "Percentage",
        "healthy": "Healthy",
        "damaged": "Damaged",
        "rotten": "Rotten",
        "sprouted": "Sprouted",
        "grade_a": "Grade A (Healthy)",
        "urs": "URS (Under Regular Standard)",
        "rejected": "Rejected (Rotten + Sprouted)",
        "total_bulbs": "Total Evaluated Bulbs",
        "mandi_benchmark": "GOVERNMENT MANDI BENCHMARK (data.gov.in)",
        "price_payout": "QUALITY-ADJUSTED PRICE & PAYOUT",
        "ref_mandi": "Reference Mandi",
        "modal_price": "Modal Price",
        "price_source": "Price Date & Source",
        "quality_score": "Batch Quality Score",
        "est_price": "Estimated Price",
        "proc_qty": "Procured Batch Quantity",
        "total_payout": "TOTAL ESTIMATED FARMER PAYOUT",
        "formula": "Formula: Modal Price × Quality Score ({score}) × Quantity ({qty})",
        "annotated_title": "AI ANNOTATED ASSESSMENT IMAGE",
        "annotated_title_multi": "AI ANNOTATED ASSESSMENT IMAGES ({count} Sample Perspectives)",
        "primary_perspective": "AI ANNOTATED ASSESSMENT — PRIMARY SAMPLE PERSPECTIVE (Angle 1 of {count})",
        "multi_angle_notice": "<b>MULTI-ANGLE BATCH NOTICE:</b> Consignment evaluated across <b>{count} photographic angles</b> ({total} total bulbs). To preserve optical clarity and avoid visual congestion, all individual angle photographs with bounding boxes and defect breakdowns are cataloged in the <b>Multi-Angle Annexure (Pages 2+)</b>.",
        "quality_summary": "QUALITY SUMMARY",
        "ai_assessment_note": "Generated automatically by OnionGrade AI.",
        "officer_verif_note": "Officially confirmed by",
        "center": "Center",
        "official_verif": "OFFICIAL VERIFICATION",
        "digitally_auth": "Digitally Authenticated",
        "disclaimer": "Disclaimer: AI-assisted evaluation. Final procurement decisions remain subject to applicable procurement procedures and officer verification.",
        "annexure_title": "ONIONGRADE AI — MULTI-ANGLE INSPECTION ANNEXURE",
        "annexure_sub": "OFFICIAL PHOTOGRAPHIC QUALITY AUDIT & PER-ANGLE BULB DETECTION LOG",
        "annexure_farmer": "FARMER",
        "annexure_angles": "TOTAL ANGLES",
        "annexure_bulbs": "TOTAL BULBS",
        "consolidated_audit": "CONSOLIDATED BATCH AUDIT",
        "perspectives_eval": "Sample Perspectives: {count} Angles Evaluated",
        "overall_class": "Overall Classification",
        "ai_cert_badge": "OFFICIAL AI QUALITY CERTIFICATION",
        "annexure_note": "Annexure Note: This multi-angle photo audit log provides official visual documentation for APMC procurement records. Each onion bulb is sequentially indexed and validated across batch sample perspectives by OnionGrade AI.",
        "status_grade_a": "STATUS: 100% Grade A (Healthy)",
        "status_urs": "STATUS: Standard Grade ({damaged} URS)",
        "status_rejected": "DEFECT DETECTED: {defect} Rejected Bulb(s)",
        "angle_sample": "Angle Sample #{order}",
        "bulbs_detected": "{count} Bulbs Detected",
        "healthy_stat": "Healthy",
        "damaged_stat": "Damaged",
        "rotten_stat": "Rotten",
        "sprouted_stat": "Sprouted",
        "pending_rate": "Pending Reference Rate",
        "pending_qty": "Pending Quantity",
        "qty_pending_entry": "Quantity Entry Pending",
        "quintal_unit": "Quintal",
        "quintals_unit": "Quintals"
    },
    "hi": {
        "title": "ऑनियनग्रेड एआई (ONIONGRADE AI)",
        "subtitle": "एआई-संचालित प्याज गुणवत्ता मूल्यांकन एवं डिजिटल खरीद प्रमाण-पत्र",
        "report_id": "रिपोर्ट संख्या (ID)",
        "eval_date": "मूल्यांकन दिनांक",
        "status_label": "स्थिति",
        "status_val": "आधिकारिक रूप से सत्यापित",
        "farmer_details": "किसान विवरण",
        "eval_details": "मूल्यांकन विवरण",
        "name": "नाम",
        "officer": "अधिकारी",
        "farmer_id": "किसान आईडी",
        "proc_center": "खरीद केंद्र",
        "mobile": "मोबाइल",
        "center_loc": "केंद्र स्थान",
        "location": "स्थान / पता",
        "batch_angles": "मूल्यांकित नमूना कोण",
        "image_samples": "कोण नमूने",
        "ai_classification": "एआई गुणवत्ता वर्गीकरण",
        "final_grading": "अंतिम खरीद ग्रेडिंग",
        "count": "संख्या",
        "percentage": "प्रतिशत (%)",
        "healthy": "स्वस्थ (Healthy)",
        "damaged": "क्षतिग्रस्त (Damaged)",
        "rotten": "सड़ा हुआ (Rotten)",
        "sprouted": "अंकुरित (Sprouted)",
        "grade_a": "ग्रेड ए (उत्कृष्ट / स्वस्थ)",
        "urs": "यूआरएस (URS - मध्यम स्तर)",
        "rejected": "अस्वीकृत (सड़ा + अंकुरित)",
        "total_bulbs": "कुल मूल्यांकित प्याज",
        "mandi_benchmark": "सरकारी मंडी दर बेंचमार्क (data.gov.in)",
        "price_payout": "गुणवत्ता-समायोजित भाव एवं भुगतान",
        "ref_mandi": "संदर्भ मंडी",
        "modal_price": "मॉडल भाव",
        "price_source": "दर दिनांक व स्रोत",
        "quality_score": "बैच गुणवत्ता स्कोर",
        "est_price": "अनुमानित भाव",
        "proc_qty": "खरीदी गई कुल मात्रा",
        "total_payout": "कुल अनुमानित किसान भुगतान",
        "formula": "सूत्र: मंडी भाव × गुणवत्ता स्कोर ({score}) × मात्रा ({qty})",
        "annotated_title": "एआई एनोटेटेड गुणवत्ता मूल्यांकन छायाचित्र",
        "annotated_title_multi": "एआई एनोटेटेड गुणवत्ता छायाचित्र ({count} कोण नमूने)",
        "primary_perspective": "एआई मूल्यांकन — प्राथमिक कोण परिप्रेक्ष्य ({count} में से कोण 1)",
        "multi_angle_notice": "<b>बहु-कोणीय बैच सूचना:</b> लॉट का मूल्यांकन <b>{count} फोटोग्राफिक कोणों</b> (कुल {total} प्याज) में किया गया है। स्पष्टता बनाए रखने हेतु सभी अलग-अलग कोणों के छायाचित्र बाउंडिंग बॉक्स एवं दोष विवरण के साथ <b>बहु-कोणीय परिशिष्ट (पृष्ठ 2+)</b> में दर्ज हैं।",
        "quality_summary": "गुणवत्ता सारांश",
        "ai_assessment_note": "ऑनियनग्रेड एआई द्वारा स्वचालित रूप से विश्लेषित किया गया।",
        "officer_verif_note": "सत्यापनकर्ता अधिकारी:",
        "center": "केंद्र",
        "official_verif": "आधिकारिक सत्यापन",
        "digitally_auth": "डिजिटल रूप से प्रमाणित",
        "disclaimer": "अस्वीकरण: यह एआई-सहायता प्राप्त मूल्यांकन है। अंतिम खरीद निर्णय संबंधित खरीद नियमों एवं अधिकारी सत्यापन के अधीन हैं।",
        "annexure_title": "ऑनियनग्रेड एआई — बहु-कोणीय निरीक्षण परिशिष्ट (ANNEXURE)",
        "annexure_sub": "आधिकारिक फोटोग्राफिक गुणवत्ता ऑडिट एवं प्रति-कोण बल्ब डिटेक्शन लॉग",
        "annexure_farmer": "किसान",
        "annexure_angles": "कुल कोण",
        "annexure_bulbs": "कुल प्याज",
        "consolidated_audit": "संयुक्त बैच ऑडिट",
        "perspectives_eval": "नमूना परिप्रेक्ष्य: {count} कोण मूल्यांकित",
        "overall_class": "समग्र वर्गीकरण",
        "ai_cert_badge": "आधिकारिक एआई गुणवत्ता प्रमाणन",
        "annexure_note": "परिशिष्ट नोट: यह बहु-कोणीय फोटो ऑडिट लॉग कृषि उपज मंडी समिति (APMC) खरीद रिकॉर्ड के लिए आधिकारिक साक्ष्य प्रदान करता है।",
        "status_grade_a": "स्थिति: 100% ग्रेड ए (स्वस्थ)",
        "status_urs": "स्थिति: मानक स्तर ({damaged} यूआरएस)",
        "status_rejected": "दोष पाया गया: {defect} अस्वीकृत प्याज",
        "angle_sample": "कोण नमूना #{order}",
        "bulbs_detected": "{count} प्याज पहचाने गए",
        "healthy_stat": "स्वस्थ",
        "damaged_stat": "क्षतिग्रस्त",
        "rotten_stat": "सड़ा",
        "sprouted_stat": "अंकुरित",
        "pending_rate": "संदर्भ दर प्रतीक्षित",
        "pending_qty": "मात्रा प्रतीक्षित",
        "qty_pending_entry": "मात्रा प्रविष्टि प्रतीक्षित",
        "quintal_unit": "क्विंटल",
        "quintals_unit": "क्विंटल"
    },
    "mr": {
        "title": "ऑनियनग्रेड एआय (ONIONGRADE AI)",
        "subtitle": "एआय-आधारित कांदा गुणवत्ता मूल्यांकन आणि डिजिटल खरेदी प्रमाणपत्र",
        "report_id": "अहवाल क्र. (ID)",
        "eval_date": "मूल्यांकन तारीख",
        "status_label": "स्थिती",
        "status_val": "अधिकृतपणे प्रमाणित",
        "farmer_details": "शेतकरी तपशील",
        "eval_details": "मूल्यांकन तपशील",
        "name": "नाव",
        "officer": "अधिकारी",
        "farmer_id": "शेतकरी आयडी",
        "proc_center": "खरेदी केंद्र",
        "mobile": "मोबाईल",
        "center_loc": "केंद्र ठिकाण",
        "location": "पत्ता / ठिकाण",
        "batch_angles": "मूल्यांकित नमुना कोपरे",
        "image_samples": "नमुना कोपरे",
        "ai_classification": "एआय गुणवत्ता वर्गीकरण",
        "final_grading": "अंतिम खरेदी प्रतवारी (Grading)",
        "count": "संख्या",
        "percentage": "टक्केवारी (%)",
        "healthy": "निरोगी (Healthy)",
        "damaged": "खराब / डागी (Damaged)",
        "rotten": "सडलेला (Rotten)",
        "sprouted": "कोंब आलेला (Sprouted)",
        "grade_a": "दर्जा 'अ' (Grade A - निरोगी)",
        "urs": "यूआरएस (URS - मध्यम प्रत)",
        "rejected": "नाकारलेले (सडलेला + कोंब)",
        "total_bulbs": "एकूण मूल्यांकित कांदे",
        "mandi_benchmark": "शासकीय कृषी बाजार भाव (data.gov.in)",
        "price_payout": "गुणवत्ता-आधारित दर आणि शेतकरी देयक",
        "ref_mandi": "संदर्भ बाजारपेठ (मंडी)",
        "modal_price": "सरासरी (Modal) भाव",
        "price_source": "भाव दिनांक व स्रोत",
        "quality_score": "गुणवत्ता गुण (Score)",
        "est_price": "अपेक्षित खरेदी दर",
        "proc_qty": "खरेदी केलेले एकूण वजन",
        "total_payout": "शेतकऱ्याला मिळणारी एकूण रक्कम",
        "formula": "सूत्र: बाजार भाव × गुणवत्ता गुण ({score}) × वजन ({qty})",
        "annotated_title": "एआय प्रमाणित प्रतवारी छायाचित्र",
        "annotated_title_multi": "एआय प्रमाणित प्रतवारी छायाचित्रे ({count} नमुने)",
        "primary_perspective": "एआय प्रतवारी — प्राथमिक नमुना छायाचित्र ({count} पैकी १)",
        "multi_angle_notice": "<b>बहु-कोणीय लॉट सूचना:</b> या मालाचे मूल्यांकन <b>{count} वेगवेगळ्या छायाचित्र कोनांतून</b> (एकूण {total} कांदे) केले आहे. स्पष्टतेसाठी सर्व कोनांचे स्वतंत्र विश्लेषण व दोष विवरण <b>परिशिष्टामध्ये (पान २+)</b> जोडले आहे.",
        "quality_summary": "गुणवत्ता सारांश",
        "ai_assessment_note": "ऑनियनग्रेड एआय प्रणालीद्वारे स्वयंचलित मूल्यमापन.",
        "officer_verif_note": "प्रमाणित करणारे अधिकारी:",
        "center": "केंद्र",
        "official_verif": "अधिकृत प्रमाणीकरण",
        "digitally_auth": "डिजिटली प्रमाणित",
        "disclaimer": "सूचना: हे एआय-आधारित मूल्यांकन आहे. अंतिम खरेदी निर्णय विहित खरेदी नियमावली आणि अधिकाऱ्यांच्या अंतिम पडताळणीनुसार मान्य राहतील.",
        "annexure_title": "ऑनियनग्रेड एआय — बहु-कोणीय तपासणी परिशिष्ट (ANNEXURE)",
        "annexure_sub": "अधिकृत छायाचित्र गुणवत्ता लेखापरीक्षण आणि कोनानुसार कांदा नोंदवही",
        "annexure_farmer": "शेतकरी",
        "annexure_angles": "एकूण कोपरे",
        "annexure_bulbs": "एकूण कांदे",
        "consolidated_audit": "एकत्रित कांदा लॉट ऑडिट",
        "perspectives_eval": "नमुना कोपरे: {count} कोपरे मूल्यांकित",
        "overall_class": "एकूण प्रतवारी",
        "ai_cert_badge": "अधिकृत एआय गुणवत्ता प्रमाणपत्र",
        "annexure_note": "परिशिष्ट नोंद: ही बहु-कोणीय छायाचित्र नोंद कृषी उत्पन्न बाजार समितीच्या (APMC) खरेदी अभिलेखासाठी अधिकृत पुरावा म्हणून जोडली आहे.",
        "status_grade_a": "स्थिती: १००% दर्जा 'अ' (निरोगी)",
        "status_urs": "स्थिती: मध्यम प्रत ({damaged} URS)",
        "status_rejected": "दोष आढळले: {defect} नाकारलेले कांदे",
        "angle_sample": "नमुना कोन #{order}",
        "bulbs_detected": "{count} कांदे नोंदवले",
        "healthy_stat": "निरोगी",
        "damaged_stat": "खराब",
        "rotten_stat": "सडलेला",
        "sprouted_stat": "कोंब",
        "pending_rate": "संदर्भ दर प्रतीक्षेत",
        "pending_qty": "वजन प्रविष्टी प्रतीक्षेत",
        "qty_pending_entry": "वजन नोंद प्रतीक्षेत",
        "quintal_unit": "क्विंटल",
        "quintals_unit": "क्विंटल"
    }
}


def resolve_image_path(image_path, fallback_path=None):
    """
    Robustly resolves an image path to an existing file on disk.
    Handles:
    - Existing direct path (absolute or relative)
    - Path relative to Config.BASE_DIR
    - Filename extracted from path and searched in Config.OUTPUT_FOLDER, Config.UPLOAD_FOLDER, Config.STATIC_SAMPLES_FOLDER
    - Fallback path (e.g. original image if annotated image is missing)
    """
    candidates = []
    if image_path:
        candidates.append(image_path)
    if fallback_path:
        candidates.append(fallback_path)

    base_dir = getattr(Config, "BASE_DIR", None)

    for cand in candidates:
        if not cand:
            continue
        cand_str = str(cand).strip()
        if not cand_str:
            continue

        # 1. Exact path as provided
        if os.path.isfile(cand_str):
            return cand_str

        # 2. Relative to BASE_DIR
        if base_dir:
            rel_cand = os.path.join(base_dir, cand_str)
            if os.path.isfile(rel_cand):
                return rel_cand

        # 3. Clean up slashes to extract basename
        clean_cand = cand_str.replace("\\", "/").rstrip("/")
        fname = os.path.basename(clean_cand)

        # Also strip leading url prefixes if path was like "/outputs/abc.jpg" or "/uploads/abc.jpg"
        for prefix in ["outputs/", "uploads/", "static/samples/", "static/images/", "static/"]:
            if clean_cand.lower().startswith(prefix):
                fname = clean_cand[len(prefix):]
                break

        if fname:
            # Check in Config.OUTPUT_FOLDER
            if hasattr(Config, "OUTPUT_FOLDER"):
                p = os.path.join(Config.OUTPUT_FOLDER, fname)
                if os.path.isfile(p):
                    return p
            # Check in Config.UPLOAD_FOLDER
            if hasattr(Config, "UPLOAD_FOLDER"):
                p = os.path.join(Config.UPLOAD_FOLDER, fname)
                if os.path.isfile(p):
                    return p
            # Check in Config.STATIC_SAMPLES_FOLDER
            if hasattr(Config, "STATIC_SAMPLES_FOLDER"):
                p = os.path.join(Config.STATIC_SAMPLES_FOLDER, fname)
                if os.path.isfile(p):
                    return p
            # Check other standard subdirectories in base_dir
            if base_dir:
                for sub in ["outputs", "uploads", os.path.join("static", "samples"), os.path.join("static", "images"), "static"]:
                    p = os.path.join(base_dir, sub, fname)
                    if os.path.isfile(p):
                        return p

    return None


def get_proportional_image(image_path, max_w, max_h, fallback_path=None):
    """
    Returns a ReportLab Image flowable scaled to fit within max_w and max_h,
    strictly maintaining the original image's aspect ratio.
    Automatically resolves the image path across project directories and fallbacks.
    """
    actual_path = resolve_image_path(image_path, fallback_path=fallback_path)
    if not actual_path or not os.path.exists(actual_path):
        return None
    try:
        with PILImage.open(actual_path) as pimg:
            orig_w, orig_h = pimg.size
        if orig_w <= 0 or orig_h <= 0:
            return None
        aspect = orig_w / orig_h
        target_w = max_w
        target_h = max_w / aspect
        if target_h > max_h:
            target_h = max_h
            target_w = max_h * aspect
        rl_img = RLImage(actual_path, width=target_w, height=target_h)
        rl_img.hAlign = "CENTER"
        return rl_img
    except Exception as e:
        print(f"[PDFService] Error loading image {actual_path} (from {image_path}): {e}")
        return None


def generate_evaluation_pdf(evaluation, language=None):
    """
    Generates an official agricultural quality assessment PDF for an evaluation.
    Supports English ('en'), Hindi ('hi'), and Marathi ('mr').
    Conforms to government/APMC procurement documentation standards:
    - Page 1: Official 1-page executive procurement certificate with primary sample angle.
    - Page 2+: High-resolution Multi-Angle Visual Assessment Log (Annexure) when multiple angles exist.
    """
    os.makedirs(Config.PDF_REPORT_FOLDER, exist_ok=True)
    report_id = evaluation.report_id or f"ONR-{evaluation.id}"
    pdf_filename = f"Onion_Report_{report_id}.pdf"
    pdf_path = os.path.join(Config.PDF_REPORT_FOLDER, pdf_filename)

    # Determine language
    if not language:
        language = getattr(evaluation, "report_language", None)
        if not language and getattr(evaluation, "report", None):
            language = getattr(evaluation.report, "language", None)
    
    lang = str(language or "en").lower().strip()
    if lang not in ("en", "hi", "mr"):
        lang = "en"

    # Font selection & registration
    is_devanagari = lang in ("hi", "mr")
    if is_devanagari:
        has_font = register_devanagari_fonts()
        font_regular = "Devanagari" if has_font else "Helvetica"
        font_bold = "Devanagari-Bold" if has_font else "Helvetica-Bold"
        font_oblique = font_regular
    else:
        font_regular = "Helvetica"
        font_bold = "Helvetica-Bold"
        font_oblique = "Helvetica-Oblique"

    t = TRANSLATIONS.get(lang, TRANSLATIONS["en"])

    # Document setup: A4
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=28,
        rightMargin=28,
        topMargin=24,
        bottomMargin=24
    )

    styles = getSampleStyleSheet()

    # Dynamic typography sizing for Devanagari vs Latin
    title_size = 16 if is_devanagari else 18
    title_lead = 20 if is_devanagari else 22
    cell_size = 8.0 if is_devanagari else 8.5
    cell_lead = 11.0 if is_devanagari else 10.5

    title_style = ParagraphStyle(
        f"DocTitle_{lang}",
        parent=styles["Normal"],
        fontName=font_bold,
        fontSize=title_size,
        leading=title_lead,
        textColor=colors.HexColor("#0f5132"),
        alignment=1
    )

    subtitle_style = ParagraphStyle(
        f"DocSubtitle_{lang}",
        parent=styles["Normal"],
        fontName=font_bold,
        fontSize=8.5 if is_devanagari else 9,
        leading=11.5 if is_devanagari else 12,
        textColor=colors.HexColor("#4b5563"),
        alignment=1
    )

    section_header_style = ParagraphStyle(
        f"SectionHeader_{lang}",
        parent=styles["Normal"],
        fontName=font_bold,
        fontSize=9.5 if is_devanagari else 10,
        leading=12.5 if is_devanagari else 13,
        textColor=colors.HexColor("#0f5132"),
        spaceBefore=4,
        spaceAfter=2
    )

    cell_bold_style = ParagraphStyle(
        f"CellBold_{lang}",
        parent=styles["Normal"],
        fontName=font_bold,
        fontSize=cell_size,
        leading=cell_lead,
        textColor=colors.HexColor("#1f2937")
    )

    cell_value_style = ParagraphStyle(
        f"CellValue_{lang}",
        parent=styles["Normal"],
        fontName=font_regular,
        fontSize=cell_size,
        leading=cell_lead,
        textColor=colors.HexColor("#374151")
    )

    summary_text_style = ParagraphStyle(
        f"SummaryText_{lang}",
        parent=styles["Normal"],
        fontName=font_regular,
        fontSize=cell_size,
        leading=cell_lead + 1.0,
        textColor=colors.HexColor("#1f2937")
    )

    disclaimer_style = ParagraphStyle(
        f"Disclaimer_{lang}",
        parent=styles["Normal"],
        fontName=font_oblique,
        fontSize=7,
        leading=9.5,
        textColor=colors.HexColor("#6b7280"),
        alignment=1
    )

    notice_box_style = ParagraphStyle(
        f"NoticeBox_{lang}",
        parent=styles["Normal"],
        fontName=font_regular,
        fontSize=7.5,
        leading=10.5,
        textColor=colors.HexColor("#166534")
    )

    annexure_title_style = ParagraphStyle(
        f"AnnexureTitle_{lang}",
        parent=styles["Normal"],
        fontName=font_bold,
        fontSize=13 if is_devanagari else 14,
        leading=17 if is_devanagari else 18,
        textColor=colors.HexColor("#0f5132"),
        alignment=1
    )

    annexure_sub_style = ParagraphStyle(
        f"AnnexureSub_{lang}",
        parent=styles["Normal"],
        fontName=font_bold,
        fontSize=8.0 if is_devanagari else 8.5,
        leading=11.0 if is_devanagari else 11.5,
        textColor=colors.HexColor("#4b5563"),
        alignment=1
    )

    card_header_style = ParagraphStyle(
        f"CardHeader_{lang}",
        parent=styles["Normal"],
        fontName=font_bold,
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#0f5132"),
        alignment=1
    )

    card_stats_style = ParagraphStyle(
        f"CardStats_{lang}",
        parent=styles["Normal"],
        fontName=font_regular,
        fontSize=7,
        leading=9.5,
        textColor=colors.HexColor("#374151"),
        alignment=1
    )

    card_badge_style = ParagraphStyle(
        f"CardBadge_{lang}",
        parent=styles["Normal"],
        fontName=font_bold,
        fontSize=7.5,
        leading=9.5,
        alignment=1
    )

    elements = []

    # =========================================================================
    # PAGE 1: OFFICIAL PROCUREMENT ASSESSMENT CERTIFICATE
    # =========================================================================

    # 1. Header Banner
    elements.append(Paragraph(t["title"], title_style))
    elements.append(Paragraph(t["subtitle"], subtitle_style))
    elements.append(Spacer(1, 4))

    # Meta banner (Report ID & Date)
    eval_date_str = evaluation.evaluation_date.strftime("%d/%m/%Y %I:%M %p") if evaluation.evaluation_date else ""
    meta_table_data = [
        [
            Paragraph(f"<b>{t['report_id']}:</b> {report_id}", cell_bold_style),
            Paragraph(f"<b>{t['eval_date']}:</b> {eval_date_str}", cell_bold_style),
            Paragraph(f"<b>{t['status_label']}:</b> <font color='#0f5132'><b>{t['status_val']}</b></font>", cell_bold_style)
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

    # 2. Farmer & Evaluation Details
    farmer = evaluation.farmer
    farmer_user = farmer.user if farmer else None
    officer = evaluation.officer
    officer_user = officer.user if officer else None

    farmer_data = [
        [Paragraph(f"<b>{t['farmer_details']}</b>", section_header_style), Paragraph(f"<b>{t['eval_details']}</b>", section_header_style)],
        [
            Paragraph(f"<b>{t['name']}:</b> {farmer_user.name if farmer_user else 'N/A'}", cell_value_style),
            Paragraph(f"<b>{t['officer']}:</b> {officer_user.name if officer_user else 'Officer'} ({officer.officer_id if officer else 'N/A'})", cell_value_style)
        ],
        [
            Paragraph(f"<b>{t['farmer_id']}:</b> {farmer.farmer_id if farmer else 'N/A'}", cell_value_style),
            Paragraph(f"<b>{t['proc_center']}:</b> {officer.procurement_center if officer else 'N/A'}", cell_value_style)
        ],
        [
            Paragraph(f"<b>{t['mobile']}:</b> {farmer_user.phone if farmer_user else 'N/A'}", cell_value_style),
            Paragraph(f"<b>{t['center_loc']}:</b> {officer.location if officer else 'N/A'}", cell_value_style)
        ],
        [
            Paragraph(f"<b>{t['location']}:</b> {farmer.village}, {farmer.taluka}, {farmer.district}, {farmer.state}" if farmer else "N/A", cell_value_style),
            Paragraph(f"<b>{t['batch_angles']}:</b> {evaluation.total_images or 1} {t['image_samples']}", cell_value_style)
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
            Paragraph(f"<b>{t['ai_classification']}</b>", cell_bold_style),
            Paragraph(f"<b>{t['count']}</b>", cell_bold_style),
            Paragraph(f"<b>{t['percentage']}</b>", cell_bold_style),
            Paragraph(f"<b>{t['final_grading']}</b>", cell_bold_style),
            Paragraph(f"<b>{t['count']}</b>", cell_bold_style),
            Paragraph(f"<b>{t['percentage']}</b>", cell_bold_style)
        ],
        [
            Paragraph(t["healthy"], cell_value_style),
            str(evaluation.healthy_count),
            f"{h_pct}%",
            Paragraph(f"<b>{t['grade_a']}</b>", cell_value_style),
            str(evaluation.grade_a_count),
            f"{ga_pct}%"
        ],
        [
            Paragraph(t["damaged"], cell_value_style),
            str(evaluation.damaged_count),
            f"{d_pct}%",
            Paragraph(f"<b>{t['urs']}</b>", cell_value_style),
            str(evaluation.urs_count),
            f"{urs_pct}%"
        ],
        [
            Paragraph(t["rotten"], cell_value_style),
            str(evaluation.rotten_count),
            f"{r_pct}%",
            Paragraph(f"<b>{t['rejected']}</b>", cell_value_style),
            str(evaluation.rejected_count),
            f"{rej_pct}%"
        ],
        [
            Paragraph(t["sprouted"], cell_value_style),
            str(evaluation.sprouted_count),
            f"{s_pct}%",
            Paragraph(f"<b>{t['total_bulbs']}</b>", cell_bold_style),
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
    m_modal = f"Rs. {evaluation.mandi_modal_price:,.2f} / {t['quintal_unit']}" if evaluation.mandi_modal_price else "Rate Unavailable"
    m_source = evaluation.mandi_api_source or "data.gov.in"
    m_date = evaluation.mandi_price_date or (evaluation.evaluation_date.strftime("%d/%m/%Y") if evaluation.evaluation_date else "N/A")

    q_score_val = evaluation.quality_score if evaluation.quality_score is not None else round((ga_pct * 1.0 + urs_pct * 0.8), 1)
    q_score_str = f"{q_score_val:.1f}%"
    est_price_str = f"Rs. {evaluation.estimated_price_per_quintal:,.2f} / {t['quintal_unit']}" if evaluation.estimated_price_per_quintal else t["pending_rate"]

    has_qty = evaluation.quantity_quintals and evaluation.quantity_quintals > 0
    qty_str = f"{evaluation.quantity_quintals:.2f} {t['quintals_unit']}" if has_qty else t["qty_pending_entry"]

    has_payout = evaluation.total_payout and evaluation.total_payout > 0
    payout_str = f"Rs. {evaluation.total_payout:,.2f}" if has_payout else (t["pending_qty"] if evaluation.estimated_price_per_quintal else "N/A")

    formula_text = t["formula"].format(score=q_score_str, qty=qty_str)

    price_table_data = [
        [
            Paragraph(f"<b>{t['mandi_benchmark']}</b>", section_header_style),
            Paragraph(f"<b>{t['price_payout']}</b>", section_header_style)
        ],
        [
            Paragraph(f"<b>{t['ref_mandi']}:</b> {m_name}<br/>"
                      f"<b>{t['modal_price']}:</b> <font color='#0f5132'><b>{m_modal}</b></font><br/>"
                      f"<b>{t['price_source']}:</b> {m_date} ({m_source})", cell_value_style),
            Paragraph(f"<b>{t['quality_score']}:</b> <b>{q_score_str}</b> [A: 100%, URS: 80%, Rej: 0%]<br/>"
                      f"<b>{t['est_price']}:</b> <font color='#0f5132'><b>{est_price_str}</b></font><br/>"
                      f"<b>{t['proc_qty']}:</b> <b>{qty_str}</b>", cell_value_style)
        ],
        [
            Paragraph(f"<b>{t['total_payout']}:</b> <font size='9.5' color='#0f5132'><b>{payout_str}</b></font>", cell_bold_style),
            Paragraph(formula_text, disclaimer_style)
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
        single_path = eval_images[0].annotated_image_path if eval_images else evaluation.annotated_image_path
        single_fallback = eval_images[0].original_image_path if eval_images else getattr(evaluation, "original_image_path", None)
        elements.append(Paragraph(f"<b>{t['annotated_title']}</b>", section_header_style))
        img_flow = get_proportional_image(single_path, max_w=460, max_h=130, fallback_path=single_fallback)
        if img_flow:
            elements.append(img_flow)
            elements.append(Spacer(1, 4))
    elif total_imgs in (2, 3) and len(eval_images) == total_imgs:
        elements.append(Paragraph(f"<b>{t['annotated_title_multi'].format(count=total_imgs)}</b>", section_header_style))
        col_w = 539.0 / total_imgs
        img_cells = []
        for img_rec in sorted(eval_images, key=lambda x: x.image_order):
            img_flow = get_proportional_image(
                img_rec.annotated_image_path,
                max_w=col_w - 14,
                max_h=110,
                fallback_path=getattr(img_rec, "original_image_path", None)
            )
            cell_content = [
                Paragraph(f"<b>{t['angle_sample'].format(order=img_rec.image_order)}</b> ({img_rec.total_onions} bulbs)", cell_bold_style),
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
        primary_path = eval_images[0].annotated_image_path if eval_images else evaluation.annotated_image_path
        primary_fallback = eval_images[0].original_image_path if eval_images else getattr(evaluation, "original_image_path", None)
        elements.append(Paragraph(f"<b>{t['primary_perspective'].format(count=total_imgs)}</b>", section_header_style))
        img_flow = get_proportional_image(primary_path, max_w=440, max_h=115, fallback_path=primary_fallback)
        if img_flow:
            elements.append(img_flow)
            elements.append(Spacer(1, 3))

        notice_data = [
            [
                Paragraph(
                    t["multi_angle_notice"].format(count=total_imgs, total=evaluation.total_onions),
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
    summary_text = evaluation.quality_summary or "Quality assessment successfully completed."
    if lang == "mr":
        summary_text = f"कांदा लॉट गुणवत्ता मूल्यमापन पूर्ण झाले. एकूण कांदे: {evaluation.total_onions}, दर्जा 'अ': {evaluation.grade_a_count}, मध्यम (URS): {evaluation.urs_count}, नाकारलेले: {evaluation.rejected_count}."
    elif lang == "hi":
        summary_text = f"प्याज लॉट गुणवत्ता मूल्यांकन पूर्ण हुआ। कुल प्याज: {evaluation.total_onions}, ग्रेड 'ए': {evaluation.grade_a_count}, मध्यम (URS): {evaluation.urs_count}, अस्वीकृत: {evaluation.rejected_count}."

    summary_box_data = [
        [Paragraph(f"<b>{t['quality_summary']}</b>", section_header_style)],
        [Paragraph(summary_text, summary_text_style)]
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
                f"<b>AI:</b> {t['ai_assessment_note']}<br/>"
                f"<b>{t['officer_verif_note']}</b> {officer_user.name if officer_user else 'Officer'} ({officer.officer_id if officer else ''})<br/>"
                f"<b>{t['center']}:</b> {officer.procurement_center if officer else ''}",
                cell_value_style
            ),
            Paragraph(
                f"<b>{t['official_verif']}</b><br/>"
                f"{t['digitally_auth']}<br/>"
                f"Ref: {report_id}",
                ParagraphStyle(f"Stamp_{lang}", parent=cell_bold_style, alignment=2, textColor=colors.HexColor("#0f5132"))
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
    elements.append(Paragraph(t["disclaimer"], disclaimer_style))

    # =========================================================================
    # MULTI-ANGLE VISUAL ASSESSMENT LOG (ANNEXURE) - PAGES 2+
    # =========================================================================
    if total_imgs > 1 and len(eval_images) > 0:
        elements.append(PageBreak())

        elements.append(Paragraph(t["annexure_title"], annexure_title_style))
        elements.append(Paragraph(t["annexure_sub"], annexure_sub_style))
        elements.append(Spacer(1, 5))

        annex_meta_data = [
            [
                Paragraph(f"<b>{t['report_id']}:</b> {report_id}", cell_bold_style),
                Paragraph(f"<b>{t['annexure_farmer']}:</b> {farmer_user.name if farmer_user else 'N/A'}", cell_bold_style),
                Paragraph(f"<b>{t['annexure_angles']}:</b> {total_imgs} {t['image_samples']}", cell_bold_style),
                Paragraph(f"<b>{t['annexure_bulbs']}:</b> {evaluation.total_onions}", cell_bold_style)
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
                verdict_html = f"<font color='#0f5132'><b>{t['status_grade_a']}</b></font>"
                badge_bg = colors.HexColor("#f0fdf4")
            elif defect_cnt == 0:
                verdict_html = f"<font color='#0284c7'><b>{t['status_urs'].format(damaged=damaged_cnt)}</b></font>"
                badge_bg = colors.HexColor("#f0f9ff")
            else:
                verdict_html = f"<font color='#b91c1c'><b>{t['status_rejected'].format(defect=defect_cnt)}</b></font>"
                badge_bg = colors.HexColor("#fef2f2")

            img_flow = get_proportional_image(
                img_rec.annotated_image_path,
                max_w=248,
                max_h=126,
                fallback_path=getattr(img_rec, "original_image_path", None)
            )
            if not img_flow:
                img_flow = Paragraph("<i>Image preview unavailable</i>", cell_value_style)

            card_data = [
                [Paragraph(f"<b>{t['angle_sample'].format(order=img_rec.image_order)}</b> &nbsp;|&nbsp; <b>{t['bulbs_detected'].format(count=img_rec.total_onions)}</b>", card_header_style)],
                [Paragraph(f"{t['healthy_stat']}: <b>{img_rec.healthy_count}</b> &bull; {t['damaged_stat']}: <b>{img_rec.damaged_count}</b> &bull; {t['rotten_stat']}: <b>{img_rec.rotten_count}</b> &bull; {t['sprouted_stat']}: <b>{img_rec.sprouted_count}</b>", card_stats_style)],
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
                [Paragraph(f"<b>{t['consolidated_audit']}</b>", card_header_style)],
                [Paragraph(t["perspectives_eval"].format(count=total_imgs), card_stats_style)],
                [
                    Paragraph(
                        f"<b>{t['total_bulbs']}:</b> {evaluation.total_onions}<br/>"
                        f"<b>{t['grade_a']}:</b> {evaluation.grade_a_count} ({g_pct}%)<br/>"
                        f"<b>{t['urs']}:</b> {evaluation.urs_count} ({u_pct}%)<br/>"
                        f"<b>{t['rejected']}:</b> {evaluation.rejected_count} ({r_pct}%)<br/>"
                        f"<b>{t['quality_score']}:</b> <b>{q_score_str}</b><br/>"
                        f"<b>{t['overall_class']}:</b> <font color='#0f5132'><b>{evaluation.overall_result}</b></font>",
                        cell_value_style
                    )
                ],
                [Paragraph(f"<font color='#0f5132'><b>{t['ai_cert_badge']}</b></font>", card_badge_style)]
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
        elements.append(Paragraph(t["annexure_note"], disclaimer_style))

    # Build PDF document
    doc.build(elements)
    file_size = os.path.getsize(pdf_path) if os.path.exists(pdf_path) else 0

    return pdf_filename, pdf_path, file_size
