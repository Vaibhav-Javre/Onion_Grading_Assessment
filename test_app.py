import os
import unittest
from app import create_app
from backend.database.db import db
from backend.models.user import User
from backend.models.farmer import FarmerProfile
from backend.models.officer import OfficerProfile
from backend.models.evaluation import Evaluation, EvaluationImage, EvaluationItem
from backend.models.report import Report
from backend.models.market import MarketPrice
from backend.ai.pipeline import evaluate_onion_image, evaluate_multiple_onion_images
from backend.services.pdf_service import generate_evaluation_pdf
from backend.services.market_price_service import MarketPriceService
from config import Config

class OnionGradeSystemTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def test_01_database_and_seed_data(self):
        with self.app.app_context():
            # Verify officer exists
            officer = User.query.filter_by(role="officer").first()
            self.assertIsNotNone(officer, "Officer should be seeded")
            self.assertIsNotNone(officer.officer_profile, "Officer profile should exist")
            self.assertEqual(officer.officer_profile.officer_id, "OFF-2026-001")

            # Verify farmers exist
            farmers = FarmerProfile.query.all()
            self.assertGreaterEqual(len(farmers), 2, "At least 2 farmers should be seeded")

            # Verify evaluations exist
            evals = Evaluation.query.filter_by(status="confirmed").all()
            self.assertGreaterEqual(len(evals), 2, "At least 2 historical evaluations should be seeded")

            # Verify market prices seeded
            prices = MarketPrice.query.all()
            self.assertGreaterEqual(len(prices), 4, "Benchmark market prices should be seeded")
            print("✓ Database and Seed Data verified.")

    def test_02_authentication_and_passwords(self):
        with self.app.app_context():
            officer = User.query.filter_by(role="officer").first()
            self.assertTrue(officer.check_password("officer123"), "Officer password should verify")
            self.assertFalse(officer.check_password("wrongpw"), "Wrong password should fail")

            farmer = User.query.filter_by(phone="9876543210").first()
            self.assertIsNotNone(farmer, "Farmer 1 should exist")
            self.assertTrue(farmer.check_password("farmer123"), "Farmer password should verify")

        # Test API Login for Farmer
        res = self.client.post("/api/auth/login", json={
            "identifier": "9876543210",
            "password": "farmer123",
            "role": "farmer"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["role"], "farmer")

        # Test API Login for Officer
        res = self.client.post("/api/auth/login", json={
            "identifier": "OFF-2026-001",
            "password": "officer123",
            "role": "officer"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["role"], "officer")
        print("✓ Authentication & Password verification passed.")

    def test_03_role_authorization_and_report_security(self):
        client = self.app.test_client()
        # 1. Anonymous access to protected dashboard should fail with 401
        res = client.get("/api/farmer/dashboard")
        self.assertEqual(res.status_code, 401)

        # 2. Login as Farmer 1
        client.post("/api/auth/login", json={
            "identifier": "9876543210",
            "password": "farmer123",
            "role": "farmer"
        })

        # Farmer 1 can access own dashboard
        res = client.get("/api/farmer/dashboard")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])

        # Farmer 1 cannot access Officer endpoint (403 Forbidden)
        res = client.get("/api/officer/dashboard")
        self.assertEqual(res.status_code, 403)

        # Farmer 1 cannot access Farmer 2's report (ONR-2026-001090)
        res = client.get("/api/farmer/reports/ONR-2026-001090")
        self.assertEqual(res.status_code, 403, "Farmer 1 must be blocked from accessing Farmer 2's report")
        res_pdf = client.get("/api/reports/ONR-2026-001090/pdf")
        self.assertEqual(res_pdf.status_code, 403, "Farmer 1 must be blocked from downloading Farmer 2's PDF")

        # Farmer 1 can access own report (ONR-2026-001089)
        res_own = client.get("/api/farmer/reports/ONR-2026-001089")
        self.assertEqual(res_own.status_code, 200, "Farmer 1 should access own report")
        print("✓ Strict Role-Based Security & Farmer Report Isolation verified.")

    def test_04_ai_pipeline_inference(self):
        sample_img = os.path.join(Config.STATIC_SAMPLES_FOLDER, "onion1.jpg")
        self.assertTrue(os.path.exists(sample_img), f"Sample image should exist at {sample_img}")

        print("Testing AI pipeline on onion1.jpg...")
        results = evaluate_onion_image(sample_img)
        self.assertIn("total_onions", results)
        self.assertGreater(results["total_onions"], 0, "Should detect at least 1 onion")
        self.assertIn("Healthy", results["classes"])
        self.assertIn("Grade A", results["grades"])
        self.assertTrue(os.path.exists(results["annotated_image_path"]), "Annotated image must exist")
        print(f"✓ AI Pipeline Inference passed: {results['total_onions']} onions detected, "
              f"Healthy: {results['classes']['Healthy']['count']}, "
              f"Damaged: {results['classes']['Damaged']['count']}")

    def test_05_pdf_report_generation(self):
        with self.app.app_context():
            eval1 = Evaluation.query.filter_by(report_id="ONR-2026-001089").first()
            self.assertIsNotNone(eval1)
            pdf_fn, pdf_fp, pdf_size = generate_evaluation_pdf(eval1)
            self.assertTrue(os.path.exists(pdf_fp), f"Generated PDF must exist at {pdf_fp}")
            self.assertGreater(pdf_size, 1000, "PDF size should be > 1KB")
            print(f"✓ ReportLab PDF generation passed: {pdf_fn} ({pdf_size} bytes)")

    def test_06_market_price_service(self):
        with self.app.app_context():
            prices = MarketPriceService.get_market_prices()
            self.assertGreater(len(prices), 0, "Market prices list should not be empty")
            first_price = prices[0]
            self.assertIn("market_name", first_price)
            self.assertIn("modal_price", first_price)
            self.assertGreater(first_price["modal_price"], 0)

            # Test district filter
            nashik_prices = MarketPriceService.get_market_prices(district="Nashik")
            self.assertGreater(len(nashik_prices), 0, "Should find Nashik mandi prices")
            print(f"✓ Market Price Service verified: {len(prices)} mandis loaded.")

    def test_07_multi_image_evaluation_pipeline(self):
        sample1 = os.path.join(Config.STATIC_SAMPLES_FOLDER, "onion1.jpg")
        sample2 = os.path.join(Config.STATIC_SAMPLES_FOLDER, "onion2.jpg")
        self.assertTrue(os.path.exists(sample1))
        self.assertTrue(os.path.exists(sample2))

        print("Testing multi-image AI pipeline on 2 sample images...")
        results = evaluate_multiple_onion_images([sample1, sample2])
        self.assertEqual(results["total_images"], 2)
        self.assertGreaterEqual(results["total_onions"], 2)
        self.assertEqual(len(results["per_image_results"]), 2)
        self.assertTrue(os.path.exists(results["primary_annotated_image_path"]))
        self.assertIn("classes", results)
        self.assertIn("grades", results)
        self.assertIn("quality_summary", results)
        print(f"✓ Multi-Image AI Pipeline passed: {results['total_images']} images, "
              f"{results['total_onions']} total detected onions.")

    def test_08_multi_image_evaluation_endpoint(self):
        client = self.app.test_client()

        # Login as officer
        client.post("/api/auth/login", json={
            "identifier": "OFF-2026-001",
            "password": "officer123",
            "role": "officer"
        })

        sample1 = os.path.join(Config.STATIC_SAMPLES_FOLDER, "onion1.jpg")
        sample2 = os.path.join(Config.STATIC_SAMPLES_FOLDER, "onion2.jpg")

        with open(sample1, "rb") as f1, open(sample2, "rb") as f2:
            data = {
                "farmer_id": "FMR-2026-0001",
                "images": [
                    (f1, "sample_angle1.jpg"),
                    (f2, "sample_angle2.jpg")
                ]
            }
            res = client.post("/api/officer/evaluate", data=data, content_type="multipart/form-data")

        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertTrue(json_data["success"])
        eval_id = json_data["evaluation_id"]
        results = json_data["results"]
        self.assertEqual(results["total_images"], 2)
        self.assertEqual(len(results["images"]), 2)

        # Verify database record
        with self.app.app_context():
            evaluation = db.session.get(Evaluation, eval_id)
            self.assertIsNotNone(evaluation)
            self.assertEqual(evaluation.total_images, 2)
            self.assertEqual(len(evaluation.images), 2)
            self.assertGreaterEqual(len(evaluation.items), 2)

            # Test confirm evaluation & PDF generation
            res_confirm = client.post(f"/api/officer/evaluate/{eval_id}/confirm")
            self.assertEqual(res_confirm.status_code, 200)
            confirm_data = res_confirm.get_json()
            self.assertTrue(confirm_data["success"])
            self.assertTrue(confirm_data["report_id"].startswith("ONR-"))

            # Test PDF download
            pdf_res = client.get(confirm_data["pdf_url"])
            self.assertEqual(pdf_res.status_code, 200)
            self.assertEqual(pdf_res.content_type, "application/pdf")
            print(f"✓ Multi-Image API Endpoint & PDF generation verified for evaluation #{eval_id}.")

if __name__ == "__main__":
    unittest.main()
