from collections import defaultdict
from datetime import date, timedelta
from functools import reduce
from operator import concat

import seaborn
from numpy import ones
from pandas import DataFrame
from pandas_datareader import DataReader

from wallet.util.m1 import get_hedge_fund_replication_securities, screen_funds, screen_securities

seaborn.set(rc={'figure.figsize': (15, 5)})


class Analysis:
    def __init__(self, symbols, data_points, period, risk_free_rate_per_year=2):
        data_points += period
        start = date.today() - timedelta(days=data_points * 1.5)
        start = DataReader('SPY', 'yahoo', start).index[-data_points]
        self.data = DataReader(symbols, 'yahoo', start)['Adj Close']
        self.period = period
        self.origin_data = None
        self.risk_free_rate_per_day = risk_free_rate_per_year / 252

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
        # self.drop_mask()
        stat = _moving_average_statistics(self.data, self.period, self.risk_free_rate_per_day)
        stat = stat[stat['count'] == stat['count'].max()]
        # stat = stat[(stat['shrp'] > 0) & (stat['yield'] > 0)]
        # stat = stat[(stat['std'] > .1) & (abs(stat['skew']) < 1)]
        self.setup_mask(stat.index)
        return stat

    def graph(self, portfolio=None, drop_components=False, truncate=0,
              rebalance_interval=10, rebalance_threshold=2):
        if portfolio:
            self.setup_mask(portfolio)
            total_weight = sum(portfolio.values())
            if total_weight > 0:
                portfolio = {st: round(sh / total_weight, 3) for st, sh in portfolio.items()}
        if truncate > 0:
            self.data = self.data.truncate(self.data.index[0 - truncate - self.period])
        start = self.data.index[0]
        data = {col: self.data[col] * (100 / self.data[col][start]) for col in self.data.columns}
        if portfolio:
            data['Portfolio'] = sum(data[st] * sh for st, sh in portfolio.items())
            if total_weight <= 0:
                data['Portfolio'] += 100

            if rebalance_interval > 0:
                data['Portfolio-RB'] = data['Portfolio'].copy()
                last_rebalance, shares = 1 - rebalance_interval, dict(portfolio)
                for i in range(1, len(self.data.index)):
                    idx = self.data.index[i]
                    data['Portfolio-RB'][idx] = sum(data[st][idx] * sh for st, sh in shares.items())
                    if i - last_rebalance < rebalance_interval:
                        continue
                    new_shares = {st: data['Portfolio-RB'][idx] * sh / data[st][idx] for st, sh in portfolio.items()}
                    delta = sum(abs(sh - shares[st]) for st, sh in new_shares.items()) * 100 / 2
                    if delta >= rebalance_threshold:
                        print(f'{idx.date()} rebalance: '
                              f'buy {",".join([st for st, sh in new_shares.items() if sh > shares[st]])}, '
                              f'sell {",".join([st for st, sh in new_shares.items() if sh < shares[st]])}')
                        last_rebalance, shares = i, new_shares

            if drop_components:
                if isinstance(drop_components, list):
                    for st in drop_components:
                        del data[st]
                else:
                    for st in portfolio:
                        del data[st]
        frame = DataFrame(data)
        seaborn.lineplot(data=frame, dashes=False)
        return _moving_average_statistics(frame, self.period, self.risk_free_rate_per_day)

    def optimize(self, min_percent=.2, max_count=5, sharpe=True):
        data = self.data.rolling(self.period).mean().pct_change() * 100
        corr = data.corr()
        candidates = set(self.data.columns)
        similarity = defaultdict(set)
        while len(candidates) > 1:
            ratio, shrp = _optimize(data, self.risk_free_rate_per_day, sharpe)
            symbol = min(ratio, key=lambda s: ratio[s])
            if ratio[symbol] >= min_percent and len(ratio) <= max_count:
                return shrp, ratio, {s: similarity[s] for s in ratio}
            candidates.remove(symbol)
            similarity[corr.loc[symbol, candidates].idxmax()].add(symbol)
            data = data[candidates]
        candidate = next(iter(candidates))
        shrp = (data[candidate].mean() - self.risk_free_rate_per_day) / data[candidate].std()
        return round(shrp, 4), {candidate: 1}, {candidate: similarity[candidate]}

    def optimize_iteration(self, group_ratios, min_percent=.2, max_count=5, additions=None, sharpe=True):
        def try_and_try_again():
            shrp, ratio, similarity = self.optimize(min_percent, max_count, sharpe)
            if (shrp, ratio) not in ratios:
                ratios.append((shrp, ratio))
            for symbol in ratio:
                if similarity[symbol]:
                    self.setup_mask(ratio.keys() - {symbol} | similarity[symbol])
                    s, r, _ = self.optimize(min_percent, max_count, sharpe)
                    if (s, r) not in ratios:
                        ratios.append((s, r))
                candidates.remove(symbol)

        assert not additions or not (set(additions) - set(self.origin_data.columns))
        ratios = []

        candidates = set(self.data.columns)
        for _ in range(len(group_ratios) * 3):
            try_and_try_again()
            if not candidates:
                break
            self.setup_mask(candidates)

        if additions:
            candidates = set(additions)
            while candidates:
                self.setup_mask(candidates)
                try_and_try_again()

        candidates = {s for _, r in ratios for s in r}
        while candidates:
            self.setup_mask(candidates)
            try_and_try_again()

        ratios.sort(key=lambda e: e[0])
        return ratios, self._combine_groups(
            [r for _, r in ratios[::-1]],
            group_ratios,
            set(additions) if additions else set(),
        )

    @staticmethod
    def _combine_groups(ratios, group_ratios, previous):
        def dfs(index, skipped, covered, selected):
            if len(selected) == len(group_ratios):
                covered_set = frozenset({s for rt in selected for s in rt} & previous)
                if skipped <= results[covered][covered_set][0]:
                    if skipped < results[covered][covered_set][0]:
                        results[covered][covered_set] = (skipped, [])
                    choice = {s: round(rt[s] * gr)
                              for rt, gr in zip(selected, group_ratios) for s in rt}
                    results[covered][covered_set][1].append([choice, previous & choice.keys()])
                return
            if index >= len(ratios) or skipped > max((e[0] for e in results[-1].values()), default=float('+inf')):
                return
            ratio = ratios[index]
            if len(ratio) > 1 and all(s not in rt for s in ratio for rt in selected):
                dfs(index + 1, skipped, covered + len(previous & ratio.keys()), selected + [ratio])
                dfs(index + 1, skipped + 1, covered, selected)
            else:
                dfs(index + 1, skipped, covered, selected)

        results = [defaultdict(lambda: (float('+inf'), [])) for _ in range(len(previous) + 1)]
        dfs(0, 0, 0, [])
        for i in range(1, len(previous) + 1):
            for covered_set in results[i]:
                skipped = results[i][covered_set][0]
                for j in range(i):
                    to_be_deleted = []
                    for cs in results[j]:
                        if not (cs - covered_set) and results[j][cs][0] >= skipped:
                            to_be_deleted.append(cs)
                    for tbd in to_be_deleted:
                        del results[j][tbd]
        return [(i, *r) for i, rs in enumerate(results) for r in rs.values() if r[1]]

    @classmethod
    def from_securities(cls, data_points, period=5, additions=None, **kwargs):
        symbols = screen_securities(**kwargs)
        if additions:
            symbols += additions
        return cls(symbols, data_points, period)

    @classmethod
    def from_funds(cls, data_points, period=5, additions=None, *, categories, **kwargs):
        symbols = reduce(concat, (screen_funds(*c.split(','), **kwargs) for c in categories))
        if additions:
            symbols += additions
        return cls(symbols, data_points, period)

    @classmethod
    def from_hedge_funds(cls, data_points, period=5, additions=None, *, categories, **kwargs):
        symbols = []
        for category, securities in get_hedge_fund_replication_securities(**kwargs).items():
            print(f'{category} ({len(securities)} securities)')
            if not categories or category in categories:
                symbols.extend(securities)
                for symbol, security in securities.items():
                    cap = f'{security.cap:.1f}B' if security.cap else ''
                    pe = f'{security.pe}PE' if security.pe else ''
                    print(f'  [{symbol.ljust(5)}] {security.name[:16].ljust(16)}:\t'
                          f'{cap.ljust(8)} {pe.ljust(8)} {",".join(security.funds)}')
        if additions:
            additions = set(additions) - set(symbols)
            if additions:
                print(f'Additions: {additions}')
                symbols += additions
        return cls(symbols, data_points, period)


def _moving_average_statistics(frame, period, risk_free_rate_per_day=.008):
    data = frame.rolling(period).mean().pct_change() * 100
    stat = data.describe(percentiles=[.05, .5, .95]).T
    stat['shrp'] = (stat['mean'] - risk_free_rate_per_day) / stat['std']
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


def _optimize(data, risk_free_rate_per_day, sharpe):
    def calculate(target):
        weights = ((B * one.T.dot(cov_inv) - A * mean.T.dot(cov_inv)) / (B * C - A * A) +
                   (C * mean.T.dot(cov_inv) - A * one.T.dot(cov_inv)) / (B * C - A * A) * target)
        m, s = weights.T.dot(mean), weights.T.dot(cov).dot(weights) ** .5
        r = ((m - risk_free_rate_per_day) / s) if sharpe else (1 / s)
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
