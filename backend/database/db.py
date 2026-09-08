from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

db = SQLAlchemy()

def init_db(app):
    db.init_app(app)
    with app.app_context():
        # Import models so SQLAlchemy metadata registers all tables
        from backend.models import user, farmer, officer, evaluation, report, market
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
                
            res_items = db.session.execute(text("PRAGMA table_info(evaluation_items)")).fetchall()
            item_cols = [r[1] for r in res_items]
            if "image_order" not in item_cols:
                db.session.execute(text("ALTER TABLE evaluation_items ADD COLUMN image_order INTEGER DEFAULT 1"))
            db.session.commit()
        except Exception as e:
            print(f"[DB Init Warning] Schema check note: {e}")
            db.session.rollback()

