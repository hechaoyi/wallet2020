from bisect import bisect_left
from collections import defaultdict, namedtuple
from datetime import datetime, timedelta
from time import sleep

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
    req.headers['User-Agent'] = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36'
                                 ' (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36')
    req.headers['Referer'] = 'https://robinhood.com/'
    req.headers['Cache-Control'] = 'no-cache'
    req.headers['Pragma'] = 'no-cache'

    positions = get_option_positions(req)
    for item in positions.values():
        shares = sum(pos.shares for pos in item.positions)
        output(f'{item.symbol} '
               f'[Gain {sum(pos.gain for pos in item.positions)}, Theta {sum(pos.theta for pos in item.positions):.2f},'
               f' Shares {shares}, Gamma {sum(pos.gamma for pos in item.positions):.2f},'
               f' Price {item.price}, Value {shares * item.price:.0f}]:')
        if verbose:
            for pos in item.positions:
                output(f' - {pos.name} '
                       f'[Gain {pos.gain}, Theta {pos.theta},'
                       f' Shares {pos.shares}, Gamma {pos.gamma},'
                       f' Health {pos.health}%]')

    output()
    dd = defaultdict(lambda: [0, 0, 0])
    for item in positions.values():
        for pos in item.positions:
            dd[pos.expiry][0] += pos.gain
            dd[pos.expiry][1] += pos.theta
            dd[pos.expiry][2] += abs(pos.shares) * item.price
    for expiry in sorted(dd):
        output(f'Week {expiry}\'s Gain: {dd[expiry][0]}, Theta: {dd[expiry][1]:.2f}, Value: {dd[expiry][2]:.0f}')
    qqq = sum(pos.shares for pos in positions['QQQ'].positions) * positions['QQQ'].price
    spy = sum(pos.shares for pos in positions['SPY'].positions) * positions['SPY'].price
    ratio = round(spy / qqq, 2)
    output(f'QQQ:SPY  1.0:{ratio}')
    target = -0.7
    if ratio < target - .1:  # too much SPY
        output(f'Long QQQ {(spy / target - qqq) / positions["QQQ"].price:.0f} shares')
    elif ratio > target + .1:  # too much QQQ
        output(f'Short SPY {(qqq * target - spy) / positions["SPY"].price:.0f} shares')

    output()
    today = datetime.today()
    expiry_date = (today + timedelta(days=28 + (4 - today.weekday()) % 7)).strftime('%Y-%m-%d')
    expiry_date = {
        '2020-07-03': '2020-07-02',
    }.get(expiry_date, expiry_date)
    output(f'QQQ candidates: [stock price: {positions["QQQ"].price}, expiry date: {expiry_date}]')
    spreads = find_option_spreads(req, 'short_put',
                                  positions['QQQ'].chain, expiry_date, positions['QQQ'].price, .56, .72)
    if not verbose:
        spreads = spreads[1:4]
    for spread in spreads:
        output(f' - {spread.name} [Shares {spread.shares}, Price {spread.price},'
               f' Maximum {spread.maximum}, Health {spread.health}%,'
               f' Gamma {spread.gamma}, Theta {spread.theta}]')
    output(f'SPY candidates: [stock price: {positions["SPY"].price}, expiry date: {expiry_date}]')
    spreads = find_option_spreads(req, 'short_call',
                                  positions['SPY'].chain, expiry_date, positions['SPY'].price, .64, .80)
    if not verbose:
        spreads = spreads[1:4]
    for spread in spreads:
        output(f' - {spread.name} [Shares {spread.shares}, Price {spread.price},'
               f' Maximum {spread.maximum}, Health {spread.health}%,'
               f' Gamma {spread.gamma}, Theta {spread.theta}]')


def get_summary_with_notif():
    def output(line=None):
        notification[0] += f'{line or ""}\n'

    notification = ['']
    get_summary(output, verbose=False)
    from wallet.util.plivo import send
    send(notification[0])


