import os

from flask import Flask, render_template, session

from backend.ai.classifier import OnionClassifier
from backend.ai.detector import OnionDetector
from backend.database.db import init_db
from backend.routes.auth import auth_bp
from backend.routes.farmer import farmer_bp
from backend.routes.government import government_bp
from backend.routes.market import market_bp
from backend.routes.officer import officer_bp
from backend.routes.reports import reports_bp
from backend.routes.views import views_bp
from backend.utils.seed_data import seed_demo_data
from config import Config


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)

    # Ensure vital operational directories exist
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(Config.OUTPUT_FOLDER, exist_ok=True)
    os.makedirs(Config.PDF_REPORT_FOLDER, exist_ok=True)
    os.makedirs(Config.MODEL_FOLDER, exist_ok=True)

    # Initialize SQLAlchemy database
    init_db(app)

    # Register Blueprints
    app.register_blueprint(views_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(farmer_bp)
    app.register_blueprint(officer_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(market_bp)
    app.register_blueprint(government_bp)

    # Register Jinja Template Filters
    @app.template_filter("basename")
    def basename_filter(path):
        if not path:
            return ""
        return os.path.basename(path)

    # Template Context Processor
    @app.context_processor
    def inject_auth_context():
        return {
            "is_authenticated": "user_id" in session,
            "current_user_name": session.get("user_name", ""),
            "current_user_role": session.get("user_role", ""),
            "current_farmer_id": session.get("farmer_id", ""),
            "current_officer_id": session.get("officer_id", "")
        }

    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("base.html", error_title="404 - Page Not Found", error_message="The requested resource could not be found."), 404

    @app.errorhandler(403)
    def access_forbidden(e):
        return render_template("base.html", error_title="403 - Access Forbidden", error_message="You do not have permission to access this resource."), 403

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template("base.html", error_title="500 - Server Error", error_message="An unexpected error occurred. Please try again."), 500

    # Warm up models and seed data in application context
    with app.app_context():
        print("[OnionGrade AI] Initializing platform...")
        # Preload AI models ONCE at startup per specification
        try:
            OnionDetector()
            OnionClassifier()
        except Exception as e:
            print(f"[OnionGrade AI] Note on AI pre-load: {e}")

        # Seed initial demo data
        try:
            seed_demo_data()
        except Exception as e:
            print(f"[OnionGrade AI] Seed note: {e}")

    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)
