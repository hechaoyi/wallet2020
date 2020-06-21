from collections import namedtuple
from datetime import datetime

from flask import current_app
from pytz import timezone

from wallet.core import db
from wallet.util.m1 import get_accounts
from wallet.util.plivo import error_notifier
from wallet.util.robinhood import get_portfolio

tz = timezone('US/Pacific')


class M1Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False, server_default='')
    date = db.Column(db.Date, nullable=False)
    value = db.Column(db.Float, nullable=False)
    gain = db.Column(db.Float, nullable=False)
    rate = db.Column(db.Float, nullable=False)
    start_value = db.Column(db.Float, nullable=False)
    net_cash_flow = db.Column(db.Float, nullable=False)
    capital_gain = db.Column(db.Float, nullable=False)
    dividend_gain = db.Column(db.Float, nullable=False)
    cost_basis = db.Column(db.Float)
    updated = db.Column(db.DateTime, nullable=False, default=db.utcnow, onupdate=db.utcnow)

    __table_args__ = (
        db.UniqueConstraint('name', 'date', name='m1_portfolio_name_date_key'),
    )

    def __str__(self):
        return f'[{self.date}] {self.value} | {self.gain}/{self.rate}%'

    def inspect(self, previous=None, fix_start_value=False):
        if previous:
            assert self.name == previous.name
            if (fix_start_value and self.start_value != previous.value
                    and round(abs(self.start_value - previous.value) / previous.value, 4) <= .002):
                diff = round(self.start_value - previous.value, 2)
                current_app.logger.info(f'fixed start value, capital gain, gain by {diff}')
                self.start_value = previous.value
                self.capital_gain = round(self.capital_gain + diff, 2)
                self.gain = round(self.gain + diff, 2)
                expected_rate = round(self.gain / (self.start_value + self.net_cash_flow) * 100, 2)
                if round(abs(self.rate - expected_rate), 2) <= .2:
                    self.rate = expected_rate
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
        m1 = get_accounts()
        current_app.logger.info(f'm1finance: {m1}')
        today = tz.fromutc(datetime.utcnow()).date()

        result = []

        # M1
        for name, performance in m1.items():
            if not performance or (performance['startValue']['value'] == 0 and performance['endValue']['value'] == 0):
                continue
            start_date = tz.fromutc(datetime.fromisoformat(performance['startValue']['date'][:-1])).date()
            assert start_date == today, f'start date not matched {start_date}, expected {today}'
            inst, last = cls._load(name, today)

            inst.value = performance['endValue']['value']
            inst.gain = performance['totalGain']
            inst.rate = performance['moneyWeightedRateOfReturn']
            inst.start_value = performance['startValue']['value']
            inst.net_cash_flow = performance['netCashFlow']
            inst.capital_gain = performance['capitalGain']
            inst.dividend_gain = performance['earnedDividends']
            inst.cost_basis = round(inst.net_cash_flow, -2) + (last.cost_basis if last else 0)
            current_app.logger.info(f'{name}: {inst}')
            result.append((inst, last))

        # Robinhood
        name, rh = 'Robinhood', get_portfolio()
        inst, last = cls._load(name, today)
        inst.value = round(rh.value, 2)
        inst.start_value = round(rh.start_value, 2)
        inst.gain = round(rh.value - rh.start_value, 2)
        inst.rate = round(inst.gain / inst.start_value * 100, 2)
        inst.capital_gain = inst.gain
        inst.net_cash_flow = inst.dividend_gain = 0
        inst.cost_basis = last.cost_basis if last else 0
        current_app.logger.info(f'{name}: {inst}')
        result.append((inst, last))

        for inst, last in result:
            inst.inspect(last, fix_start_value=True)

    @classmethod
    def _load(cls, name, today):
        inst = cls.query.filter_by(name=name).order_by(cls.date.desc()).first()
        if inst and inst.date == today:
            last = cls.query.filter_by(name=name).order_by(cls.date.desc()).offset(1).first()
        else:
            last, inst = inst, cls(name=name, date=today)
            db.session.add(inst)
        return inst, last

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
        def update_m1_accounts():
            """ Update M1Finance Accounts """
            cls.update()
            db.session.commit()
