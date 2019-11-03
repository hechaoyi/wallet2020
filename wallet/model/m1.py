from collections import namedtuple
from datetime import datetime

from flask import current_app
from pytz import timezone

from wallet.core import db
from wallet.util.m1 import request_m1finance

tz = timezone('US/Pacific')


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

    def __str__(self):
        return f'[{self.date}] {self.value} | {self.gain}/{self.rate}%'

    def inspect(self, previous=None):
        assert self.value == round(self.start_value + self.net_cash_flow + self.capital_gain, 2)
        assert self.gain == round(self.capital_gain + self.dividend_gain, 2)
        assert self.rate == round(self.gain / (self.start_value + self.net_cash_flow) * 100, 2)
        if previous:
            assert self.start_value == previous.value

    @classmethod
    def create_or_update(cls):
        today = tz.fromutc(datetime.utcnow()).date()
        inst = cls.query.order_by(cls.date.desc()).first()
        if inst.date == today:
            last = cls.query.order_by(cls.date.desc()).offset(1).first()
        else:
            last, inst = inst, cls(date=today)
            db.session.add(inst)

        m1 = request_m1finance()
        current_app.logger.info(f'm1finance: {m1}')
        assert last.date == tz.fromutc(datetime.fromisoformat(m1['startValue']['date'][:-1])).date()

        inst.value = m1['endValue']['value']
        inst.gain = m1['totalGain']
        inst.rate = m1['moneyWeightedRateOfReturn']
        inst.start_value = m1['startValue']['value']
        inst.net_cash_flow = m1['netCashFlow']
        inst.capital_gain = m1['capitalGain']
        inst.dividend_gain = m1['earnedDividends']
        current_app.logger.info(f'portfolio: {inst}')
        inst.inspect(last)
        return inst

    @classmethod
    def net_value_series(cls, limit=10):
        R = namedtuple('R', 'date value gain rate start')
        items = cls.query.order_by(cls.date.desc())[:limit]
        series = [R(None, None, None, None, items[0].value)]
        for e in items:
            gain = round(series[-1].start / (1 + 100 / e.rate), 2)
            start = round(series[-1].start / (1 + e.rate / 100), 2)
            series.append(R(e.date, series[-1].start, gain, e.rate, start))
        return series[:0:-1]

    @classmethod
    def init_app(cls, app):
        @app.cli.command()
        def update_m1_account():
            """ Update M1Finance Account """
            cls.create_or_update()
            db.session.commit()
