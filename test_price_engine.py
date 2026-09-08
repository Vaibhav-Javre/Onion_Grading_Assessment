import os
import unittest
from app import create_app
from backend.database.db import db
from backend.models.evaluation import Evaluation
from backend.services.price_engine import PriceEngine
from config import Config

class TestPriceEngine(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()

    def tearDown(self):
        self.app_context.pop()

    def test_example_calculation_from_spec(self):
        """
        Tests the exact user prompt example:
        60% Grade A + 30% URS + 10% Rejected
        Modal Price = 2500
        Expected Quality Score = 84%
        Expected Estimated Price = 2100
        """
        calc = PriceEngine.calculate_price_estimation(
            grade_a_pct=60.0,
            urs_pct=30.0,
            rejected_pct=10.0,
            modal_price=2500.0,
            quantity_quintals=20.0
        )
        self.assertEqual(calc["quality_score_pct"], 84.0)
        self.assertEqual(calc["estimated_price_per_quintal"], 2100.0)
        self.assertEqual(calc["total_payout"], 42000.0)
        self.assertEqual(calc["quantity_quintals"], 20.0)

    def test_perfect_grade_a(self):
        """100% Grade A -> Quality Score = 100%, Price = Modal Price"""
        calc = PriceEngine.calculate_price_estimation(
            grade_a_pct=100.0,
            urs_pct=0.0,
            rejected_pct=0.0,
            modal_price=2400.0,
            quantity_quintals=15.0
        )
        self.assertEqual(calc["quality_score_pct"], 100.0)
        self.assertEqual(calc["estimated_price_per_quintal"], 2400.0)
        self.assertEqual(calc["total_payout"], 36000.0)

    def test_all_rejected(self):
        """100% Rejected -> Quality Score = 0%, Price = 0"""
        calc = PriceEngine.calculate_price_estimation(
            grade_a_pct=0.0,
            urs_pct=0.0,
            rejected_pct=100.0,
            modal_price=2400.0,
            quantity_quintals=10.0
        )
        self.assertEqual(calc["quality_score_pct"], 0.0)
        self.assertEqual(calc["estimated_price_per_quintal"], 0.0)
        self.assertEqual(calc["total_payout"], 0.0)

    def test_all_urs(self):
        """100% URS -> Quality Score = 80%, Price = Modal Price * 0.8"""
        calc = PriceEngine.calculate_price_estimation(
            grade_a_pct=0.0,
            urs_pct=100.0,
            rejected_pct=0.0,
            modal_price=2000.0,
            quantity_quintals=5.0
        )
        self.assertEqual(calc["quality_score_pct"], 80.0)
        self.assertEqual(calc["estimated_price_per_quintal"], 1600.0)
        self.assertEqual(calc["total_payout"], 8000.0)

    def test_lasalgaon_reference_privacy(self):
        """Ensures DATA_GOV_API_KEY is not exposed in the reference price payload"""
        ref = PriceEngine.get_lasalgaon_reference_price()
        # Verify API key is never in the returned dict
        self.assertNotIn("api_key", ref)
        self.assertNotIn("api-key", ref)
        self.assertNotIn(Config.DATA_GOV_API_KEY, str(ref))

    def test_market_endpoint_privacy(self):
        """Tests the public /api/market/lasalgaon-reference endpoint"""
        res = self.client.get("/api/market/lasalgaon-reference")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertIn("data", data)
        # Ensure API key is not exposed
        self.assertNotIn(Config.DATA_GOV_API_KEY, res.get_data(as_text=True))

    def test_evaluation_schema_and_dict(self):
        """Verifies Evaluation model contains all price snapshot fields in to_dict"""
        evaluation = Evaluation.query.first()
        if evaluation:
            d = evaluation.to_dict()
            self.assertIn("price_estimation", d)
            pe = d["price_estimation"]
            self.assertIn("mandi_name", pe)
            self.assertIn("mandi_modal_price", pe)
            self.assertIn("quality_score_pct", pe)
            self.assertIn("estimated_price_per_quintal", pe)
            self.assertIn("quantity_quintals", pe)
            self.assertIn("total_payout", pe)

if __name__ == "__main__":
    unittest.main()
