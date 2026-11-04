import os
import unittest
from datetime import datetime, timezone

from app import create_app
from backend.database.db import db
from backend.models.evaluation import Evaluation
from backend.models.farmer import FarmerProfile
from backend.models.officer import OfficerFarmer, OfficerProfile
from backend.models.user import User
from config import Config


class FarmerWorkflowEndToEndTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            test_farmers = FarmerProfile.query.join(User).filter(User.name.ilike('%Test Kailash%')).all()
            for f in test_farmers:
                fid = f.id
                uid = f.user_id
                from backend.models.evaluation import EvaluationItem, EvaluationImage
                from backend.models.transaction import ProcurementTransaction
                OfficerFarmer.query.filter_by(farmer_id=fid).delete()
                for ev in Evaluation.query.filter_by(farmer_id=fid).all():
                    ProcurementTransaction.query.filter_by(evaluation_id=ev.id).delete()
                    EvaluationItem.query.filter_by(evaluation_id=ev.id).delete()
                    EvaluationImage.query.filter_by(evaluation_id=ev.id).delete()
                    db.session.delete(ev)
                db.session.delete(f)
                if uid:
                    u = db.session.get(User, uid)
                    if u:
                        db.session.delete(u)
            db.session.commit()

    def test_full_farmer_workflow_journey(self):
        client = self.client
        ts = int(datetime.now(timezone.utc).timestamp())
        farmer_phone = f"99{ts % 100000000:08d}"

        # ---------------------------------------------------------
        # Step 1: Farmer Register ONLY via Farmer Portal
        # ---------------------------------------------------------
        res_reg = client.post("/api/auth/register/farmer", json={
            "name": "Test Kailash",
            "phone": farmer_phone,
            "email": f"test_kailash_{ts}@example.com",
            "village": "Chandwad",
            "taluka": "Chandwad",
            "district": "Nashik",
            "state": "Maharashtra",
            "password": "farmerpassword123",
            "confirm_password": "farmerpassword123"
        })
        self.assertEqual(res_reg.status_code, 201)
        reg_data = res_reg.get_json()
        self.assertTrue(reg_data["success"])
        farmer_id = reg_data["farmer_id"]
        self.assertTrue(farmer_id.startswith("FMR-"), f"Farmer ID should start with FMR-, got {farmer_id}")

        # Verify saved in central Farmer Registry
        with self.app.app_context():
            central_farmer = FarmerProfile.query.filter_by(farmer_id=farmer_id).first()
            self.assertIsNotNone(central_farmer, "Farmer must be present in central Farmer Registry")
            self.assertEqual(central_farmer.user.name, "Test Kailash")
            self.assertEqual(central_farmer.user.phone, farmer_phone)
            central_farmer_db_id = central_farmer.id

        # ---------------------------------------------------------
        # Step 2: Verify NOT automatically in Officer's list
        # ---------------------------------------------------------
        # Login as Officer
        res_off_login = client.post("/api/auth/login", json={
            "identifier": "OFF-2026-001",
            "password": "officer123",
            "role": "officer"
        })
        self.assertEqual(res_off_login.status_code, 200)

        # Check officer's farmer list - Kailash must NOT be in it
        res_my_farmers = client.get("/api/officer/farmers")
        self.assertEqual(res_my_farmers.status_code, 200)
        my_farmers_data = res_my_farmers.get_json()
        officer_farmer_ids = [f["farmer_id"] for f in my_farmers_data["farmers"]]
        self.assertNotIn(farmer_id, officer_farmer_ids, "Newly registered farmer must NOT be automatically added to officer's list")

        # ---------------------------------------------------------
        # Step 3: Officer attempts to register farmer -> MUST BE BLOCKED
        # ---------------------------------------------------------
        res_blocked = client.post("/api/officer/farmers", json={
            "name": "Should Fail",
            "phone": "9999999999",
            "village": "Nowhere",
            "taluka": "Nowhere",
            "district": "Nashik"
        })
        self.assertEqual(res_blocked.status_code, 403, "Officer must NOT be allowed to register farmers")

        # ---------------------------------------------------------
        # Step 4: Officer searches an unknown farmer -> exact message
        # ---------------------------------------------------------
        res_unknown = client.get("/api/officer/farmers/search?query=NONEXISTENT_FARMER_99999")
        self.assertEqual(res_unknown.status_code, 404)
        self.assertEqual(
            res_unknown.get_json()["error"],
            "Farmer not found. Please ask the farmer to register through the Farmer Portal."
        )

        # ---------------------------------------------------------
        # Step 5: Officer searches existing farmer using Farmer ID
        # ---------------------------------------------------------
        res_search_id = client.get(f"/api/officer/farmers/search?query={farmer_id}")
        self.assertEqual(res_search_id.status_code, 200)
        search_id_data = res_search_id.get_json()
        self.assertTrue(search_id_data["success"])
        self.assertEqual(search_id_data["farmer"]["farmer_id"], farmer_id)
        self.assertFalse(search_id_data["is_in_my_list"])

        # Officer searches existing farmer using Mobile Number
        res_search_phone = client.get(f"/api/officer/farmers/search?query={farmer_phone}")
        self.assertEqual(res_search_phone.status_code, 200)
        search_phone_data = res_search_phone.get_json()
        self.assertTrue(search_phone_data["success"])
        self.assertEqual(search_phone_data["farmer"]["phone"], farmer_phone)

        # ---------------------------------------------------------
        # Step 6: Officer clicks "Add to My Farmers"
        # ---------------------------------------------------------
        res_add = client.post("/api/officer/farmers/add", json={
            "farmer_id": farmer_id
        })
        self.assertEqual(res_add.status_code, 201)
        add_data = res_add.get_json()
        self.assertTrue(add_data["success"])

        # Verify farmer is now in officer's My Farmers list
        res_my_farmers_after = client.get("/api/officer/farmers")
        self.assertEqual(res_my_farmers_after.status_code, 200)
        my_ids_after = [f["farmer_id"] for f in res_my_farmers_after.get_json()["farmers"]]
        self.assertIn(farmer_id, my_ids_after, "Farmer must now be in officer's My Farmers list")

        # ---------------------------------------------------------
        # Step 7: Officer can Remove farmer from list (NOT from central registry)
        # ---------------------------------------------------------
        res_remove = client.post("/api/officer/farmers/remove", json={
            "farmer_profile_id": central_farmer_db_id
        })
        self.assertEqual(res_remove.status_code, 200)

        # Verify farmer is no longer in officer's list
        res_my_after_remove = client.get("/api/officer/farmers")
        my_ids_removed = [f["farmer_id"] for f in res_my_after_remove.get_json()["farmers"]]
        self.assertNotIn(farmer_id, my_ids_removed, "Farmer should be removed from officer's list")

        # CRITICAL: Verify farmer STILL exists in central registry!
        with self.app.app_context():
            still_in_registry = FarmerProfile.query.filter_by(farmer_id=farmer_id).first()
            self.assertIsNotNone(still_in_registry, "Removing from officer list must NOT delete from central Farmer Registry")

        # Re-add farmer to officer's list for evaluation step
        res_readd = client.post("/api/officer/farmers/add", json={"farmer_id": farmer_id})
        self.assertEqual(res_readd.status_code, 201)

        # ---------------------------------------------------------
        # Step 8: New Evaluation: select farmer & run AI Pipeline
        # ---------------------------------------------------------
        # Verify lookup works for officer's farmer
        res_lookup = client.get(f"/api/officer/farmer-lookup/{farmer_id}")
        self.assertEqual(res_lookup.status_code, 200)
        self.assertEqual(res_lookup.get_json()["farmer"]["farmer_id"], farmer_id)

        sample1 = os.path.join(Config.STATIC_SAMPLES_FOLDER, "onion1.jpg")
        self.assertTrue(os.path.exists(sample1), f"Sample image should exist at {sample1}")

        with open(sample1, "rb") as f1:
            data = {
                "farmer_id": farmer_id,
                "images": [
                    (f1, "batch_sample1.jpg")
                ]
            }
            res_eval = client.post("/api/officer/evaluate", data=data, content_type="multipart/form-data")

        self.assertEqual(res_eval.status_code, 200)
        eval_data = res_eval.get_json()
        self.assertTrue(eval_data["success"])
        eval_id = eval_data["evaluation_id"]
        self.assertGreater(eval_data["results"]["total_onions"], 0)

        # ---------------------------------------------------------
        # Step 9: Confirm Evaluation & Generate Certified PDF Report
        # ---------------------------------------------------------
        res_confirm = client.post(f"/api/officer/evaluate/{eval_id}/confirm")
        self.assertEqual(res_confirm.status_code, 200)
        confirm_data = res_confirm.get_json()
        self.assertTrue(confirm_data["success"])
        report_id = confirm_data["report_id"]
        self.assertTrue(report_id.startswith("ONR-"))

        # Download PDF Report
        pdf_res = client.get(confirm_data["pdf_url"])
        self.assertEqual(pdf_res.status_code, 200)
        self.assertEqual(pdf_res.content_type, "application/pdf")
        self.assertGreater(len(pdf_res.data), 1000)

        print("\n=======================================================")
        print(f"✓ FULL JOURNEY VERIFIED:")
        print(f"  1. Farmer Registered: {farmer_id} ({farmer_phone})")
        print(f"  2. Registry Search by ID & Mobile: SUCCESS")
        print(f"  3. Added to Officer's List: SUCCESS")
        print(f"  4. Removed & Verified Central Preservation: SUCCESS")
        print(f"  5. Evaluation with AI Detection & Grading: SUCCESS")
        print(f"  6. Report Created: {report_id}")
        print(f"  7. PDF Downloaded: {len(pdf_res.data)} bytes")
        print("=======================================================\n")


if __name__ == "__main__":
    unittest.main()
