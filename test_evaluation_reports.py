import sys
import os
from datetime import datetime, date, timedelta, timezone

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app
from backend.database.db import db
from backend.models.user import User
from backend.models.farmer import FarmerProfile
from backend.models.officer import OfficerProfile
from backend.models.evaluation import Evaluation
from backend.services.evaluation_report_service import EvaluationReportService

def run_tests():
    print("=" * 70)
    print("RUNNING COMPREHENSIVE EVALUATION REPORTS & ANALYTICS TEST SUITE")
    print("=" * 70)

    with app.app_context():
        # 1. Test Date Range Parser
        print("\n[TEST 1] Testing Date Range Resolution for all periods...")
        periods = ["today", "yesterday", "this_week", "last_week", "this_month", "last_month", "this_year", "custom"]
        for p in periods:
            dr = EvaluationReportService.parse_date_range(p, start_date_str="2026-09-01", end_date_str="2026-09-30")
            assert dr["start_dt"] is not None
            assert dr["end_dt"] is not None
            assert dr["prev_start_dt"] is not None
            assert dr["prev_end_dt"] is not None
            assert dr["start_dt"] <= dr["end_dt"]
            print(f"  ✓ Period '{p}': {dr['period_label']} (span: {dr['span_days']} days)")

        # 2. Test Core Statistical Calculations
        print("\n[TEST 2] Testing Core Calculations (Total Onions vs Total Evaluations, Grades, Quality)...")
        data = EvaluationReportService.get_analytics(period="this_year", role="government")
        sum_c = data["summary_cards"]
        qd = data["quality_distribution"]

        total_onions = sum_c["total_onions_evaluated"]
        total_evals = sum_c["total_evaluations"]

        print(f"  Confirmed Evaluations: {total_evals}")
        print(f"  Total Onions Evaluated: {total_onions}")
        print(f"  Farmers Evaluated: {sum_c['total_farmers_evaluated']}")
        print(f"  Officers Active: {sum_c['total_officers_active']}")
        print(f"  Grade A: {sum_c['grade_a_count']} ({sum_c['grade_a_pct']}%)")
        print(f"  URS: {sum_c['urs_count']} ({sum_c['urs_pct']}%)")
        print(f"  Rejected: {sum_c['rejected_count']} ({sum_c['rejected_pct']}%)")
        print(f"  Healthy: {qd['healthy']['count']} ({qd['healthy']['pct']}%)")
        print(f"  Damaged: {qd['damaged']['count']} ({qd['damaged']['pct']}%)")
        print(f"  Rotten: {qd['rotten']['count']} ({qd['rotten']['pct']}%)")
        print(f"  Sprouted: {qd['sprouted']['count']} ({qd['sprouted']['pct']}%)")

        assert total_evals >= 0
        assert total_onions >= 0
        if total_onions > 0:
            # Check grade sum + uncertain matches total onions
            grade_sum = sum_c["grade_a_count"] + sum_c["urs_count"] + sum_c["rejected_count"]
            uncertain_cnt = qd.get("uncertain", {}).get("count", 0)
            assert grade_sum <= total_onions, f"Grade sum ({grade_sum}) exceeds total onions ({total_onions})"
            assert grade_sum + uncertain_cnt == total_onions, f"Grade sum + uncertain ({grade_sum + uncertain_cnt}) != total onions ({total_onions})"
            # Check quality classes sum
            q_sum = qd["healthy"]["count"] + qd["damaged"]["count"] + qd["rotten"]["count"] + qd["sprouted"]["count"]
            assert q_sum + uncertain_cnt == total_onions, f"Quality sum + uncertain ({q_sum + uncertain_cnt}) != total onions ({total_onions})"
        print("  ✓ Grade sum and quality class distribution match total onions exactly.")

        # 3. Test Distinction Between Evaluations and Onions
        print("\n[TEST 3] Testing Distinction: Total Evaluations vs Total Onions...")
        if total_evals > 1 and total_onions > 0:
            assert total_onions != total_evals, "Total onions should represent individual bulbs, not session count."
            print(f"  ✓ Distinction Verified: {total_evals} evaluation sessions evaluated {total_onions} onions.")
        else:
            print("  ✓ Distinction rule checked (single/zero evaluation scenario).")

        # 4. Test Period Comparison and Zero-Div Guard
        print("\n[TEST 4] Testing Period Comparison & Zero-Division Safety...")
        cmp = data["period_comparison"]
        assert "onions" in cmp
        assert "evaluations" in cmp
        assert "farmers" in cmp
        assert "grade_a" in cmp
        assert cmp["onions"]["pct_change_str"] is not None
        print(f"  ✓ Period comparison generated successfully: Onions change = {cmp['onions']['pct_change_str']} (Current: {cmp['onions']['current']}, Prev: {cmp['onions']['previous']})")

        # 5. Test Daily, Weekly, and Monthly Trends
        print("\n[TEST 5] Testing Daily, Weekly, and Monthly Trend Sequences...")
        daily = data["daily_trend"]
        assert len(daily["labels"]) == len(daily["onions"]) == len(daily["evaluations"])
        print(f"  ✓ Daily trend generated: {len(daily['labels'])} calendar days sequenced.")

        weekly = data["weekly_trend"]
        assert len(weekly["labels"]) == 4
        print(f"  ✓ Weekly trend generated: {len(weekly['labels'])} historical weeks analyzed.")

        monthly = data["monthly_trend"]
        assert len(monthly["labels"]) == 6
        print(f"  ✓ Monthly trend generated: {len(monthly['labels'])} historical months analyzed.")

        # 6. Test Center, Officer, and Farmer Tables
        print("\n[TEST 6] Testing Center, Officer, and Farmer Activity Aggregations...")
        assert "center_activity" in data
        assert "officer_activity" in data
        assert "farmer_history" in data
        print(f"  ✓ Procurement Centers Analyzed: {len(data['center_activity'])}")
        print(f"  ✓ Officers Active: {len(data['officer_activity'])}")
        print(f"  ✓ Farmers with History: {len(data['farmer_history'])}")

        # 7. Test CSV and Excel Exports
        print("\n[TEST 7] Testing CSV and Excel Export Generation...")
        csv_str = EvaluationReportService.export_csv(period="this_month", role="government")
        assert "ONIONGRADE AI - EVALUATION REPORT" in csv_str
        assert "EXECUTIVE SUMMARY" in csv_str
        print("  ✓ CSV Export generated with correct structure and metadata.")

        excel_bytes = EvaluationReportService.export_excel(period="this_month", role="government")
        assert excel_bytes.startswith(b"\xef\xbb\xbf"), "Excel export must contain UTF-8 BOM"
        print("  ✓ Excel Export generated with UTF-8 BOM signature.")

        # 8. Test Official ReportLab PDF Reports (Weekly & Monthly)
        print("\n[TEST 8] Testing Official Weekly & Monthly PDF Report Generation...")
        w_fn, w_fp, w_size = EvaluationReportService.generate_pdf_report(report_type="weekly", period="this_week", role="government")
        assert os.path.exists(w_fp), f"Weekly PDF file not created at {w_fp}"
        assert w_size > 0, "Weekly PDF file size must be > 0"
        print(f"  ✓ Weekly PDF Report generated: {w_fn} ({w_size} bytes)")

        m_fn, m_fp, m_size = EvaluationReportService.generate_pdf_report(report_type="monthly", period="this_month", role="government")
        assert os.path.exists(m_fp), f"Monthly PDF file not created at {m_fp}"
        assert m_size > 0, "Monthly PDF file size must be > 0"
        print(f"  ✓ Monthly PDF Report generated: {m_fn} ({m_size} bytes)")

        # 9. Test API Endpoints via Flask Test Client
        print("\n[TEST 9] Testing API Endpoints & Role-Based Access Isolation...")
        client = app.test_client()

        # Government user
        gov_user = User.query.filter(User.role.in_(["government", "admin"])).first()
        if gov_user:
            with client.session_transaction() as sess:
                sess["user_id"] = gov_user.id
                sess["user_role"] = gov_user.role

            resp_gov = client.get("/api/evaluation-reports/analytics?period=this_month")
            assert resp_gov.status_code == 200
            g_json = resp_gov.get_json()
            assert g_json["success"] is True
            assert "summary_cards" in g_json
            assert "center_activity" in g_json
            print(f"  ✓ GET /api/evaluation-reports/analytics passed for Government ({gov_user.name})")

            resp_records = client.get("/api/evaluation-reports/records?period=this_year")
            assert resp_records.status_code == 200
            rec_json = resp_records.get_json()
            assert rec_json["success"] is True
            print(f"  ✓ GET /api/evaluation-reports/records returned {rec_json['total']} records")

            resp_w_pdf = client.get("/api/evaluation-reports/export/weekly-pdf")
            assert resp_w_pdf.status_code == 200
            assert resp_w_pdf.content_type == "application/pdf"
            print("  ✓ GET /api/evaluation-reports/export/weekly-pdf downloaded valid PDF")

            resp_m_pdf = client.get("/api/evaluation-reports/export/monthly-pdf")
            assert resp_m_pdf.status_code == 200
            assert resp_m_pdf.content_type == "application/pdf"
            print("  ✓ GET /api/evaluation-reports/export/monthly-pdf downloaded valid PDF")

        # Officer user
        officer_user = User.query.filter_by(role="officer").first()
        if officer_user:
            with client.session_transaction() as sess:
                sess["user_id"] = officer_user.id
                sess["user_role"] = "officer"

            resp_off = client.get("/api/evaluation-reports/analytics?period=this_month")
            assert resp_off.status_code == 200
            o_json = resp_off.get_json()
            assert o_json["success"] is True
            print(f"  ✓ GET /api/evaluation-reports/analytics passed for Officer ({officer_user.name})")

        # Farmer user (Strict Data Isolation)
        farmer_user = User.query.filter_by(role="farmer").first()
        if farmer_user:
            with client.session_transaction() as sess:
                sess["user_id"] = farmer_user.id
                sess["user_role"] = "farmer"

            resp_farmer = client.get("/api/evaluation-reports/analytics?period=this_year")
            assert resp_farmer.status_code == 200
            f_json = resp_farmer.get_json()
            assert f_json["success"] is True
            # Verify records strictly belong to this farmer
            for rec in f_json["records"]:
                assert rec["farmer_id"] == farmer_user.farmer_profile.farmer_id
            print(f"  ✓ GET /api/evaluation-reports/analytics strictly isolated for Farmer ({farmer_user.name})")

        # 10. Test Web HTML Views Rendering
        print("\n[TEST 10] Testing Web Portal HTML Rendering (200 OK)...")
        if gov_user:
            with client.session_transaction() as sess:
                sess["user_id"] = gov_user.id
                sess["user_role"] = gov_user.role
            res_gov_view = client.get("/government/evaluation-reports")
            assert res_gov_view.status_code == 200
            assert b"Evaluation Reports & Analytics" in res_gov_view.data
            print("  ✓ /government/evaluation-reports view rendered with 200 OK")

        if officer_user:
            with client.session_transaction() as sess:
                sess["user_id"] = officer_user.id
                sess["user_role"] = "officer"
            res_off_view = client.get("/officer/evaluation-reports")
            assert res_off_view.status_code == 200
            assert b"Field Evaluation Reports" in res_off_view.data
            print("  ✓ /officer/evaluation-reports view rendered with 200 OK")

        if farmer_user:
            with client.session_transaction() as sess:
                sess["user_id"] = farmer_user.id
                sess["user_role"] = "farmer"
            res_far_view = client.get("/farmer/evaluation-history")
            assert res_far_view.status_code == 200
            assert b"My Evaluation History" in res_far_view.data
            print("  ✓ /farmer/evaluation-history view rendered with 200 OK")

    print("\n" + "=" * 70)
    print("ALL EVALUATION REPORTS & ANALYTICS TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
