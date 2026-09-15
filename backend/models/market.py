from datetime import datetime, timezone

from backend.database.db import db


class MarketPrice(db.Model):
    __tablename__ = "market_prices"

    id = db.Column(db.Integer, primary_key=True)
    market_name = db.Column(db.String(120), nullable=False, index=True) # e.g. Lasalgaon Mandi
    district = db.Column(db.String(80), nullable=False, index=True)    # e.g. Nashik
    state = db.Column(db.String(80), nullable=False, default="Maharashtra")
    commodity = db.Column(db.String(50), nullable=False, default="Onion")
    variety = db.Column(db.String(50), nullable=False, default="Red / Garwa")
    min_price = db.Column(db.Float, nullable=False)   # Rs / Quintal
    max_price = db.Column(db.Float, nullable=False)   # Rs / Quintal
    modal_price = db.Column(db.Float, nullable=False) # Rs / Quintal (most frequent trading price)
    unit = db.Column(db.String(20), default="₹/Quintal")
    arrival_tons = db.Column(db.Float, default=0.0)
    last_updated = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        # Calculate human-readable updated time
        now = datetime.now(timezone.utc)
        diff = now - (self.last_updated.replace(tzinfo=timezone.utc) if self.last_updated.tzinfo is None else self.last_updated)
        minutes_ago = max(1, int(diff.total_seconds() / 60))
        time_str = f"Updated {minutes_ago}m ago" if minutes_ago < 60 else f"Updated {int(minutes_ago/60)}h ago"

        return {
            "id": self.id,
            "market_name": self.market_name,
            "district": self.district,
            "state": self.state,
            "commodity": self.commodity,
            "variety": self.variety,
            "min_price": round(self.min_price, 2),
            "max_price": round(self.max_price, 2),
            "modal_price": round(self.modal_price, 2),
            "unit": self.unit,
            "arrival_tons": round(self.arrival_tons, 1),
            "last_updated": self.last_updated.strftime("%d/%m/%Y %I:%M %p"),
            "time_ago": time_str
        }

    def __repr__(self):
        return f"<MarketPrice {self.market_name}: ₹{self.modal_price}>"
