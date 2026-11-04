import io
import csv
import os
from datetime import datetime, date, time, timedelta, timezone
from collections import defaultdict
from sqlalchemy import func, distinct, or_

from backend.database.db import db
from backend.models.evaluation import Evaluation
from backend.models.farmer import FarmerProfile
from backend.models.officer import OfficerProfile
from config import Config, BASE_DIR

# ReportLab imports for PDF exports
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, HRFlowable, KeepTogether
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


class EvaluationReportService:
    """
    Core business logic and statistical calculations for the Evaluation Reports & Analytics system.
    Strictly aggregates actual confirmed evaluation records (status == 'confirmed').
    Never fabricates, estimates, or uses placeholder evaluation counts.
    """

    @classmethod
    def parse_date_range(cls, period="this_month", start_date_str=None, end_date_str=None):
        """
        Parses report period filter into (start_dt, end_dt) and comparative (prev_start_dt, prev_end_dt).
        Supported periods:
        - today, yesterday, this_week, last_week, this_month, last_month, this_year, custom
        """
        now = datetime.now(timezone.utc)
        today = now.date()

        period_clean = (period or "this_month").lower().strip()

        if period_clean == "today":
            start_d = today
            end_d = today
            prev_start_d = today - timedelta(days=1)
            prev_end_d = today - timedelta(days=1)
            period_label = f"Today ({today.strftime('%d %b %Y')})"

        elif period_clean == "yesterday":
            start_d = today - timedelta(days=1)
            end_d = today - timedelta(days=1)
            prev_start_d = today - timedelta(days=2)
            prev_end_d = today - timedelta(days=2)
            period_label = f"Yesterday ({start_d.strftime('%d %b %Y')})"

        elif period_clean == "this_week":
            # Monday of current week
            start_d = today - timedelta(days=today.weekday())
            end_d = today
            duration = (end_d - start_d).days + 1
            prev_end_d = start_d - timedelta(days=1)
            prev_start_d = prev_end_d - timedelta(days=duration - 1)
            period_label = f"This Week ({start_d.strftime('%d %b')} – {end_d.strftime('%d %b %Y')})"

        elif period_clean == "last_week":
            current_monday = today - timedelta(days=today.weekday())
            start_d = current_monday - timedelta(days=7)
            end_d = current_monday - timedelta(days=1)
            prev_start_d = start_d - timedelta(days=7)
            prev_end_d = end_d - timedelta(days=7)
            period_label = f"Last Week ({start_d.strftime('%d %b')} – {end_d.strftime('%d %b %Y')})"

        elif period_clean == "this_month":
            start_d = today.replace(day=1)
            end_d = today
            # Previous month up to same relative day or end of prev month
            prev_month_last = start_d - timedelta(days=1)
            prev_start_d = prev_month_last.replace(day=1)
            prev_day = min(today.day, prev_month_last.day)
            prev_end_d = prev_start_d.replace(day=prev_day)
            period_label = f"This Month ({start_d.strftime('%d %b')} – {end_d.strftime('%d %b %Y')})"

        elif period_clean == "last_month":
            current_first = today.replace(day=1)
            end_d = current_first - timedelta(days=1)
            start_d = end_d.replace(day=1)
            prev_end_d = start_d - timedelta(days=1)
            prev_start_d = prev_end_d.replace(day=1)
            period_label = f"Last Month ({start_d.strftime('%B %Y')})"

        elif period_clean == "this_year":
            start_d = today.replace(month=1, day=1)
            end_d = today
            prev_start_d = start_d.replace(year=today.year - 1)
            prev_end_d = today.replace(year=today.year - 1)
            period_label = f"This Year ({today.year})"

        elif period_clean == "custom":
            try:
                if start_date_str:
                    # Support YYYY-MM-DD or DD/MM/YYYY
                    if "/" in start_date_str:
                        start_d = datetime.strptime(start_date_str, "%d/%m/%Y").date()
                    else:
                        start_d = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                else:
                    start_d = today - timedelta(days=30)
            except Exception:
                start_d = today - timedelta(days=30)

            try:
                if end_date_str:
                    if "/" in end_date_str:
                        end_d = datetime.strptime(end_date_str, "%d/%m/%Y").date()
                    else:
                        end_d = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                else:
                    end_d = today
            except Exception:
                end_d = today

            if start_d > end_d:
                start_d, end_d = end_d, start_d

            span = (end_d - start_d).days + 1
            prev_end_d = start_d - timedelta(days=1)
            prev_start_d = prev_end_d - timedelta(days=span - 1)
            period_label = f"Custom ({start_d.strftime('%d %b %Y')} – {end_d.strftime('%d %b %Y')})"

        else:
            # Default fallback: last 30 days
            start_d = today - timedelta(days=30)
            end_d = today
            prev_end_d = start_d - timedelta(days=1)
            prev_start_d = prev_end_d - timedelta(days=30)
            period_label = "Last 30 Days"

        start_dt = datetime.combine(start_d, time.min).replace(tzinfo=timezone.utc)
        end_dt = datetime.combine(end_d, time.max).replace(tzinfo=timezone.utc)
        prev_start_dt = datetime.combine(prev_start_d, time.min).replace(tzinfo=timezone.utc)
        prev_end_dt = datetime.combine(prev_end_d, time.max).replace(tzinfo=timezone.utc)

        return {
            "period": period_clean,
            "period_label": period_label,
            "start_date": start_d,
            "end_date": end_d,
            "start_dt": start_dt,
            "end_dt": end_dt,
            "prev_start_dt": prev_start_dt,
            "prev_end_dt": prev_end_dt,
            "span_days": (end_d - start_d).days + 1
        }

    @classmethod
    def _build_evaluation_query(cls, start_dt, end_dt, role="government", user=None, center=None, officer_id=None, farmer_id=None, grade=None):
        """Builds SQLAlchemy query strictly scoped to confirmed evaluations and role access."""
        query = Evaluation.query.filter(Evaluation.status == "confirmed")

        # Date Range filter
        if start_dt:
            # In SQLite, dates can be naive or timezone-aware
            query = query.filter(Evaluation.evaluation_date >= start_dt)
        if end_dt:
            query = query.filter(Evaluation.evaluation_date <= end_dt)

        # Role-based access control
        if role == "farmer":
            if user and user.farmer_profile:
                query = query.filter(Evaluation.farmer_id == user.farmer_profile.id)
            elif farmer_id:
                query = query.filter(Evaluation.farmer_id == farmer_id)
            else:
                query = query.filter(Evaluation.id == -1)  # Empty fallback
        elif role == "officer":
            if user and user.officer_profile:
                query = query.filter(Evaluation.officer_id == user.officer_profile.id)
            elif officer_id:
                query = query.filter(Evaluation.officer_id == officer_id)
        elif role in ("government", "admin"):
            if center and center != "All":
                query = query.join(OfficerProfile).filter(OfficerProfile.procurement_center.ilike(f"%{center}%"))
            if officer_id and str(officer_id) != "All":
                query = query.filter(Evaluation.officer_id == int(officer_id))
            if farmer_id and str(farmer_id) != "All":
                query = query.filter(Evaluation.farmer_id == int(farmer_id))

        if grade and grade != "All":
            if grade == "Grade A":
                query = query.filter(Evaluation.overall_result.ilike("%Grade A%"))
            elif grade == "URS":
                query = query.filter(Evaluation.overall_result.ilike("%URS%"))
            elif grade == "Rejected":
                query = query.filter(Evaluation.overall_result.ilike("%Rejection%"))

        return query

    @classmethod
    def get_analytics(cls, period="this_month", start_date=None, end_date=None,
                      role="government", user=None, center=None, officer_id=None,
                      farmer_id=None, grade=None, trend_weeks=4, trend_months=6):
        """
        Computes all evaluation reports and analytics dynamically from stored records.
        Never generates fake data or demo numbers.
        """
        dr = cls.parse_date_range(period, start_date, end_date)
        start_dt = dr["start_dt"]
        end_dt = dr["end_dt"]
        prev_start_dt = dr["prev_start_dt"]
        prev_end_dt = dr["prev_end_dt"]

        # 1. Current Period Evaluations
        query = cls._build_evaluation_query(
            start_dt, end_dt, role=role, user=user, center=center,
            officer_id=officer_id, farmer_id=farmer_id, grade=grade
        )
        evaluations = query.order_by(Evaluation.evaluation_date.desc()).all()

        # 2. Previous Period Evaluations (for Period Comparison)
        prev_query = cls._build_evaluation_query(
            prev_start_dt, prev_end_dt, role=role, user=user, center=center,
            officer_id=officer_id, farmer_id=farmer_id, grade=grade
        )
        prev_evaluations = prev_query.all()

        # Aggregate Metrics for Current Period
        total_evals = len(evaluations)
        total_onions = sum(e.total_onions for e in evaluations)

        # Distinct counts
        unique_farmer_ids = set(e.farmer_id for e in evaluations if e.farmer_id)
        unique_officer_ids = set(e.officer_id for e in evaluations if e.officer_id)
        total_farmers = len(unique_farmer_ids)
        total_officers = len(unique_officer_ids)

        # Grade counts
        grade_a_count = sum(e.grade_a_count for e in evaluations)
        urs_count = sum(e.urs_count for e in evaluations)
        rejected_count = sum(e.rejected_count for e in evaluations)

        # Quality class counts
        healthy_count = sum(e.healthy_count for e in evaluations)
        damaged_count = sum(e.damaged_count for e in evaluations)
        rotten_count = sum(e.rotten_count for e in evaluations)
        sprouted_count = sum(e.sprouted_count for e in evaluations)
        uncertain_count = sum((getattr(e, "uncertain_count", 0) or 0) for e in evaluations)

        # Dynamic percentages
        def _calc_pct(part, whole):
            return round((part / whole * 100.0) if whole > 0 else 0.0, 2)

        grade_a_pct = _calc_pct(grade_a_count, total_onions)
        urs_pct = _calc_pct(urs_count, total_onions)
        rejected_pct = _calc_pct(rejected_count, total_onions)

        healthy_pct = _calc_pct(healthy_count, total_onions)
        damaged_pct = _calc_pct(damaged_count, total_onions)
        rotten_pct = _calc_pct(rotten_count, total_onions)
        sprouted_pct = _calc_pct(sprouted_count, total_onions)
        uncertain_pct = _calc_pct(uncertain_count, total_onions)

        # Day-by-day mapping for active days & daily trends
        daily_onion_map = defaultdict(int)
        daily_eval_map = defaultdict(int)

        for e in evaluations:
            if e.evaluation_date:
                d_key = e.evaluation_date.strftime("%Y-%m-%d")
                daily_onion_map[d_key] += e.total_onions
                daily_eval_map[d_key] += 1

        active_days_count = len(daily_onion_map)
        avg_onions_per_eval = round((total_onions / total_evals) if total_evals > 0 else 0.0, 2)
        avg_onions_per_day = round((total_onions / active_days_count) if active_days_count > 0 else 0.0, 2)

        highest_day = {"date": "N/A", "onions": 0}
        lowest_day = {"date": "N/A", "onions": 0}

        if daily_onion_map:
            sorted_days = sorted(daily_onion_map.items(), key=lambda x: x[1], reverse=True)
            highest_day = {"date": datetime.strptime(sorted_days[0][0], "%Y-%m-%d").strftime("%d %b %Y"), "onions": sorted_days[0][1]}
            lowest_day = {"date": datetime.strptime(sorted_days[-1][0], "%Y-%m-%d").strftime("%d %b %Y"), "onions": sorted_days[-1][1]}

        # 3. Build Daily Evaluation Trend for Selected Period
        # Enumerate each calendar day in the range. If no evals occurred, output 0 (Never fake counts).
        daily_labels = []
        daily_onion_counts = []
        daily_eval_counts = []

        curr_d = dr["start_date"]
        end_d = dr["end_date"]
        # Limit daily sequence resolution to 60 days to prevent chart clutter on full-year view
        step_days = 1
        if dr["span_days"] > 62:
            step_days = max(1, dr["span_days"] // 30)

        while curr_d <= end_d:
            d_str = curr_d.strftime("%Y-%m-%d")
            display_label = curr_d.strftime("%d %b")
            daily_labels.append(display_label)
            daily_onion_counts.append(daily_onion_map.get(d_str, 0))
            daily_eval_counts.append(daily_eval_map.get(d_str, 0))
            curr_d += timedelta(days=step_days)

        # 4. Weekly Comparison Trend (Last N Weeks)
        weeks_count = int(trend_weeks) if trend_weeks in (4, 8, 12, "4", "8", "12") else 4
        weekly_trend_labels = []
        weekly_trend_onions = []
        weekly_trend_evals = []

        now_d = datetime.now(timezone.utc).date()
        for w in range(weeks_count - 1, -1, -1):
            w_start = now_d - timedelta(days=now_d.weekday() + (w * 7))
            w_end = w_start + timedelta(days=6)
            w_start_dt = datetime.combine(w_start, time.min).replace(tzinfo=timezone.utc)
            w_end_dt = datetime.combine(w_end, time.max).replace(tzinfo=timezone.utc)

            w_query = cls._build_evaluation_query(w_start_dt, w_end_dt, role=role, user=user)
            w_evals = w_query.all()
            w_onions = sum(x.total_onions for x in w_evals)

            label = f"W-{weeks_count - w} ({w_start.strftime('%d %b')})"
            weekly_trend_labels.append(label)
            weekly_trend_onions.append(w_onions)
            weekly_trend_evals.append(len(w_evals))

        # 5. Monthly Comparison Trend (Last N Months)
        months_count = int(trend_months) if trend_months in (6, 12, "6", "12") else 6
        monthly_trend_labels = []
        monthly_trend_onions = []
        monthly_trend_evals = []

        for m in range(months_count - 1, -1, -1):
            # Calculate target year and month
            target_year = now_d.year
            target_month = now_d.month - m
            while target_month <= 0:
                target_month += 12
                target_year -= 1

            m_start = date(target_year, target_month, 1)
            if target_month == 12:
                m_end = date(target_year + 1, 1, 1) - timedelta(days=1)
            else:
                m_end = date(target_year, target_month + 1, 1) - timedelta(days=1)

            m_start_dt = datetime.combine(m_start, time.min).replace(tzinfo=timezone.utc)
            m_end_dt = datetime.combine(m_end, time.max).replace(tzinfo=timezone.utc)

            m_query = cls._build_evaluation_query(m_start_dt, m_end_dt, role=role, user=user)
            m_evals = m_query.all()
            m_onions = sum(x.total_onions for x in m_evals)

            label = m_start.strftime("%b %Y")
            monthly_trend_labels.append(label)
            monthly_trend_onions.append(m_onions)
            monthly_trend_evals.append(len(m_evals))

        # 6. Period Comparison (Current vs Previous)
        prev_total_onions = sum(e.total_onions for e in prev_evaluations)
        prev_total_evals = len(prev_evaluations)
        prev_farmers = len(set(e.farmer_id for e in prev_evaluations if e.farmer_id))
        prev_officers = len(set(e.officer_id for e in prev_evaluations if e.officer_id))
        prev_grade_a = sum(e.grade_a_count for e in prev_evaluations)
        prev_urs = sum(e.urs_count for e in prev_evaluations)
        prev_rejected = sum(e.rejected_count for e in prev_evaluations)

        def _calc_change(cur, prev):
            if prev == 0:
                return {
                    "current": cur,
                    "previous": prev,
                    "diff": cur,
                    "pct_change_str": "Comparison unavailable" if cur == 0 else "+100%",
                    "pct_change": None if cur == 0 else 100.0,
                    "direction": "up" if cur > 0 else "neutral"
                }
            diff = cur - prev
            pct = round((diff / prev) * 100.0, 2)
            direction = "up" if diff > 0 else ("down" if diff < 0 else "neutral")
            pct_str = f"+{pct}%" if diff > 0 else f"{pct}%"
            return {
                "current": cur,
                "previous": prev,
                "diff": diff,
                "pct_change_str": pct_str,
                "pct_change": pct,
                "direction": direction
            }

        comparison = {
            "onions": _calc_change(total_onions, prev_total_onions),
            "evaluations": _calc_change(total_evals, prev_total_evals),
            "farmers": _calc_change(total_farmers, prev_farmers),
            "officers": _calc_change(total_officers, prev_officers),
            "grade_a": _calc_change(grade_a_count, prev_grade_a),
            "urs": _calc_change(urs_count, prev_urs),
            "rejected": _calc_change(rejected_count, prev_rejected)
        }

        # 7. Procurement Center Activity Breakdown
        centers_map = {}
        for e in evaluations:
            officer = e.officer
            center_name = officer.procurement_center if officer else "Lasalgaon APMC Mandi"
            if center_name not in centers_map:
                centers_map[center_name] = {
                    "center_name": center_name,
                    "location": officer.location if officer else "Nashik",
                    "total_evaluations": 0,
                    "total_onions": 0,
                    "grade_a_count": 0,
                    "urs_count": 0,
                    "rejected_count": 0,
                    "farmer_ids": set(),
                    "officer_ids": set()
                }

            c = centers_map[center_name]
            c["total_evaluations"] += 1
            c["total_onions"] += e.total_onions
            c["grade_a_count"] += e.grade_a_count
            c["urs_count"] += e.urs_count
            c["rejected_count"] += e.rejected_count
            if e.farmer_id:
                c["farmer_ids"].add(e.farmer_id)
            if e.officer_id:
                c["officer_ids"].add(e.officer_id)

        center_rows = []
        for cname, cdata in sorted(centers_map.items(), key=lambda x: x[1]["total_onions"], reverse=True):
            tot_o = cdata["total_onions"]
            center_rows.append({
                "center_name": cname,
                "location": cdata["location"],
                "total_evaluations": cdata["total_evaluations"],
                "total_onions": tot_o,
                "grade_a_count": cdata["grade_a_count"],
                "grade_a_pct": _calc_pct(cdata["grade_a_count"], tot_o),
                "urs_count": cdata["urs_count"],
                "urs_pct": _calc_pct(cdata["urs_count"], tot_o),
                "rejected_count": cdata["rejected_count"],
                "rejected_pct": _calc_pct(cdata["rejected_count"], tot_o),
                "farmers_evaluated": len(cdata["farmer_ids"]),
                "officers_active": len(cdata["officer_ids"])
            })

        # 8. Officer Evaluation Activity
        officer_map = {}
        for e in evaluations:
            off = e.officer
            o_id = off.officer_id if off else f"OFF-{e.officer_id}"
            if o_id not in officer_map:
                officer_map[o_id] = {
                    "officer_id": o_id,
                    "officer_name": off.user.name if (off and off.user) else "Procurement Officer",
                    "procurement_center": off.procurement_center if off else "APMC Mandi",
                    "evaluation_sessions": 0,
                    "total_onions": 0,
                    "grade_a_count": 0,
                    "urs_count": 0,
                    "rejected_count": 0,
                    "farmer_ids": set()
                }

            o = officer_map[o_id]
            o["evaluation_sessions"] += 1
            o["total_onions"] += e.total_onions
            o["grade_a_count"] += e.grade_a_count
            o["urs_count"] += e.urs_count
            o["rejected_count"] += e.rejected_count
            if e.farmer_id:
                o["farmer_ids"].add(e.farmer_id)

        officer_rows = []
        for o_id, odata in sorted(officer_map.items(), key=lambda x: x[1]["total_onions"], reverse=True):
            tot_o = odata["total_onions"]
            officer_rows.append({
                "officer_id": o_id,
                "officer_name": odata["officer_name"],
                "procurement_center": odata["procurement_center"],
                "evaluation_sessions": odata["evaluation_sessions"],
                "total_onions": tot_o,
                "farmers_evaluated": len(odata["farmer_ids"]),
                "grade_a_count": odata["grade_a_count"],
                "grade_a_pct": _calc_pct(odata["grade_a_count"], tot_o),
                "urs_count": odata["urs_count"],
                "urs_pct": _calc_pct(odata["urs_count"], tot_o),
                "rejected_count": odata["rejected_count"],
                "rejected_pct": _calc_pct(odata["rejected_count"], tot_o)
            })

        # 9. Farmer Evaluation History
        farmer_map = {}
        for e in evaluations:
            f = e.farmer
            f_code = f.farmer_id if f else f"FARM-{e.farmer_id}"
            if f_code not in farmer_map:
                farmer_map[f_code] = {
                    "farmer_id": f_code,
                    "farmer_name": f.user.name if (f and f.user) else "Farmer",
                    "mobile": f.user.phone if (f and f.user) else "--",
                    "district": f.district if f else "--",
                    "village": f.village if f else "--",
                    "total_evaluations": 0,
                    "total_onions": 0,
                    "grade_a_count": 0,
                    "urs_count": 0,
                    "rejected_count": 0,
                    "last_eval_date": e.evaluation_date
                }

            fm = farmer_map[f_code]
            fm["total_evaluations"] += 1
            fm["total_onions"] += e.total_onions
            fm["grade_a_count"] += e.grade_a_count
            fm["urs_count"] += e.urs_count
            fm["rejected_count"] += e.rejected_count
            if e.evaluation_date and (fm["last_eval_date"] is None or e.evaluation_date > fm["last_eval_date"]):
                fm["last_eval_date"] = e.evaluation_date

        farmer_rows = []
        for f_code, fdata in sorted(farmer_map.items(), key=lambda x: x[1]["total_onions"], reverse=True):
            tot_o = fdata["total_onions"]
            farmer_rows.append({
                "farmer_id": f_code,
                "farmer_name": fdata["farmer_name"],
                "mobile": fdata["mobile"],
                "district": fdata["district"],
                "village": fdata["village"],
                "total_evaluations": fdata["total_evaluations"],
                "total_onions": tot_o,
                "grade_a_count": fdata["grade_a_count"],
                "grade_a_pct": _calc_pct(fdata["grade_a_count"], tot_o),
                "urs_count": fdata["urs_count"],
                "urs_pct": _calc_pct(fdata["urs_count"], tot_o),
                "rejected_count": fdata["rejected_count"],
                "rejected_pct": _calc_pct(fdata["rejected_count"], tot_o),
                "last_evaluation_date": fdata["last_eval_date"].strftime("%d/%m/%Y") if fdata["last_eval_date"] else "N/A"
            })

        # 10. Evaluation Records Table Rows
        records_rows = []
        for e in evaluations:
            farmer_obj = e.farmer
            officer_obj = e.officer
            records_rows.append({
                "id": e.id,
                "report_id": e.report_id or f"ONR-{e.id}",
                "evaluation_date": e.evaluation_date.strftime("%d/%m/%Y %H:%M") if e.evaluation_date else "N/A",
                "date_only": e.evaluation_date.strftime("%d/%m/%Y") if e.evaluation_date else "N/A",
                "farmer_id": farmer_obj.farmer_id if farmer_obj else f"FARM-{e.farmer_id}",
                "farmer_name": farmer_obj.user.name if (farmer_obj and farmer_obj.user) else "Farmer",
                "farmer_mobile": farmer_obj.user.phone if (farmer_obj and farmer_obj.user) else "",
                "officer_id": officer_obj.officer_id if officer_obj else f"OFF-{e.officer_id}",
                "officer_name": officer_obj.user.name if (officer_obj and officer_obj.user) else "Officer",
                "procurement_center": officer_obj.procurement_center if officer_obj else "APMC Mandi",
                "total_onions": e.total_onions,
                "healthy_count": e.healthy_count,
                "damaged_count": e.damaged_count,
                "rotten_count": e.rotten_count,
                "sprouted_count": e.sprouted_count,
                "grade_a_count": e.grade_a_count,
                "urs_count": e.urs_count,
                "rejected_count": e.rejected_count,
                "overall_result": e.overall_result or "Standard",
                "mandi_modal_price": e.mandi_modal_price,
                "estimated_price_per_quintal": e.estimated_price_per_quintal,
                "quantity_quintals": e.quantity_quintals or 0.0,
                "total_payout": e.total_payout or 0.0,
                "status": e.status,
                "pdf_url": f"/reports/download/Onion_Report_{e.report_id or e.id}.pdf"
            })

        return {
            "success": True,
            "period": dr["period"],
            "period_label": dr["period_label"],
            "start_date": dr["start_date"].strftime("%d/%m/%Y"),
            "end_date": dr["end_date"].strftime("%d/%m/%Y"),
            "summary_cards": {
                "total_onions_evaluated": total_onions,
                "total_evaluations": total_evals,
                "total_farmers_evaluated": total_farmers,
                "total_officers_active": total_officers,
                "grade_a_count": grade_a_count,
                "grade_a_pct": grade_a_pct,
                "urs_count": urs_count,
                "urs_pct": urs_pct,
                "rejected_count": rejected_count,
                "rejected_pct": rejected_pct,
                "active_evaluation_days": active_days_count,
                "avg_onions_per_evaluation": avg_onions_per_eval,
                "avg_onions_per_day": avg_onions_per_day,
                "highest_day": highest_day,
                "lowest_day": lowest_day
            },
            "quality_distribution": {
                "healthy": {"count": healthy_count, "pct": healthy_pct},
                "damaged": {"count": damaged_count, "pct": damaged_pct},
                "rotten": {"count": rotten_count, "pct": rotten_pct},
                "sprouted": {"count": sprouted_count, "pct": sprouted_pct},
                "uncertain": {"count": uncertain_count, "pct": uncertain_pct},
                "grade_a": {"count": grade_a_count, "pct": grade_a_pct},
                "urs": {"count": urs_count, "pct": urs_pct},
                "rejected": {"count": rejected_count, "pct": rejected_pct}
            },
            "daily_trend": {
                "labels": daily_labels,
                "onions": daily_onion_counts,
                "evaluations": daily_eval_counts
            },
            "weekly_trend": {
                "labels": weekly_trend_labels,
                "onions": weekly_trend_onions,
                "evaluations": weekly_trend_evals
            },
            "monthly_trend": {
                "labels": monthly_trend_labels,
                "onions": monthly_trend_onions,
                "evaluations": monthly_trend_evals
            },
            "period_comparison": comparison,
            "center_activity": center_rows,
            "officer_activity": officer_rows,
            "farmer_history": farmer_rows,
            "records": records_rows
        }

    # =========================================================================
    # EXPORT ENGINES: CSV, EXCEL, AND OFFICIAL REPORTLAB PDFS
    # =========================================================================
    @classmethod
    def export_csv(cls, period="this_month", start_date=None, end_date=None, role="government", user=None):
        """Generates CSV string containing report summary and evaluation records."""
        data = cls.get_analytics(period=period, start_date=start_date, end_date=end_date, role=role, user=user)
        output = io.StringIO()
        writer = csv.writer(output)

        # Header Metadata
        writer.writerow(["ONIONGRADE AI - EVALUATION REPORT & ANALYTICS"])
        writer.writerow(["Report Period", data["period_label"]])
        writer.writerow(["Generated At", datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")])
        writer.writerow([])

        # Summary Metrics
        sum_c = data["summary_cards"]
        writer.writerow(["EXECUTIVE SUMMARY"])
        writer.writerow(["Total Onions Evaluated", sum_c["total_onions_evaluated"]])
        writer.writerow(["Total Evaluations Conducted", sum_c["total_evaluations"]])
        writer.writerow(["Farmers Evaluated", sum_c["total_farmers_evaluated"]])
        writer.writerow(["Officers Active", sum_c["total_officers_active"]])
        writer.writerow(["Grade A Onions", f"{sum_c['grade_a_count']} ({sum_c['grade_a_pct']}%)"])
        writer.writerow(["URS Standard Onions", f"{sum_c['urs_count']} ({sum_c['urs_pct']}%)"])
        writer.writerow(["Rejected Onions", f"{sum_c['rejected_count']} ({sum_c['rejected_pct']}%)"])
        writer.writerow(["Active Evaluation Days", sum_c["active_evaluation_days"]])
        writer.writerow(["Average Onions / Evaluation", sum_c["avg_onions_per_evaluation"]])
        writer.writerow([])

        # Quality Distribution
        qd = data["quality_distribution"]
        writer.writerow(["QUALITY DEFECT DISTRIBUTION"])
        writer.writerow(["Class", "Count", "Percentage"])
        writer.writerow(["Healthy", qd["healthy"]["count"], f"{qd['healthy']['pct']}%"])
        writer.writerow(["Damaged", qd["damaged"]["count"], f"{qd['damaged']['pct']}%"])
        writer.writerow(["Rotten", qd["rotten"]["count"], f"{qd['rotten']['pct']}%"])
        writer.writerow(["Sprouted", qd["sprouted"]["count"], f"{qd['sprouted']['pct']}%"])
        writer.writerow([])

        # Center Breakdown (if authorized)
        if role in ("government", "admin") and data["center_activity"]:
            writer.writerow(["PROCUREMENT CENTER EVALUATION ACTIVITY"])
            writer.writerow(["Center", "Location", "Evaluations", "Total Onions", "Grade A", "URS", "Rejected", "Farmers"])
            for c in data["center_activity"]:
                writer.writerow([
                    c["center_name"], c["location"], c["total_evaluations"],
                    c["total_onions"], c["grade_a_count"], c["urs_count"],
                    c["rejected_count"], c["farmers_evaluated"]
                ])
            writer.writerow([])

        # Detailed Record Rows
        writer.writerow(["DETAILED CONFIRMED EVALUATION RECORDS"])
        writer.writerow([
            "Report ID", "Date", "Farmer ID", "Farmer Name", "Officer ID", "Officer Name",
            "Procurement Center", "Total Onions", "Grade A", "URS", "Rejected",
            "Healthy", "Damaged", "Rotten", "Sprouted", "Overall Result", "Total Payout (Rs)"
        ])
        for r in data["records"]:
            writer.writerow([
                r["report_id"], r["evaluation_date"], r["farmer_id"], r["farmer_name"],
                r["officer_id"], r["officer_name"], r["procurement_center"],
                r["total_onions"], r["grade_a_count"], r["urs_count"], r["rejected_count"],
                r["healthy_count"], r["damaged_count"], r["rotten_count"], r["sprouted_count"],
                r["overall_result"], r["total_payout"]
            ])

        return output.getvalue()

    @classmethod
    def export_excel(cls, period="this_month", start_date=None, end_date=None, role="government", user=None):
        """Generates UTF-8 encoded Excel-compatible CSV stream."""
        csv_content = cls.export_csv(period=period, start_date=start_date, end_date=end_date, role=role, user=user)
        # Prepend UTF-8 BOM so Excel opens Hindi/Marathi characters and commas seamlessly
        return b"\xef\xbb\xbf" + csv_content.encode("utf-8")

    @classmethod
    def generate_pdf_report(cls, report_type="weekly", period="this_week", role="government", user=None):
        """
        Generates an official Weekly or Monthly Evaluation Report PDF using ReportLab.
        Conforms strictly to project branding, styling, and required document sections.
        """
        data = cls.get_analytics(period=period, role=role, user=user)
        sum_c = data["summary_cards"]
        qd = data["quality_distribution"]

        pdf_dir = getattr(Config, "PDF_REPORT_FOLDER", os.path.join(str(BASE_DIR), "reports", "pdf"))
        os.makedirs(pdf_dir, exist_ok=True)
        report_code = f"EVAL-{report_type.upper()}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        filename = f"OnionGrade_{report_type.capitalize()}_Report_{report_code}.pdf"
        filepath = os.path.join(pdf_dir, filename)

        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#0f5132")
        )
        subtitle_style = ParagraphStyle(
            "DocSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#64748b")
        )
        section_style = ParagraphStyle(
            "SectionHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#0a3622")
        )
        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#1e293b")
        )
        bold_cell = ParagraphStyle(
            "BoldCell",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#0f172a")
        )

        story = []

        # Header Title
        report_title = f"ONIONGRADE AI — {report_type.upper()} EVALUATION REPORT"
        story.append(Paragraph(report_title, title_style))
        story.append(Paragraph(f"REPORTING PERIOD: <b>{data['period_label']}</b> • REPORT ID: <b>{report_code}</b>", subtitle_style))
        story.append(Spacer(1, 8))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#0f5132"), spaceAfter=12))

        # Executive Summary Box
        story.append(Paragraph("1. EXECUTIVE EVALUATION SUMMARY", section_style))
        story.append(Spacer(1, 6))

        summary_table_data = [
            [
                Paragraph("<b>Total Onions Evaluated:</b>", body_style),
                Paragraph(f"<b>{sum_c['total_onions_evaluated']:,}</b>", bold_cell),
                Paragraph("<b>Evaluation Sessions:</b>", body_style),
                Paragraph(f"<b>{sum_c['total_evaluations']:,}</b>", bold_cell)
            ],
            [
                Paragraph("<b>Farmers Evaluated:</b>", body_style),
                Paragraph(f"<b>{sum_c['total_farmers_evaluated']}</b>", bold_cell),
                Paragraph("<b>Officers Active:</b>", body_style),
                Paragraph(f"<b>{sum_c['total_officers_active']}</b>", bold_cell)
            ],
            [
                Paragraph("<b>Grade A Onions:</b>", body_style),
                Paragraph(f"<font color='#16a34a'><b>{sum_c['grade_a_count']:,} ({sum_c['grade_a_pct']}%)</b></font>", bold_cell),
                Paragraph("<b>URS Onions:</b>", body_style),
                Paragraph(f"<font color='#d97706'><b>{sum_c['urs_count']:,} ({sum_c['urs_pct']}%)</b></font>", bold_cell)
            ],
            [
                Paragraph("<b>Rejected Bulbs:</b>", body_style),
                Paragraph(f"<font color='#dc2626'><b>{sum_c['rejected_count']:,} ({sum_c['rejected_pct']}%)</b></font>", bold_cell),
                Paragraph("<b>Active Evaluation Days:</b>", body_style),
                Paragraph(f"<b>{sum_c['active_evaluation_days']} days</b>", bold_cell)
            ]
        ]

        if report_type.lower() == "monthly":
            summary_table_data.append([
                Paragraph("<b>Avg Onions / Day:</b>", body_style),
                Paragraph(f"<b>{sum_c['avg_onions_per_day']} kg/day</b>", bold_cell),
                Paragraph("<b>Avg Onions / Session:</b>", body_style),
                Paragraph(f"<b>{sum_c['avg_onions_per_evaluation']}</b>", bold_cell)
            ])

        sum_table = Table(summary_table_data, colWidths=[130, 130, 130, 130])
        sum_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(sum_table)
        story.append(Spacer(1, 14))

        # Quality & Defect Distribution Table
        story.append(Paragraph("2. QUALITY & GRADING DISTRIBUTION", section_style))
        story.append(Spacer(1, 6))

        quality_rows = [
            [Paragraph("<b>Category / Defect</b>", bold_cell), Paragraph("<b>Count (Bulbs)</b>", bold_cell), Paragraph("<b>Share (%)</b>", bold_cell), Paragraph("<b>Procurement Classification</b>", bold_cell)],
            [Paragraph("Grade A (Healthy)", body_style), Paragraph(str(sum_c["grade_a_count"]), body_style), Paragraph(f"{sum_c['grade_a_pct']}%", body_style), Paragraph("<font color='#16a34a'><b>Grade A Premium</b></font>", body_style)],
            [Paragraph("Damaged (URS)", body_style), Paragraph(str(qd["damaged"]["count"]), body_style), Paragraph(f"{qd['damaged']['pct']}%", body_style), Paragraph("<font color='#d97706'><b>URS Standard</b></font>", body_style)],
            [Paragraph("Rotten (Defect)", body_style), Paragraph(str(qd["rotten"]["count"]), body_style), Paragraph(f"{qd['rotten']['pct']}%", body_style), Paragraph("<font color='#dc2626'><b>Rejected</b></font>", body_style)],
            [Paragraph("Sprouted (Defect)", body_style), Paragraph(str(qd["sprouted"]["count"]), body_style), Paragraph(f"{qd['sprouted']['pct']}%", body_style), Paragraph("<font color='#dc2626'><b>Rejected</b></font>", body_style)]
        ]

        q_table = Table(quality_rows, colWidths=[150, 110, 110, 150])
        q_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ecfdf5")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#bbf7d0")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(q_table)
        story.append(Spacer(1, 14))

        # Procurement Center Activity Summary
        if data["center_activity"]:
            story.append(Paragraph("3. PROCUREMENT CENTER EVALUATION ACTIVITY", section_style))
            story.append(Spacer(1, 6))

            center_header = [Paragraph("<b>Center</b>", bold_cell), Paragraph("<b>Sessions</b>", bold_cell), Paragraph("<b>Total Onions</b>", bold_cell), Paragraph("<b>Grade A</b>", bold_cell), Paragraph("<b>URS</b>", bold_cell), Paragraph("<b>Farmers</b>", bold_cell)]
            center_rows = [center_header]
            for c in data["center_activity"][:6]:
                center_rows.append([
                    Paragraph(c["center_name"], body_style),
                    Paragraph(str(c["total_evaluations"]), body_style),
                    Paragraph(f"<b>{c['total_onions']:,}</b>", body_style),
                    Paragraph(f"{c['grade_a_count']:,}", body_style),
                    Paragraph(f"{c['urs_count']:,}", body_style),
                    Paragraph(str(c["farmers_evaluated"]), body_style)
                ])

            c_table = Table(center_rows, colWidths=[170, 70, 90, 65, 65, 60])
            c_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(c_table)
            story.append(Spacer(1, 14))

        # Monthly Report Extra: Period Comparison
        if report_type.lower() == "monthly":
            comp = data["period_comparison"]
            story.append(Paragraph("4. PERIOD COMPARISON (CURRENT VS PREVIOUS PERIOD)", section_style))
            story.append(Spacer(1, 6))

            comp_header = [Paragraph("<b>Metric</b>", bold_cell), Paragraph("<b>Current Period</b>", bold_cell), Paragraph("<b>Previous Period</b>", bold_cell), Paragraph("<b>Change %</b>", bold_cell)]
            comp_rows = [
                comp_header,
                [Paragraph("Total Onions Evaluated", body_style), Paragraph(str(comp["onions"]["current"]), body_style), Paragraph(str(comp["onions"]["previous"]), body_style), Paragraph(comp["onions"]["pct_change_str"], bold_cell)],
                [Paragraph("Evaluation Sessions", body_style), Paragraph(str(comp["evaluations"]["current"]), body_style), Paragraph(str(comp["evaluations"]["previous"]), body_style), Paragraph(comp["evaluations"]["pct_change_str"], bold_cell)],
                [Paragraph("Farmers Evaluated", body_style), Paragraph(str(comp["farmers"]["current"]), body_style), Paragraph(str(comp["farmers"]["previous"]), body_style), Paragraph(comp["farmers"]["pct_change_str"], bold_cell)],
                [Paragraph("Grade A Onions", body_style), Paragraph(str(comp["grade_a"]["current"]), body_style), Paragraph(str(comp["grade_a"]["previous"]), body_style), Paragraph(comp["grade_a"]["pct_change_str"], bold_cell)]
            ]
            comp_table = Table(comp_rows, colWidths=[180, 110, 110, 120])
            comp_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eff6ff")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#bfdbfe")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(comp_table)
            story.append(Spacer(1, 14))

        # Footer Notice
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=8))
        story.append(Paragraph(
            f"Official System Generated Report • Generated on: {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M:%S UTC')} • "
            f"All values are dynamically aggregated from confirmed digital evaluation records.",
            ParagraphStyle("Footer", fontName="Helvetica", fontSize=7.5, textColor=colors.HexColor("#64748b"))
        ))

        doc.build(story)
        file_size = os.path.getsize(filepath)
        return filename, filepath, file_size
