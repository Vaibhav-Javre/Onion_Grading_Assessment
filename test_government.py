import os
import unittest

from app import create_app
from backend.database.db import db
from backend.models.audit import AuditLog
from backend.models.evaluation import Evaluation
from backend.models.farmer import FarmerProfile
from backend.models.officer import OfficerProfile
from backend.models.transaction import ProcurementTransaction
from backend.models.user import User
from config import Config


class GovernmentPortalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def test_01_government_seeding_and_admin_user(self):
        with self.app.app_context():
            admin = User.query.filter_by(role="government").first()
            self.assertIsNotNone(admin, "Government Admin user must exist")
            self.assertEqual(admin.email, "admin@agri.gov.in")
            self.assertTrue(admin.check_password("GovAdmin@2026"))

            # Transactions check
            txns = ProcurementTransaction.query.all()
            self.assertGreaterEqual(len(txns), 1, "Seeded transactions should exist")
            first_txn = txns[0]
            self.assertTrue(first_txn.transaction_id.startswith("TXN-"))
            self.assertIsNotNone(first_txn.total_onions)

            # Audit logs check
            logs = AuditLog.query.all()
            self.assertGreaterEqual(len(logs), 1, "Audit logs must exist")
            print(f"✓ Government Admin and Transactions verified: {len(txns)} transactions, {len(logs)} audit logs.")

    def test_02_government_auth_and_rbac(self):
        client = self.app.test_client()

        # 1. Anonymous access -> 401
        res = client.get("/api/government/dashboard")
        self.assertEqual(res.status_code, 401)

        # 2. Farmer access -> 403 Forbidden
        client.post("/api/auth/login", json={
            "identifier": "9876543210",
            "password": "farmer123",
            "role": "farmer"
        })
        res = client.get("/api/government/dashboard")
        self.assertEqual(res.status_code, 403, "Farmer must be blocked from government APIs")

        # 3. Officer access -> 403 Forbidden
        client.post("/api/auth/login", json={
            "identifier": "OFF-2026-001",
            "password": "officer123",
            "role": "officer"
        })
        res = client.get("/api/government/dashboard")
        self.assertEqual(res.status_code, 403, "Officer must be blocked from government APIs")

        # 4. Government Admin login -> 200
        res_login = client.post("/api/auth/login", json={
            "identifier": "admin@agri.gov.in",
            "password": "GovAdmin@2026",
            "role": "government"
        })
        self.assertEqual(res_login.status_code, 200)
        login_data = res_login.get_json()
        self.assertTrue(login_data["success"])
        self.assertEqual(login_data["role"], "government")
        self.assertEqual(login_data["redirect_url"], "/government/dashboard")

        # 5. Access Dashboard with Government credentials -> 200
        res_dash = client.get("/api/government/dashboard")
        self.assertEqual(res_dash.status_code, 200)
        data = res_dash.get_json()
        self.assertTrue(data["success"])
        self.assertIn("summary", data)
        self.assertIn("total_farmers", data["summary"])
        self.assertIn("total_evaluations", data["summary"])
        self.assertIn("total_onions", data["summary"])
        self.assertIn("recent_transactions", data)
        print("✓ RBAC security and Government login verified.")

    def test_03_government_farmer_and_officer_apis(self):
        client = self.app.test_client()
        client.post("/api/auth/login", json={
            "identifier": "admin@agri.gov.in",
            "password": "GovAdmin@2026",
            "role": "government"
        })

        # List farmers
        res_farmers = client.get("/api/government/farmers")
        self.assertEqual(res_farmers.status_code, 200)
        farmers_data = res_farmers.get_json()
        self.assertTrue(farmers_data["success"])
        self.assertGreaterEqual(farmers_data["count"], 2)
        f1 = farmers_data["farmers"][0]
        self.assertIn("farmer_id", f1)
        self.assertIn("total_evaluations", f1)
        self.assertIn("grades", f1)

        # Farmer detail
        farmer_id = f1["id"]
        res_detail = client.get(f"/api/government/farmers/{farmer_id}")
        self.assertEqual(res_detail.status_code, 200)
        detail_data = res_detail.get_json()
        self.assertTrue(detail_data["success"])
        self.assertIn("evaluations", detail_data)
        self.assertIn("transactions", detail_data)

        # List officers
        res_officers = client.get("/api/government/officers")
        self.assertEqual(res_officers.status_code, 200)
        officers_data = res_officers.get_json()
        self.assertTrue(officers_data["success"])
        self.assertGreaterEqual(officers_data["count"], 1)
        o1 = officers_data["officers"][0]
        self.assertIn("officer_id", o1)
        self.assertIn("procurement_center", o1)

        # Officer detail
        officer_id = o1["id"]
        res_off_detail = client.get(f"/api/government/officers/{officer_id}")
        self.assertEqual(res_off_detail.status_code, 200)
        print("✓ Government Farmer and Officer directory APIs verified.")

    def test_04_transactions_api_and_export(self):
        client = self.app.test_client()
        client.post("/api/auth/login", json={
            "identifier": "admin@agri.gov.in",
            "password": "GovAdmin@2026",
            "role": "government"
        })

        # List transactions
        res_txns = client.get("/api/government/transactions")
        self.assertEqual(res_txns.status_code, 200)
        data = res_txns.get_json()
        self.assertTrue(data["success"])
        self.assertGreaterEqual(data["count"], 1)

        t1 = data["transactions"][0]
        self.assertTrue(t1["transaction_id"].startswith("TXN-"))
        self.assertIn("economics", t1)
        self.assertIn("counts", t1)

        # Test filter by result
        res_filter = client.get("/api/government/transactions?result=Grade A")
        self.assertEqual(res_filter.status_code, 200)

        # Test CSV export
        res_csv = client.get("/api/government/transactions?export=csv")
        self.assertEqual(res_csv.status_code, 200)
        self.assertEqual(res_csv.content_type, "text/csv; charset=utf-8")
        self.assertIn(b"Transaction ID", res_csv.data)

        # Detailed transaction
        res_single = client.get(f"/api/government/transactions/{t1['transaction_id']}")
        self.assertEqual(res_single.status_code, 200)
        print("✓ Digital Procurement Transactions & CSV Export verified.")

    def test_05_reports_management_and_pdf_access(self):
        client = self.app.test_client()
        client.post("/api/auth/login", json={
            "identifier": "admin@agri.gov.in",
            "password": "GovAdmin@2026",
            "role": "government"
        })

        # List reports
        res_reports = client.get("/api/government/reports")
        self.assertEqual(res_reports.status_code, 200)
        data = res_reports.get_json()
        self.assertTrue(data["success"])
        self.assertGreaterEqual(data["count"], 1)

        rep = data["reports"][0]
        report_id = rep["report_id"]

        # Government user can access PDF
        res_pdf = client.get(f"/api/reports/{report_id}/pdf")
        # May redirect (302) to named download URL
        if res_pdf.status_code == 302:
            download_url = res_pdf.headers["Location"]
            res_pdf = client.get(download_url)
        self.assertEqual(res_pdf.status_code, 200)
        self.assertEqual(res_pdf.content_type, "application/pdf")
        print(f"✓ Government Report Registry & PDF Download verified for {report_id}.")

    def test_06_audit_logs_search_and_analytics(self):
        client = self.app.test_client()
        client.post("/api/auth/login", json={
            "identifier": "admin@agri.gov.in",
            "password": "GovAdmin@2026",
            "role": "government"
        })

        # Audit logs list
        res_logs = client.get("/api/government/audit-logs")
        self.assertEqual(res_logs.status_code, 200)
        log_data = res_logs.get_json()
        self.assertTrue(log_data["success"])
        self.assertGreaterEqual(log_data["count"], 1)

        # Macro Analytics
        res_analytics = client.get("/api/government/analytics")
        self.assertEqual(res_analytics.status_code, 200)
        an_data = res_analytics.get_json()
        self.assertTrue(an_data["success"])
        self.assertIn("grade_distribution", an_data)
        self.assertIn("quality_class_distribution", an_data)
        self.assertIn("district_stats", an_data)

        # Omni search
        res_search = client.get("/api/government/search?q=FMR-2026-0001")
        self.assertEqual(res_search.status_code, 200)
        search_data = res_search.get_json()
        self.assertTrue(search_data["success"])
        self.assertGreaterEqual(len(search_data["results"]["farmers"]), 1)
        print("✓ Audit Logs, Macro Analytics, and Omni-Search verified.")

    def test_07_transaction_hook_on_evaluation_confirm(self):
        client = self.app.test_client()

        # Login as officer
        client.post("/api/auth/login", json={
            "identifier": "OFF-2026-001",
            "password": "officer123",
            "role": "officer"
        })

        sample1 = os.path.join(Config.STATIC_SAMPLES_FOLDER, "onion1.jpg")
        with open(sample1, "rb") as f1:
            data = {
                "farmer_id": "FMR-2026-0001",
                "images": [(f1, "hook_test.jpg")]
            }
            res_eval = client.post("/api/officer/evaluate", data=data, content_type="multipart/form-data")

        self.assertEqual(res_eval.status_code, 200)
        eval_id = res_eval.get_json()["evaluation_id"]

        # Confirm evaluation
        res_confirm = client.post(f"/api/officer/evaluate/{eval_id}/confirm", json={
            "quantity_quintals": 12.5,
            "mandi_modal_price": 2400.0
        })
        self.assertEqual(res_confirm.status_code, 200)
        confirm_data = res_confirm.get_json()
        report_id = confirm_data["report_id"]

        # Verify that ProcurementTransaction was automatically created!
        with self.app.app_context():
            txn = ProcurementTransaction.query.filter_by(report_id=report_id).first()
            self.assertIsNotNone(txn, "ProcurementTransaction must be automatically created upon confirmation")
            self.assertTrue(txn.transaction_id.startswith("TXN-"))
            self.assertEqual(txn.quantity_quintals, 12.5)
            self.assertGreater(txn.total_payout, 0.0)

            # Verify audit log was recorded
            audit_confirm = AuditLog.query.filter_by(action="CONFIRM_EVALUATION", entity_id=report_id).first()
            self.assertIsNotNone(audit_confirm, "CONFIRM_EVALUATION audit log must be recorded")
            print(f"✓ Automatic Transaction Hook verified: {txn.transaction_id} created for {report_id}.")


if __name__ == "__main__":
    unittest.main()
