from collections import defaultdict
from datetime import date, timedelta
from functools import reduce
from operator import concat

from numpy import ones
from pandas import DataFrame
from pandas_datareader import DataReader

from wallet.util.m1 import screen_funds, screen_securities

RISK_FREE_RATE_PER_DAY = 2 / 252


class Analysis:
    def __init__(self, symbols, data_points, period):
        data_points += period
        start = date.today() - timedelta(days=data_points * 1.5)
        start = DataReader('SPY', 'yahoo', start).index[-data_points]
        self.data = DataReader(symbols, 'yahoo', start)['Adj Close']
        self.period = period
        self.origin_data = None

    def __str__(self):
        return f'from {self.data.index[0].date()} to {self.data.index[-1].date()} - {len(self.data.columns)} symbols'

    def setup_mask(self, mask):
        if self.origin_data is None:
            self.origin_data = self.data
        self.data = self.origin_data[set(mask)]

    def drop_mask(self):
        if self.origin_data is not None:
            self.data = self.origin_data
            self.origin_data = None

    def screen(self):
        self.drop_mask()
        stat = _moving_average_statistics(self.data, self.period)
        stat = stat[(stat['shrp'] > 0) & (stat['std'] > .1) & (abs(stat['skew']) < 1)
                    & (stat['count'] == stat['count'].max())]
        self.setup_mask(stat.index)
        return stat

    def graph(self, portfolio=None, drop_components=False):
        start = self.data.index[0]
        if portfolio:
            self.setup_mask(portfolio)
        data = {col: self.data[col] * (100 / self.data[col][start]) for col in self.data.columns}
        if portfolio:
            data['Portfolio'] = sum(data[st] * sh for st, sh in portfolio.items())
            data['Portfolio'] = data['Portfolio'] * (100 / data['Portfolio'][start])
            if drop_components:
                for st in portfolio:
                    del data[st]
        frame = DataFrame(data)
        frame.plot(figsize=(15, 5), grid=1)
        return _moving_average_statistics(frame, self.period)

    def optimize(self, min_percent=.2, max_count=5, amplifier=0):
        data = self.data.rolling(self.period).mean().pct_change() * 100
        corr = data.corr()
        candidates = set(self.data.columns)
        similarity = defaultdict(set)
        while len(candidates) > 1:
            ratio, shrp = _optimize(data, amplifier)
            symbol = min(ratio, key=lambda s: ratio[s])
            if ratio[symbol] >= min_percent and len(ratio) <= max_count:
                return shrp, ratio, {s: similarity[s] for s in ratio}
            candidates.remove(symbol)
            similarity[corr.loc[symbol, candidates].idxmax()].add(symbol)
            data = data[candidates]
        candidate = next(iter(candidates))
        shrp = (data[candidate].mean() - RISK_FREE_RATE_PER_DAY * (1 + amplifier)) / data[candidate].std()
        return round(shrp, 4), {candidate: 1}, {candidate: similarity[candidate]}

    def optimize_iteration(self, group_ratios, min_percent=.2, max_count=5, amplifier=0, additions=None):
        def try_and_try_again():
            shrp, ratio, similarity = self.optimize(min_percent, max_count, amplifier)
            if (shrp, ratio) not in ratios:
                ratios.append((shrp, ratio))
            for symbol in ratio:
                if similarity[symbol]:
                    self.setup_mask(ratio.keys() - {symbol} | similarity[symbol])
                    s, r, _ = self.optimize(min_percent, max_count, amplifier)
                    if (s, r) not in ratios:
                        ratios.append((s, r))
                candidates.remove(symbol)

        assert not additions or not (set(additions) - set(self.origin_data.columns))
        ratios = []

        candidates = set(self.data.columns)
        for _ in range(len(group_ratios) * 4):
            try_and_try_again()
            if not candidates:
                break
            self.setup_mask(candidates)

        candidates = {s for _, r in ratios for s in r}
        if additions:
            candidates |= set(additions)
        while candidates:
            self.setup_mask(candidates)
            try_and_try_again()

        ratios.sort()
        return ratios, self._combine_groups(
            [r for _, r in ratios[::-1]], group_ratios, set(additions) if additions else set()
        )

    @staticmethod
    def _combine_groups(ratios, group_ratios, previous):
        def dfs(index, skipped, covered, selected):
            if len(selected) == len(group_ratios):
                if (covered, -skipped) >= result_weight[0]:
                    if (covered, -skipped) > result_weight[0]:
                        result_weight[0] = (covered, -skipped)
                        del result[:]
                    result.append({s: round(rt[s] * gr)
                                   for rt, gr in zip(selected, group_ratios)
                                   for s in rt})
                return
            if index >= len(ratios) or skipped > len(group_ratios) * 2:
                return
            ratio = ratios[index]
            if len(ratio) > 1 and all(s not in rt for s in ratio for rt in selected):
                dfs(index + 1, skipped, covered + len(previous & ratio.keys()), selected + [ratio])
                dfs(index + 1, skipped + 1, covered, selected)
            else:
                dfs(index + 1, skipped, covered, selected)

        result_weight, result = [(0, 0)], []
        dfs(0, 0, 0, [])
        return result

    @classmethod
    def from_securities(cls, data_points, period=5, additions=None, **kwargs):
        symbols = screen_securities(**kwargs)
        if additions:
            symbols += additions
        return cls(symbols, data_points, period)

    @classmethod
    def from_funds(cls, data_points, period=5, additions=None, max_exp=1, *, categories):
        symbols = reduce(concat, (screen_funds(*c.split(','), max_exp=max_exp) for c in categories))
        if additions:
            symbols += additions
        return cls(symbols, data_points, period)


