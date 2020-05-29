from bisect import bisect_left
from collections import defaultdict, namedtuple
from datetime import datetime, timedelta

from flask import current_app
from requests import Session, get

HOST = 'https://api.robinhood.com'


def init_app(app):
    @app.cli.command()
    def robinhood():
        """ Robinhood """
        get_summary()


def get_summary(output=print, verbose=True):
    req = Session()
    req.headers['Authorization'] = f'Bearer {current_app.config["RH_TOKEN"]}'

    positions = get_option_positions(req)
    for item in positions.values():
        shares = sum(pos.shares for pos in item.positions)
        output(f'{item.symbol} [Gain {sum(pos.gain for pos in item.positions)},'
               f' Price {item.price}, Shares {shares}, Value {round(shares * item.price, 2)}]:')
        if verbose:
            for pos in item.positions:
                output(f' - {pos.name} [Gain {pos.gain}, Shares {pos.shares}, Health {pos.health}%]')

    output()
    dd = defaultdict(lambda: [0, 0])
    for item in positions.values():
        for pos in item.positions:
            dd[pos.expiry][0] += pos.gain
            dd[pos.expiry][1] += abs(pos.shares) * item.price
    for expiry in sorted(dd):
        output(f'Week {expiry}\'s Gain: {dd[expiry][0]}, Value: {round(dd[expiry][1])}')
    qqq = sum(pos.shares for pos in positions['QQQ'].positions) * positions['QQQ'].price
    spy = sum(pos.shares for pos in positions['SPY'].positions) * positions['SPY'].price
    ratio = round(spy / qqq, 2)
    output(f'QQQ:SPY  1.0:{ratio}')
    target = -0.8
    if ratio < target:  # too much SPY
        output(f'Long QQQ {round((spy / target - qqq) / positions["QQQ"].price)} shares')
    elif ratio > target:  # too much QQQ
        output(f'Short SPY {round((qqq * target - spy) / positions["SPY"].price)} shares')

    output()
    today = datetime.today()
    expiry_date = (today + timedelta(days=21 + (4 - today.weekday()) % 7)).strftime('%Y-%m-%d')
    output(f'QQQ candidates: [stock price: {positions["QQQ"].price}, expiry date: {expiry_date}]')
    spreads = find_option_spreads(req, 'short_put',
                                  positions['QQQ'].chain, expiry_date, positions['QQQ'].price, .48, .64)
    if not verbose:
        spreads = spreads[:2]
    for spread in spreads:
        output(f' - {spread.name} [Shares {spread.shares}, Price {spread.price},'
               f' Maximum {spread.maximum}, Health {spread.health}%]')
    output(f'SPY candidates: [stock price: {positions["SPY"].price}, expiry date: {expiry_date}]')
    spreads = find_option_spreads(req, 'short_call',
                                  positions['SPY'].chain, expiry_date, positions['SPY'].price, .48, .64)
    if not verbose:
        spreads = spreads[:2]
    for spread in spreads:
        output(f' - {spread.name} [Shares {spread.shares}, Price {spread.price},'
               f' Maximum {spread.maximum}, Health {spread.health}%]')


def get_summary_with_notif():
    def output(line=None):
        notification[0] += f'{line or ""}\n'

    notification = ['']
    get_summary(output, False)
    from wallet.util.plivo import send
    send(notification[0])


