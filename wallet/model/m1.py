from collections import namedtuple
from datetime import datetime

from flask import current_app
from pytz import timezone

from wallet.core import db
from wallet.util.m1 import request_m1finance
from wallet.util.plivo import error_notifier

tz = timezone('US/Pacific')


class M1Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, server_default='')
    date = db.Column(db.Date, nullable=False)
    value = db.Column(db.Float, nullable=False)
    gain = db.Column(db.Float, nullable=False)
    rate = db.Column(db.Float, nullable=False)
    start_value = db.Column(db.Float, nullable=False)
    net_cash_flow = db.Column(db.Float, nullable=False)
    capital_gain = db.Column(db.Float, nullable=False)
    dividend_gain = db.Column(db.Float, nullable=False)
    updated = db.Column(db.DateTime, nullable=False, default=db.utcnow, onupdate=db.utcnow)

    __table_args__ = (
        db.UniqueConstraint('name', 'date', name='m1_portfolio_name_date_key'),
    )

    def __str__(self):
        return f'[{self.date}] {self.value} | {self.gain}/{self.rate}%'

    def inspect(self, previous=None):
        if previous:
            assert self.name == previous.name
            assert self.start_value == previous.value, \
                f'start value not matched {self.start_value}, expected {previous.value}'
        expected_capital_gain = round(self.value - self.start_value - self.net_cash_flow, 2)
        assert self.capital_gain == expected_capital_gain, \
            f'capital gain not matched {self.capital_gain}, expected {expected_capital_gain}'
        expected_gain = round(self.capital_gain + self.dividend_gain, 2)
        assert self.gain == expected_gain, f'gain not matched {self.gain}, expected {expected_gain}'
        expected_rate = round(self.gain / (self.start_value + self.net_cash_flow) * 100, 2)
        assert self.rate == expected_rate, f'rate not matched {self.rate}, expected {expected_rate}'

    def fix(self, previous=None):
        if previous and self.start_value != previous.value:
            current_app.logger.info(f'fixed start value from {self.start_value} to {previous.value}')
            self.start_value = previous.value
        expected_capital_gain = round(self.value - self.start_value - self.net_cash_flow, 2)
        if self.capital_gain != expected_capital_gain:
            current_app.logger.info(f'fixed capital gain from {self.capital_gain} to {expected_capital_gain}')
            self.capital_gain = expected_capital_gain
        expected_gain = round(self.capital_gain + self.dividend_gain, 2)
        if self.gain != expected_gain:
            current_app.logger.info(f'fixed gain from {self.gain} to {expected_gain}')
            self.gain = expected_gain
        expected_rate = round(self.gain / (self.start_value + self.net_cash_flow) * 100, 2)
        if self.rate != expected_rate:
            current_app.logger.info(f'fixed rate from {self.rate} to {expected_rate}')
            self.rate = expected_rate

    @classmethod
    def update(cls):
        m1 = request_m1finance()
        current_app.logger.info(f'm1finance: {m1}')
        today = tz.fromutc(datetime.utcnow()).date()

        result = []
        for name, performance in m1.items():
            inst = cls.query.filter_by(name=name).order_by(cls.date.desc()).first()
            if inst and inst.date == today:
                last = cls.query.filter_by(name=name).order_by(cls.date.desc()).offset(1).first()
            else:
                last, inst = inst, cls(name=name, date=today)
                db.session.add(inst)

            inst.value = performance['endValue']['value']
            inst.gain = performance['totalGain']
            inst.rate = performance['moneyWeightedRateOfReturn']
            inst.start_value = performance['startValue']['value']
            inst.net_cash_flow = performance['netCashFlow']
            inst.capital_gain = performance['capitalGain']
            inst.dividend_gain = performance['earnedDividends']
            current_app.logger.info(f'{name}: {inst}')
            result.append((inst, last,
                           tz.fromutc(datetime.fromisoformat(performance['startValue']['date'][:-1])).date()))

        for inst, last, start_date in result:
            if last:
                assert start_date == last.date, \
                    f'start date not matched {start_date}, expected {last.date}'
            inst.inspect(last)

    @classmethod
    def net_value_series(cls, name, limit):
        R = namedtuple('R', 'date value gain rate start')
        items = cls.query.filter_by(name=name).order_by(cls.date.desc())[:limit]
        series = [R(None, None, None, None, items[0].value)]
        for e in items:
            gain = round(series[-1].start / (1 + 100 / e.rate), 2)
            start = round(series[-1].start / (1 + e.rate / 100), 2)
            series.append(R(e.date, series[-1].start, gain, e.rate, start))
        return series[:0:-1]

    @classmethod
    def init_app(cls, app):
        @app.cli.command()
        @error_notifier
        def update_m1_account():
            """ Update M1Finance Account """
            cls.update()
            db.session.commit()
