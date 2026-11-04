import sys
import os
from datetime import datetime, timedelta, timezone

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app
from backend.database.db import db
from backend.models.user import User
from backend.models.farmer import FarmerProfile
from backend.models.officer import OfficerProfile
from backend.models.evaluation import Evaluation
from backend.models.inventory import InventoryItem, InventoryMovement, InventorySetting
from backend.services.predictive_inventory_service import PredictiveInventoryService

def run_tests():
    print("=" * 70)
    print("RUNNING COMPREHENSIVE PREDICTIVE INVENTORY & RECOMMENDATION TESTS")
    print("=" * 70)

    with app.app_context():
        # 1. Storage Life Planning - Grade A
        print("\n[TEST 1] Grade A Storage Life Planning (Configured Range: 70–80 Days)...")
        now = datetime.now(timezone.utc)
        
        # 20 days elapsed -> Green
        res_ga_green = PredictiveInventoryService.calculate_storage_life_status("Grade A", now - timedelta(days=20))
        assert res_ga_green["status_color"] == "GREEN", f"Expected GREEN, got {res_ga_green['status_color']}"
        assert res_ga_green["min_planning_days"] == 70
        assert res_ga_green["max_planning_days"] == 80
        assert res_ga_green["storage_age_days"] == 20
        assert res_ga_green["remaining_min_days"] == 50
        assert res_ga_green["remaining_max_days"] == 60
        print("  ✓ Grade A 20-day batch: GREEN, 50-60 days remaining window correctly computed.")

        # 60 days elapsed -> Yellow (Approaching lower boundary 70)
        res_ga_yellow = PredictiveInventoryService.calculate_storage_life_status("Grade A", now - timedelta(days=60))
        assert res_ga_yellow["status_color"] == "YELLOW", f"Expected YELLOW, got {res_ga_yellow['status_color']}"
        print("  ✓ Grade A 60-day batch: YELLOW (Approaching lower planning boundary).")

        # 75 days elapsed -> Orange (Near limit 70-80)
        res_ga_orange = PredictiveInventoryService.calculate_storage_life_status("Grade A", now - timedelta(days=75))
        assert res_ga_orange["status_color"] == "ORANGE", f"Expected ORANGE, got {res_ga_orange['status_color']}"
        print("  ✓ Grade A 75-day batch: ORANGE (Near upper planning limit).")

        # 85 days elapsed -> Red (Past limit > 80)
        res_ga_red = PredictiveInventoryService.calculate_storage_life_status("Grade A", now - timedelta(days=85))
        assert res_ga_red["status_color"] == "RED", f"Expected RED, got {res_ga_red['status_color']}"
        print("  ✓ Grade A 85-day batch: RED (Past configured planning limit).")

        # 2. Storage Life Planning - URS
        print("\n[TEST 2] URS Standard Storage Life Planning (Configured Range: 40–45 Days)...")
        # 15 days elapsed -> Green
        res_urs_green = PredictiveInventoryService.calculate_storage_life_status("URS", now - timedelta(days=15))
        assert res_urs_green["status_color"] == "GREEN"
        assert res_urs_green["min_planning_days"] == 40
        assert res_urs_green["max_planning_days"] == 45
        assert res_urs_green["remaining_min_days"] == 25
        assert res_urs_green["remaining_max_days"] == 30
        print("  ✓ URS 15-day batch: GREEN, 25-30 days remaining window correctly computed.")

        # 35 days elapsed -> Yellow (31-39)
        res_urs_yellow = PredictiveInventoryService.calculate_storage_life_status("URS", now - timedelta(days=35))
        assert res_urs_yellow["status_color"] == "YELLOW"
        print("  ✓ URS 35-day batch: YELLOW (Approaching 40-day boundary).")

        # 42 days elapsed -> Orange (40-45)
        res_urs_orange = PredictiveInventoryService.calculate_storage_life_status("URS", now - timedelta(days=42))
        assert res_urs_orange["status_color"] == "ORANGE"
        print("  ✓ URS 42-day batch: ORANGE (Near 45-day upper limit).")

        # 50 days elapsed -> Red (> 45)
        res_urs_red = PredictiveInventoryService.calculate_storage_life_status("URS", now - timedelta(days=50))
        assert res_urs_red["status_color"] == "RED"
        print("  ✓ URS 50-day batch: RED (Exceeds planning limit).")

        # 3. Stock Risk & Division by Zero Protection
        print("\n[TEST 3] Stock-Out Prediction & Zero-Demand Handling...")
        # Zero demand protection
        zero_risk = PredictiveInventoryService.calculate_stock_risk(5000.0, 0.0)
        assert zero_risk["days_remaining"] is None
        assert "Demand data insufficient" in zero_risk["days_remaining_str"]
        print("  ✓ Zero daily demand gracefully handled with explanation, zero-division prevented.")

        # Stock = 5,000 kg, Demand = 300 kg/day -> 16.7 days (Healthy > 14)
        risk_healthy = PredictiveInventoryService.calculate_stock_risk(5000.0, 300.0)
        assert risk_healthy["days_remaining"] == 16.7
        assert risk_healthy["status_color"] == "GREEN"
        assert risk_healthy["status_code"] == "HEALTHY"
        print("  ✓ 5,000 kg stock @ 300 kg/day: 16.7 days -> GREEN (Healthy Stock).")

        # Stock = 3,000 kg, Demand = 300 kg/day -> 10.0 days (Low <= 14)
        risk_low = PredictiveInventoryService.calculate_stock_risk(3000.0, 300.0)
        assert risk_low["days_remaining"] == 10.0
        assert risk_low["status_color"] == "YELLOW"
        print("  ✓ 3,000 kg stock @ 300 kg/day: 10.0 days -> YELLOW (Low Stock).")

        # Stock = 1,500 kg, Demand = 300 kg/day -> 5.0 days (Critical <= 7)
        risk_critical = PredictiveInventoryService.calculate_stock_risk(1500.0, 300.0)
        assert risk_critical["days_remaining"] == 5.0
        assert risk_critical["status_color"] == "ORANGE"
        print("  ✓ 1,500 kg stock @ 300 kg/day: 5.0 days -> ORANGE (Critical Stock).")

        # Stock = 600 kg, Demand = 300 kg/day -> 2.0 days (Stockout Risk <= 3)
        risk_risk = PredictiveInventoryService.calculate_stock_risk(600.0, 300.0)
        assert risk_risk["days_remaining"] == 2.0
        assert risk_risk["status_color"] == "RED"
        print("  ✓ 600 kg stock @ 300 kg/day: 2.0 days -> RED (Stock-Out Risk).")

        # 4. Sell First & Retain/Store Invariants
        print("\n[TEST 4] Recommendation Engine & Invariant Verification...")
        inv_summary = {
            "total_stock_kg": 5000.0,
            "grade_a_stock_kg": 3500.0,
            "urs_stock_kg": 1500.0,
            "rejected_stock_kg": 0.0
        }
        demand_data = {
            "daily_demand_kg": 200.0,
            "forecast_7d_kg": 1400.0,
            "forecast_14d_kg": 2800.0
        }
        market_data = {"trend": "Stable"}

        recs = PredictiveInventoryService.generate_recommendations(inv_summary, demand_data, market_data)
        sell = recs["sell_first"]
        retain = recs["retain"]

        assert sell["category"].startswith("URS"), f"Expected URS sell first, got {sell['category']}"
        assert sell["recommended_quantity_kg"] <= 1500.0
        assert (sell["recommended_quantity_kg"] + retain["recommended_quantity_kg"]) <= inv_summary["total_stock_kg"]
        assert len(sell["reason"]) > 10, "Sell reason must be provided"
        assert len(retain["reason"]) > 10, "Retain reason must be provided"
        print(f"  ✓ Sell First: {sell['category']} ({sell['recommended_quantity_kg']} kg)")
        print(f"  ✓ Retain: {retain['category']} ({retain['recommended_quantity_kg']} kg)")
        print(f"  ✓ Invariant Verified: Sell ({sell['recommended_quantity_kg']}) + Retain ({retain['recommended_quantity_kg']}) <= Total ({inv_summary['total_stock_kg']})")

        # 5. Quantity Update and Outbound Dispatch Protection
        print("\n[TEST 5] Physical Quantity Update & Negative Stock Prevention...")
        test_item = InventoryItem.query.first()
        if test_item:
            b_id = test_item.batch_id
            orig_balance = test_item.current_balance_kg
            # Update quantity to 1000 kg
            up_res = PredictiveInventoryService.update_batch_quantity(b_id, 1000.0, "kg")
            assert up_res["success"] is True
            assert test_item.current_balance_kg == 1000.0
            print(f"  ✓ Updated batch {b_id} physical weight to 1000 kg.")

            # Attempt dispatch exceeding stock (1500 kg)
            bad_disp = PredictiveInventoryService.record_dispatch(b_id, 1500.0, "Over-dispatch test")
            assert bad_disp["success"] is False
            assert "Cannot dispatch more than current available balance" in bad_disp["error"]
            print("  ✓ Prevented over-dispatch: Negative stock invariant successfully enforced.")

            # Valid dispatch of 200 kg
            good_disp = PredictiveInventoryService.record_dispatch(b_id, 200.0, "Valid dispatch")
            assert good_disp["success"] is True
            assert good_disp["new_balance_kg"] == 800.0
            print("  ✓ Recorded valid dispatch of 200 kg. Balance reduced to 800 kg.")

        # 6. Test Web API Endpoints using Flask Test Client
        print("\n[TEST 6] Testing Three Portal API Endpoints...")
        client = app.test_client()

        # Farmer Insights API
        farmer_user = User.query.filter_by(role="farmer").first()
        if farmer_user:
            with client.session_transaction() as sess:
                sess["user_id"] = farmer_user.id
                sess["user_role"] = "farmer"
            
            resp = client.get("/api/farmer/predictive-insights")
            assert resp.status_code == 200
            f_data = resp.get_json()
            assert f_data["success"] is True
            assert "market_condition" in f_data
            assert "stock_summary" in f_data
            assert "batches" in f_data
            assert "actionable_insights" in f_data
            print(f"  ✓ GET /api/farmer/predictive-insights passed for farmer: {farmer_user.name}")

        # Officer Predictive Inventory API
        officer_user = User.query.filter_by(role="officer").first()
        if officer_user:
            with client.session_transaction() as sess:
                sess["user_id"] = officer_user.id
                sess["user_role"] = "officer"

            resp = client.get("/api/officer/predictive-inventory")
            assert resp.status_code == 200
            o_data = resp.get_json()
            assert o_data["success"] is True
            assert "inventory_summary" in o_data
            assert "demand_forecast" in o_data
            assert "recommendations" in o_data
            assert "category_breakdown" in o_data
            print(f"  ✓ GET /api/officer/predictive-inventory passed for officer: {officer_user.name}")

        # Government Predictive Inventory API
        gov_user = User.query.filter(User.role.in_(["government", "admin"])).first()
        if gov_user:
            with client.session_transaction() as sess:
                sess["user_id"] = gov_user.id
                sess["user_role"] = gov_user.role

            resp = client.get("/api/government/predictive-inventory")
            assert resp.status_code == 200
            g_data = resp.get_json()
            assert g_data["success"] is True
            assert "macro_summary" in g_data
            assert "center_breakdown" in g_data
            assert "chart_data" in g_data
            print(f"  ✓ GET /api/government/predictive-inventory passed for government user: {gov_user.name}")

            # Test Settings Endpoint
            settings_resp = client.get("/api/government/inventory/settings")
            assert settings_resp.status_code == 200
            st_data = settings_resp.get_json()
            assert st_data["success"] is True
            assert "thresholds" in st_data
            print("  ✓ GET /api/government/inventory/settings passed.")

        # Test Page Rendering
        print("\n[TEST 7] Testing Web Views HTML Rendering...")
        if farmer_user:
            with client.session_transaction() as sess:
                sess["user_id"] = farmer_user.id
                sess["user_role"] = "farmer"
            r_farmer_view = client.get("/farmer/predictive-insights")
            assert r_farmer_view.status_code == 200
            assert b"Market & Predictive Insights" in r_farmer_view.data
            print("  ✓ /farmer/predictive-insights view rendered with 200 OK.")

        if officer_user:
            with client.session_transaction() as sess:
                sess["user_id"] = officer_user.id
                sess["user_role"] = "officer"
            r_officer_view = client.get("/officer/predictive-inventory")
            assert r_officer_view.status_code == 200
            assert b"Predictive Inventory & Stock Decisions" in r_officer_view.data
            print("  ✓ /officer/predictive-inventory view rendered with 200 OK.")

        if gov_user:
            with client.session_transaction() as sess:
                sess["user_id"] = gov_user.id
                sess["user_role"] = gov_user.role
            r_gov_view = client.get("/government/predictive-inventory")
            assert r_gov_view.status_code == 200
            assert b"Statewide Predictive Inventory" in r_gov_view.data
            print("  ✓ /government/predictive-inventory view rendered with 200 OK.")

    print("\n" + "=" * 70)
    print("ALL PREDICTIVE INVENTORY TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
