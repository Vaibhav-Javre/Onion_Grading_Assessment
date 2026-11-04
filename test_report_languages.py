import os
import unittest
from app import create_app
from backend.database.db import db
from backend.models.evaluation import Evaluation
from backend.models.farmer import FarmerProfile
from backend.models.officer import OfficerProfile
from backend.models.report import Report
from backend.models.user import User
from backend.services.pdf_service import generate_evaluation_pdf


class ReportLanguagesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_pdf_generation_all_three_languages(self):
        """Test PDF generation for English, Hindi, and Marathi."""
        with self.app.app_context():
            evaluation = Evaluation.query.filter_by(status="confirmed").first()
            self.assertIsNotNone(evaluation, "Confirmed evaluation should exist from seed data")

            for lang in ["en", "hi", "mr"]:
                filename, path, size = generate_evaluation_pdf(evaluation, language=lang)
                self.assertTrue(os.path.exists(path), f"PDF file for {lang} should exist")
                self.assertGreater(size, 10000, f"PDF file for {lang} should be non-trivial in size")
                print(f"✓ PDF generated for language '{lang}': {filename} ({size} bytes)")

    def test_officer_confirm_with_language_selection(self):
        """Test officer confirming an evaluation with selected language ('mr' / Marathi)."""
        with self.app.app_context():
            # Find an officer and pending evaluation
            officer = OfficerProfile.query.first()
            officer_user = officer.user
            evaluation = Evaluation.query.filter_by(status="pending_confirmation").first()
            
            # If no pending, create a fresh dummy evaluation
            if not evaluation:
                farmer = FarmerProfile.query.first()
                evaluation = Evaluation(
                    farmer_id=farmer.id,
                    officer_id=officer.id,
                    original_image_path="uploads/demo.jpg",
                    annotated_image_path="outputs/demo.jpg",
                    total_onions=10,
                    healthy_count=8,
                    damaged_count=1,
                    rotten_count=1,
                    sprouted_count=0,
                    grade_a_count=8,
                    urs_count=1,
                    rejected_count=1,
                    overall_result="Grade A",
                    status="pending_confirmation"
                )
                db.session.add(evaluation)
                db.session.commit()

            eval_id = evaluation.id

            with self.client.session_transaction() as sess:
                sess["user_id"] = officer_user.id
                sess["user_role"] = "officer"
                sess["officer_id"] = officer.id

            # Confirm with Marathi ('mr')
            payload = {
                "quantity_quintals": 5.0,
                "mandi_modal_price": 2400.0,
                "estimated_price_per_quintal": 2200.0,
                "quality_score": 90.0,
                "total_payout": 11000.0,
                "mandi_name": "Lasalgaon APMC Mandi",
                "language": "mr"
            }

            resp = self.client.post(f"/api/officer/evaluate/{eval_id}/confirm", json=payload)
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertTrue(data["success"])
            self.assertEqual(data["language"], "mr")
            print("✓ Officer confirmed evaluation with Marathi ('mr'):", data["report_id"])

            # Verify saved in database
            updated_eval = db.session.get(Evaluation, eval_id)
            self.assertEqual(updated_eval.report_language, "mr")
            self.assertIsNotNone(updated_eval.report)
            self.assertEqual(updated_eval.report.language, "mr")
            self.assertTrue(os.path.exists(updated_eval.report.pdf_path))
            print("✓ Evaluation and Report record verify report_language = 'mr'")

            # Now test Farmer Login retrieving this report
            farmer_user = updated_eval.farmer.user
            with self.client.session_transaction() as sess:
                sess["user_id"] = farmer_user.id
                sess["user_role"] = "farmer"
                sess["farmer_id"] = updated_eval.farmer.id

            # Check Farmer Dashboard
            dash_resp = self.client.get("/api/farmer/dashboard")
            self.assertEqual(dash_resp.status_code, 200)
            dash_data = dash_resp.get_json()
            self.assertTrue(dash_data["success"])
            recent_ids = [r["id"] for r in dash_data["recent_reports"]]
            self.assertIn(eval_id, recent_ids)
            rep_in_dash = next(r for r in dash_data["recent_reports"] if r["id"] == eval_id)
            self.assertEqual(rep_in_dash["report_language"], "mr")
            print("✓ Farmer dashboard returned report with report_language = 'mr'")

            # Check Farmer Reports list
            reports_resp = self.client.get("/api/farmer/reports")
            self.assertEqual(reports_resp.status_code, 200)
            reports_data = reports_resp.get_json()
            rep_in_list = next(r for r in reports_data["reports"] if r["id"] == eval_id)
            self.assertEqual(rep_in_list["report_language"], "mr")
            print("✓ Farmer reports list returned report with report_language = 'mr'")

            # Check Language filtering in Farmer API
            filter_mr = self.client.get("/api/farmer/reports?language=mr")
            filter_mr_data = filter_mr.get_json()
            self.assertGreaterEqual(len(filter_mr_data["reports"]), 1)
            for r in filter_mr_data["reports"]:
                self.assertEqual(r["report_language"], "mr")
            print("✓ Farmer reports filtered by language='mr' successfully")

            # Check PDF download route
            pdf_resp = self.client.get(f"/reports/download/Onion_Report_{updated_eval.report_id}.pdf")
            self.assertEqual(pdf_resp.status_code, 200)
            self.assertEqual(pdf_resp.headers["Content-Type"], "application/pdf")
            self.assertGreater(len(pdf_resp.data), 10000)
            print("✓ Farmer successfully downloaded Marathi PDF report")


if __name__ == "__main__":
    unittest.main()