def _moving_average_statistics(frame, period):
    data = frame.rolling(period).mean().pct_change() * 100
    stat = data.describe().T
    stat['shrp'] = (stat['mean'] - RISK_FREE_RATE_PER_DAY) / stat['std']
    stat['yield'] = frame.T[frame.index[-1]] / frame.T[frame.index[0]] * 100 - 100
    stat['down'] = frame.apply(_max_drawdown)
    stat['skew'] = data.skew()
    return stat.sort_values('shrp', ascending=False)


def _max_drawdown(series):
    max_price_so_far, max_drawdown_so_far = float('-inf'), 0
    result = None
    for p in series:
        drawdown = max_price_so_far - p
        if drawdown > max_drawdown_so_far:
            max_drawdown_so_far = drawdown
            result = max_drawdown_so_far / max_price_so_far * 100
        max_price_so_far = max(max_price_so_far, p)
    return result


def _optimize(data, amplifier=0):
    def calculate(target):
        weights = ((B * one.T.dot(cov_inv) - A * mean.T.dot(cov_inv)) / (B * C - A * A) +
                   (C * mean.T.dot(cov_inv) - A * one.T.dot(cov_inv)) / (B * C - A * A) * target)
        m, s = weights.T.dot(mean), weights.T.dot(cov).dot(weights) ** .5
        r = (m - RISK_FREE_RATE_PER_DAY * (1 + amplifier)) / s
        return {k: round(v, 4) for k, v in weights.items()}, round(r, 4)

    def attempt(guess):
        if guess < mean.min() or guess > mean.max():
            return float('inf')
        _, r = calculate(guess)
        if r <= 0:
            return float('inf')
        return 1 / r

    from scipy import linalg
    from scipy.optimize import minimize_scalar
    mean, cov, one = data.mean(), data.cov(), ones(len(data.columns))
    cov_inv = DataFrame(linalg.pinv(cov.values), cov.columns, cov.index)
    A, B, C = one.T.dot(cov_inv).dot(mean), mean.T.dot(cov_inv).dot(mean), one.T.dot(cov_inv).dot(one)
    res = minimize_scalar(attempt, bounds=(mean.min(), mean.max()), method='Bounded')
    assert res.success
    return calculate(res.x)
