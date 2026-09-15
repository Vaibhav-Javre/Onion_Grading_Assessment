from flask import Blueprint, jsonify, request

from backend.services.market_price_service import MarketPriceService
from backend.services.price_engine import PriceEngine

market_bp = Blueprint("market_bp", __name__, url_prefix="/api/market")

@market_bp.route("/lasalgaon-reference", methods=["GET"])
def get_lasalgaon_reference():
    """
    Returns latest Lasalgaon Mandi modal price, price date, and source from Government data.gov.in API.
    Does not expose API key. Does not simulate/fake prices if API fails.
    """
    try:
        ref_data = PriceEngine.get_lasalgaon_reference_price()
        return jsonify({
            "success": True,
            "data": ref_data
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to retrieve Lasalgaon reference price: {e!s}"
        }), 500

@market_bp.route("/prices", methods=["GET"])
def get_prices():
    district = request.args.get("district", "").strip()
    market_name = request.args.get("market", "").strip()

    try:
        prices = MarketPriceService.get_market_prices(district=district, market_name=market_name)
        return jsonify({
            "success": True,
            "total": len(prices),
            "prices": prices
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Market price service is temporarily unavailable.",
            "details": str(e)
        }), 503

@market_bp.route("/districts", methods=["GET"])
def get_districts():
    try:
        districts = MarketPriceService.get_districts()
        return jsonify({
            "success": True,
            "districts": districts
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@market_bp.route("/trends", methods=["GET"])
def get_trends():
    try:
        trends = MarketPriceService.get_price_trends()
        return jsonify({
            "success": True,
            "trends": trends
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

