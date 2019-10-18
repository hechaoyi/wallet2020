from wallet.core import db


class M1Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True, nullable=False)
    value = db.Column(db.Float, nullable=False)
    gain = db.Column(db.Float, nullable=False)
    rate = db.Column(db.Float, nullable=False)
    start_value = db.Column(db.Float, nullable=False)
    net_cash_flow = db.Column(db.Float, nullable=False)
    capital_gain = db.Column(db.Float, nullable=False)
    dividend_gain = db.Column(db.Float, nullable=False)
    updated = db.Column(db.DateTime, nullable=False, default=db.utcnow, onupdate=db.utcnow)
