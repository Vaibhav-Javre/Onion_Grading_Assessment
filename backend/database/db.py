from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

db = SQLAlchemy()

def init_db(app):
    db.init_app(app)
    with app.app_context():
        # Import models so SQLAlchemy metadata registers all tables
        import backend.models  # noqa: F401
        db.create_all()
        try:
            res_eval = db.session.execute(text("PRAGMA table_info(evaluations)")).fetchall()
            eval_cols = [r[1] for r in res_eval]
            if "total_images" not in eval_cols:
                db.session.execute(text("ALTER TABLE evaluations ADD COLUMN total_images INTEGER DEFAULT 1 NOT NULL"))
            if "mandi_name" not in eval_cols:
                db.session.execute(text("ALTER TABLE evaluations ADD COLUMN mandi_name VARCHAR(120) DEFAULT 'Lasalgaon APMC Mandi'"))
            if "mandi_modal_price" not in eval_cols:
                db.session.execute(text("ALTER TABLE evaluations ADD COLUMN mandi_modal_price FLOAT"))
            if "mandi_price_date" not in eval_cols:
                db.session.execute(text("ALTER TABLE evaluations ADD COLUMN mandi_price_date VARCHAR(60)"))
            if "mandi_api_source" not in eval_cols:
                db.session.execute(text("ALTER TABLE evaluations ADD COLUMN mandi_api_source VARCHAR(255) DEFAULT 'data.gov.in'"))
            if "quality_score" not in eval_cols:
                db.session.execute(text("ALTER TABLE evaluations ADD COLUMN quality_score FLOAT"))
            if "estimated_price_per_quintal" not in eval_cols:
                db.session.execute(text("ALTER TABLE evaluations ADD COLUMN estimated_price_per_quintal FLOAT"))
            if "quantity_quintals" not in eval_cols:
                db.session.execute(text("ALTER TABLE evaluations ADD COLUMN quantity_quintals FLOAT DEFAULT 0.0"))
            if "total_payout" not in eval_cols:
                db.session.execute(text("ALTER TABLE evaluations ADD COLUMN total_payout FLOAT DEFAULT 0.0"))
            if "report_language" not in eval_cols:
                db.session.execute(text("ALTER TABLE evaluations ADD COLUMN report_language VARCHAR(20) DEFAULT 'en'"))

            res_reports = db.session.execute(text("PRAGMA table_info(reports)")).fetchall()
            report_cols = [r[1] for r in res_reports]
            if "language" not in report_cols:
                db.session.execute(text("ALTER TABLE reports ADD COLUMN language VARCHAR(20) DEFAULT 'en'"))
                
            res_items = db.session.execute(text("PRAGMA table_info(evaluation_items)")).fetchall()
            item_cols = [r[1] for r in res_items]
            if "image_order" not in item_cols:
                db.session.execute(text("ALTER TABLE evaluation_items ADD COLUMN image_order INTEGER DEFAULT 1"))

            # Schema migration for officer_profiles verification fields
            res_officer = db.session.execute(text("PRAGMA table_info(officer_profiles)")).fetchall()
            officer_cols = [r[1] for r in res_officer]
            if "status" not in officer_cols:
                db.session.execute(text("ALTER TABLE officer_profiles ADD COLUMN status VARCHAR(30) DEFAULT 'APPROVED'"))
            if "is_active" not in officer_cols:
                db.session.execute(text("ALTER TABLE officer_profiles ADD COLUMN is_active BOOLEAN DEFAULT 1"))
            if "application_id" not in officer_cols:
                db.session.execute(text("ALTER TABLE officer_profiles ADD COLUMN application_id VARCHAR(50)"))
            if "government_id_number" not in officer_cols:
                db.session.execute(text("ALTER TABLE officer_profiles ADD COLUMN government_id_number VARCHAR(100)"))
            if "id_proof_path" not in officer_cols:
                db.session.execute(text("ALTER TABLE officer_profiles ADD COLUMN id_proof_path VARCHAR(255)"))
            if "center_address" not in officer_cols:
                db.session.execute(text("ALTER TABLE officer_profiles ADD COLUMN center_address VARCHAR(255)"))
            if "village" not in officer_cols:
                db.session.execute(text("ALTER TABLE officer_profiles ADD COLUMN village VARCHAR(100)"))
            if "taluka" not in officer_cols:
                db.session.execute(text("ALTER TABLE officer_profiles ADD COLUMN taluka VARCHAR(100)"))
            if "district" not in officer_cols:
                db.session.execute(text("ALTER TABLE officer_profiles ADD COLUMN district VARCHAR(100)"))
            if "state" not in officer_cols:
                db.session.execute(text("ALTER TABLE officer_profiles ADD COLUMN state VARCHAR(100) DEFAULT 'Maharashtra'"))
            if "designation" not in officer_cols:
                db.session.execute(text("ALTER TABLE officer_profiles ADD COLUMN designation VARCHAR(100) DEFAULT 'Procurement Officer'"))
            if "department" not in officer_cols:
                db.session.execute(text("ALTER TABLE officer_profiles ADD COLUMN department VARCHAR(150) DEFAULT 'APMC Mandi Board'"))
            if "experience_years" not in officer_cols:
                db.session.execute(text("ALTER TABLE officer_profiles ADD COLUMN experience_years VARCHAR(50)"))
            if "rejection_reason" not in officer_cols:
                db.session.execute(text("ALTER TABLE officer_profiles ADD COLUMN rejection_reason TEXT"))
            if "verified_by" not in officer_cols:
                db.session.execute(text("ALTER TABLE officer_profiles ADD COLUMN verified_by VARCHAR(120)"))
            if "verified_at" not in officer_cols:
                db.session.execute(text("ALTER TABLE officer_profiles ADD COLUMN verified_at DATETIME"))

            # Ensure any pre-existing officers have status=APPROVED and is_active=1
            db.session.execute(text("UPDATE officer_profiles SET status='APPROVED', is_active=1 WHERE status IS NULL OR status=''"))

            # Ensure officer_farmers table exists
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS officer_farmers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    officer_id INTEGER NOT NULL,
                    farmer_id INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(officer_id) REFERENCES officer_profiles(id) ON DELETE CASCADE,
                    FOREIGN KEY(farmer_id) REFERENCES farmer_profiles(id) ON DELETE CASCADE,
                    UNIQUE(officer_id, farmer_id)
                )
            """))
            db.session.commit()

            # Automatic Sync for Confirmed Evaluations into Inventory
            try:
                from backend.models.evaluation import Evaluation
                from backend.models.inventory import InventoryItem
                from backend.services.predictive_inventory_service import PredictiveInventoryService
                
                confirmed_evals = Evaluation.query.filter_by(status="confirmed").all()
                for ce in confirmed_evals:
                    b_id = ce.report_id or f"ONR-{ce.id}"
                    if not InventoryItem.query.filter_by(batch_id=b_id).first():
                        PredictiveInventoryService.sync_evaluation_to_inventory(ce, commit=False)
                db.session.commit()
            except Exception as sync_err:
                print(f"[DB Init Note] Inventory sync: {sync_err}")
                db.session.rollback()
        except Exception as e:
            print(f"[DB Init Warning] Schema check note: {e}")
            db.session.rollback()