def get_option_positions(req):
    Position = namedtuple('Position', 'name gain shares health expiry')
    SymbolPositions = namedtuple('SymbolPositions', 'symbol positions price chain')
    positions = {}  # symbol:SymbolPositions

    for position in _paginate(req, f'{HOST}/options/aggregate_positions/'):
        symbol, quantity, legs = position['symbol'], round(float(position['quantity'])), position['legs']
        if quantity == 0 or len(legs) != 2:
            continue
        if symbol not in positions:
            price = float(req.get(f'{HOST}/marketdata/quotes/{symbol}/').json()['last_trade_price'])
            positions[symbol] = SymbolPositions(symbol, [], price, position['chain'][-37:-1])

        maximum = round(abs(float(legs[0]['strike_price']) - float(legs[1]['strike_price'])) * 100 * quantity)
        strike_prices = '/'.join(str(float(leg['strike_price'])) for leg in legs)
        expiry = datetime.fromisoformat(legs[0]['expiration_date']).strftime('%m/%d')
        name = {
            'long_call_spread': lambda: f'{symbol} {expiry} Exp • {strike_prices} Calls • {quantity} Debit Spreads',
            'long_put_spread': lambda: f'{symbol} {expiry} Exp • {strike_prices} Puts • {quantity} Debit Spreads',
            'short_call_spread': lambda: f'{symbol} {expiry} Exp • {strike_prices} Calls • {quantity} Credit Spreads',
            'short_put_spread': lambda: f'{symbol} {expiry} Exp • {strike_prices} Puts • {quantity} Credit Spreads',
        }[position['strategy']]()
        market_data = req.get(f'{HOST}/marketdata/options/',
                              params={'instruments': ','.join(leg['option'] for leg in legs)}).json()['results']
        equity, shares = 0, 0
        for i, leg in enumerate(legs):
            if leg['position_type'] == 'long':
                equity += round(float(market_data[i]['mark_price']) * 100 * quantity)
                shares += round(float(market_data[i]['delta']) * 100 * quantity)
            else:
                equity -= round(float(market_data[i]['mark_price']) * 100 * quantity)
                shares -= round(float(market_data[i]['delta']) * 100 * quantity)
        cost = round(float(position['average_open_price']) * quantity)  # always positive
        gain = equity - cost
        health = equity / maximum
        if position['direction'] == 'credit':
            gain = equity + cost
            health = 1 + equity / maximum
        positions[symbol].positions.append(Position(name, gain, shares, round(health * 100), expiry))

    return positions


def find_option_spreads(req, strategy, chain_id, expiry_date, stock_price, ratio1, ratio2):
    option_type = 'call' if 'call' in strategy else 'put'
    params = {'state': 'active', 'type': option_type, 'chain_id': chain_id, 'expiration_dates': expiry_date}
    options = sorted((float(option['strike_price']), option['url'])
                     for option in _paginate(req, f'{HOST}/options/instruments/', params))
    i = bisect_left(options, (stock_price, ''))
    options = {
        'long_call': lambda: options[max(0, i - 10):i][::-1],
        'long_put': lambda: options[i:min(len(options), i + 10)],
        'short_call': lambda: options[i:min(len(options), i + 10)],
        'short_put': lambda: options[max(0, i - 10):i][::-1],
    }[strategy]()
    market_data = req.get(f'{HOST}/marketdata/options/',
                          params={'instruments': ','.join(option[1] for option in options)}).json()['results']
    Option = namedtuple('Option', 'strike_price mark_price delta')
    options = [Option(option[0], float(market_data[i]['mark_price']), float(market_data[i]['delta']))
               for i, option in enumerate(options)]

    Spread = namedtuple('Spread', 'name shares price maximum health')
    spreads = []
    for i in range(len(options)):
        if {
            'long_call': lambda: options[i].delta < ratio1,
            'long_put': lambda: options[i].delta > -ratio1,
            'short_call': lambda: options[i].delta > 1 - ratio1,
            'short_put': lambda: options[i].delta < ratio1 - 1,
        }[strategy]():
            continue
        for j in range(i + 1, len(options)):
            price = round(options[j].mark_price - options[i].mark_price, 2)
            maximum = round(abs(options[j].strike_price - options[i].strike_price), 2)
            health = price / maximum
            if 'short' in strategy:
                health = 1 + price / maximum
            if health > ratio2:
                continue
            strike_prices = f'{options[j].strike_price}/{options[i].strike_price}'
            name = {
                'long_call': lambda: f'{strike_prices} Calls Debit Spread',
                'long_put': lambda: f'{strike_prices} Puts Debit Spread',
                'short_call': lambda: f'{strike_prices} Calls Credit Spread',
                'short_put': lambda: f'{strike_prices} Puts Credit Spread',
            }[strategy]()
            shares = round((options[j].delta - options[i].delta) * 100)
            spreads.append(Spread(name, shares, price, maximum, round(health * 100)))
    spreads.sort(key=lambda c: c.health)
    result = []
    for spread in spreads:
        if not result or spread.maximum >= result[-1].maximum:
            result.append(spread)
    return result


def _paginate(req, url, params=None):
    result = req.get(url, params=params).json()
    for item in result['results']:
        yield item
    while result['next']:
        result = get(result['next']).json()
        for item in result['results']:
            yield item
