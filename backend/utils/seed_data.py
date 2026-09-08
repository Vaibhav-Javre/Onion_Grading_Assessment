import os
import shutil
from datetime import datetime, timezone, timedelta
from backend.database.db import db
from backend.models.user import User
from backend.models.farmer import FarmerProfile
from backend.models.officer import OfficerProfile
from backend.models.evaluation import Evaluation, EvaluationItem
from backend.models.report import Report
from backend.services.pdf_service import generate_evaluation_pdf
from backend.services.market_price_service import MarketPriceService
from config import Config

def seed_demo_data():
    """
    Seeds initial demonstration accounts and historical reports if empty.
    Clearly marks demo data.
    """
    # Seed Mandi market prices
    MarketPriceService.seed_or_update_benchmark_prices()

    # Check if officer already exists
    existing_officer_user = User.query.filter_by(role="officer").first()
    if existing_officer_user:
        return

    print("[SeedData] Seeding demo accounts and historical evaluations...")

    # 1. Create Officer
    officer_user = User(
        name="Vikram Shinde",
        email="vikram.shinde@apmc.gov.in",
        phone="9922001122",
        role="officer"
    )
    officer_user.set_password("officer123")
    db.session.add(officer_user)
    db.session.flush()

    officer_profile = OfficerProfile(
        user_id=officer_user.id,
        officer_id="OFF-2026-001",
        procurement_center="Lasalgaon APMC Main Procurement Yard",
        location="Lasalgaon, Nashik"
    )
    db.session.add(officer_profile)

    # 2. Create Farmer 1 (Ramesh Patil)
    farmer1_user = User(
        name="Ramesh Patil",
        email="ramesh.patil@example.com",
        phone="9876543210",
        role="farmer"
    )
    farmer1_user.set_password("farmer123")
    db.session.add(farmer1_user)
    db.session.flush()

    farmer1_profile = FarmerProfile(
        user_id=farmer1_user.id,
        farmer_id="FMR-2026-0001",
        village="Pimpalgaon Baswant",
        taluka="Niphad",
        district="Nashik",
        state="Maharashtra"
    )
    db.session.add(farmer1_profile)

    # 3. Create Farmer 2 (Suresh Deshmukh)
    farmer2_user = User(
        name="Suresh Deshmukh",
        email="suresh.deshmukh@example.com",
        phone="9823012345",
        role="farmer"
    )
    farmer2_user.set_password("farmer123")
    db.session.add(farmer2_user)
    db.session.flush()

    farmer2_profile = FarmerProfile(
        user_id=farmer2_user.id,
        farmer_id="FMR-2026-0002",
        village="Vinchur",
        taluka="Yeola",
        district="Nashik",
        state="Maharashtra"
    )
    db.session.add(farmer2_profile)
    db.session.flush()

    # 4. Create Historical Evaluations for Farmer 1
    sample_src_1 = os.path.join(Config.STATIC_SAMPLES_FOLDER, "onion1.jpg")
    sample_src_2 = os.path.join(Config.STATIC_SAMPLES_FOLDER, "onion2.jpg")

    eval1_orig = os.path.join(Config.UPLOAD_FOLDER, "demo_onion1_orig.jpg")
    eval1_annot = os.path.join(Config.OUTPUT_FOLDER, "demo_onion1_annot.jpg")
    eval2_orig = os.path.join(Config.UPLOAD_FOLDER, "demo_onion2_orig.jpg")
    eval2_annot = os.path.join(Config.OUTPUT_FOLDER, "demo_onion2_annot.jpg")

    if os.path.exists(sample_src_1):
        shutil.copy(sample_src_1, eval1_orig)
        shutil.copy(sample_src_1, eval1_annot)
    if os.path.exists(sample_src_2):
        shutil.copy(sample_src_2, eval2_orig)
        shutil.copy(sample_src_2, eval2_annot)

    # Report 1
    eval1 = Evaluation(
        report_id="ONR-2026-001089",
        farmer_id=farmer1_profile.id,
        officer_id=officer_profile.id,
        original_image_path=eval1_orig,
        annotated_image_path=eval1_annot,
        total_onions=24,
        healthy_count=18,
        damaged_count=3,
        rotten_count=2,
        sprouted_count=1,
        uncertain_count=0,
        grade_a_count=18,
        urs_count=3,
        rejected_count=3,
        overall_result="Grade A - Premium Quality",
        quality_summary=(
            "The AI system detected 24 onions. 18 onions were classified as Healthy (75.0%), "
            "3 as Damaged (12.5%), 2 as Rotten (8.3%) and 1 as Sprouted (4.2%). "
            "Based on official procurement grading standards, 18 onions were categorized as Grade A, "
            "3 as URS and 3 as Rejected."
        ),
        evaluation_date=datetime.now(timezone.utc) - timedelta(days=2),
        status="confirmed"
    )
    db.session.add(eval1)
    db.session.flush()

    # Add sample item detections
    for i in range(1, 19):
        db.session.add(EvaluationItem(
            evaluation_id=eval1.id,
            onion_number=i,
            class_name="Healthy",
            classification_confidence=0.95,
            detection_confidence=0.92,
            x1=20 + (i % 6) * 60,
            y1=20 + (i // 6) * 60,
            x2=70 + (i % 6) * 60,
            y2=70 + (i // 6) * 60
        ))
    for i in range(19, 22):
        db.session.add(EvaluationItem(
            evaluation_id=eval1.id,
            onion_number=i,
            class_name="Damaged",
            classification_confidence=0.88,
            detection_confidence=0.91,
            x1=30, y1=200, x2=80, y2=250
        ))
    db.session.add(EvaluationItem(
        evaluation_id=eval1.id,
        onion_number=22,
        class_name="Rotten",
        classification_confidence=0.93,
        detection_confidence=0.94,
        x1=90, y1=200, x2=140, y2=250
    ))
    db.session.add(EvaluationItem(
        evaluation_id=eval1.id,
        onion_number=23,
        class_name="Rotten",
        classification_confidence=0.89,
        detection_confidence=0.90,
        x1=150, y1=200, x2=200, y2=250
    ))
    db.session.add(EvaluationItem(
        evaluation_id=eval1.id,
        onion_number=24,
        class_name="Sprouted",
        classification_confidence=0.91,
        detection_confidence=0.93,
        x1=210, y1=200, x2=260, y2=250
    ))

    # Generate PDF for Report 1
    pdf_fn, pdf_fp, pdf_size = generate_evaluation_pdf(eval1)
    rep1 = Report(
        evaluation_id=eval1.id,
        pdf_path=pdf_fp,
        file_size_bytes=pdf_size
    )
    db.session.add(rep1)

    # Report 2 (Farmer 2)
    eval2 = Evaluation(
        report_id="ONR-2026-001090",
        farmer_id=farmer2_profile.id,
        officer_id=officer_profile.id,
        original_image_path=eval2_orig,
        annotated_image_path=eval2_annot,
        total_onions=30,
        healthy_count=20,
        damaged_count=6,
        rotten_count=2,
        sprouted_count=2,
        uncertain_count=0,
        grade_a_count=20,
        urs_count=6,
        rejected_count=4,
        overall_result="URS Standard - Commercial Quality",
        quality_summary=(
            "The AI system detected 30 onions. 20 onions were classified as Healthy (66.7%), "
            "6 as Damaged (20.0%), 2 as Rotten (6.7%) and 2 as Sprouted (6.7%). "
            "Based on official procurement grading standards, 20 onions were categorized as Grade A, "
            "6 as URS and 4 as Rejected."
        ),
        evaluation_date=datetime.now(timezone.utc) - timedelta(days=1),
        status="confirmed"
    )
    db.session.add(eval2)
    db.session.flush()

    pdf_fn2, pdf_fp2, pdf_size2 = generate_evaluation_pdf(eval2)
    rep2 = Report(
        evaluation_id=eval2.id,
        pdf_path=pdf_fp2,
        file_size_bytes=pdf_size2
    )
    db.session.add(rep2)

    db.session.commit()
    print("[SeedData] Demo seed completed successfully.")