def get_option_positions(req):
    Position = namedtuple('Position', 'name gain shares health gamma theta expiry')
    SymbolPositions = namedtuple('SymbolPositions', 'symbol positions price chain')
    positions = {}  # symbol:SymbolPositions

    for position in _paginate(req, f'{HOST}/options/aggregate_positions/'):
        symbol, quantity, legs = position['symbol'], round(float(position['quantity'])), position['legs']
        if quantity == 0 or len(legs) != 2:
            continue
        legs = sorted(legs, key=lambda leg: float(leg['strike_price']))
        if symbol not in positions:
            price = float(req.get(f'{HOST}/marketdata/quotes/{symbol}/').json()['last_trade_price'])
            positions[symbol] = SymbolPositions(symbol, [], price, position['chain'][-37:-1])
        else:
            price = positions[symbol].price

        market_data = _get_options_market_data(req, [leg['option'] for leg in legs])
        maximum = round(abs(float(legs[0]['strike_price']) - float(legs[1]['strike_price'])) * 100 * quantity)
        strike_prices = '/'.join(str(float(leg['strike_price'])) for leg in legs)
        expiry = datetime.fromisoformat(legs[0]['expiration_date']).strftime('%m/%d')
        name = {
            'long_call_spread': lambda: f'{symbol} {expiry} Exp • {strike_prices} Calls • {quantity} Debit Spreads',
            'long_put_spread': lambda: f'{symbol} {expiry} Exp • {strike_prices} Puts • {quantity} Debit Spreads',
            'short_call_spread': lambda: f'{symbol} {expiry} Exp • {strike_prices} Calls • {quantity} Credit Spreads',
            'short_put_spread': lambda: f'{symbol} {expiry} Exp • {strike_prices} Puts • {quantity} Credit Spreads',
        }[position['strategy']]()
        equity, shares, gamma, theta = 0, 0, 0, 0
        for i, leg in enumerate(legs):
            data = market_data[i]
            if leg['position_type'] == 'long':
                equity += round(float(data['mark_price']) * 100 * quantity)
                shares += round(float(data['delta']) * 100 * quantity)
                gamma += float(data['gamma']) * quantity * price  # the change of shares per 1%
                theta += float(data['theta']) * 100 * quantity  # the change of equity per day
            else:
                equity -= round(float(data['mark_price']) * 100 * quantity)
                shares -= round(float(data['delta']) * 100 * quantity)
                gamma -= float(data['gamma']) * quantity * price  # the change of shares per 1%
                theta -= float(data['theta']) * 100 * quantity  # the change of equity per day
        cost = round(float(position['average_open_price']) * quantity)  # always positive
        gain = equity - cost
        health = equity / maximum
        if position['direction'] == 'credit':
            gain = equity + cost
            health = 1 + equity / maximum
        positions[symbol].positions.append(Position(name, gain, shares,
                                                    round(health * 100), round(gamma, 2), round(theta, 2), expiry))

    return positions


def find_option_spreads(req, strategy, chain_id, expiry_date, stock_price, ratio1, ratio2):
    option_type = 'call' if 'call' in strategy else 'put'
    params = {'state': 'active', 'type': option_type, 'chain_id': chain_id, 'expiration_dates': expiry_date}
    options = sorted((float(option['strike_price']), option['url'])
                     for option in _paginate(req, f'{HOST}/options/instruments/', params))
    i = bisect_left(options, (stock_price, ''))
    options = {
        'long_call': lambda: options[max(0, i - 16):i][::-1],
        'long_put': lambda: options[i:min(len(options), i + 16)],
        'short_call': lambda: options[i:min(len(options), i + 16)],
        'short_put': lambda: options[max(0, i - 16):i][::-1],
    }[strategy]()
    market_data = _get_options_market_data(req, [option[1] for option in options])
    Option = namedtuple('Option', 'strike_price mark_price delta gamma theta')
    options = [Option(option[0], float(market_data[i]['mark_price']), float(market_data[i]['delta']),
                      float(market_data[i]['gamma']), float(market_data[i]['theta']))
               for i, option in enumerate(options)]

    Spread = namedtuple('Spread', 'name shares price maximum health gamma theta')
    spreads = []
    for i in range(len(options)):
        if {
            'long_call': lambda: options[i].delta < ratio1,
            'long_put': lambda: -options[i].delta < ratio1,
            'short_call': lambda: options[i].delta > 1 - ratio1,
            'short_put': lambda: -options[i].delta > 1 - ratio1,
        }[strategy]():
            continue
        for j in range(i + 1, len(options)):
            shares = round((options[j].delta - options[i].delta) * 100)
            price = round(options[j].mark_price - options[i].mark_price, 2)
            maximum = round(abs(options[j].strike_price - options[i].strike_price), 2)
            gamma = round((options[j].gamma - options[i].gamma) * stock_price, 2)
            theta = round((options[j].theta - options[i].theta) * 100, 2)
            health = price / maximum
            if 'short' in strategy:
                health = 1 + price / maximum
            if shares > 10 or shares < -10 or health > ratio2:
                continue
            strike_prices = f'{options[j].strike_price}/{options[i].strike_price}'
            name = {
                'long_call': lambda: f'{strike_prices} Calls Debit Spread',
                'long_put': lambda: f'{strike_prices} Puts Debit Spread',
                'short_call': lambda: f'{strike_prices} Calls Credit Spread',
                'short_put': lambda: f'{strike_prices} Puts Credit Spread',
            }[strategy]()
            spreads.append(Spread(name, shares, price, maximum, round(health * 100), gamma, theta))
    spreads.sort(key=lambda c: c.health)
    result = []
    for spread in spreads:
        if not result or abs(spread.shares) > abs(result[-1].shares):
            result.append(spread)
    return result


def _get_options_market_data(req, option_list):
    result = [[] for _ in range(len(option_list))]
    for _ in range(10):
        market_data = req.get(f'{HOST}/marketdata/options/',
                              params={'instruments': ','.join(option_list)}).json()['results']
        for i, data in enumerate(market_data):
            if data['delta'] is not None:
                result[i].append(data)
        if all(len(data_list) >= 7 for data_list in result):
            break
        sleep(.1)
    assert min(len(data_list) for data_list in result) > 2
    return [sorted(data_list, key=lambda d: float(d['delta']))[len(data_list) // 2] for data_list in result]


def _paginate(req, url, params=None):
    result = req.get(url, params=params).json()
    if 'results' not in result:
        raise Exception(f'Unexpected response: {result}')
    for item in result['results']:
        yield item
    while result['next']:
        result = get(result['next']).json()
        for item in result['results']:
            yield item
