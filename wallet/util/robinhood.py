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
    req = _init_request_session()

    positions = get_option_positions(req, [])
    for item in sorted(positions.values(), key=lambda e: e.symbol):
        shares = sum(pos.shares for pos in item.positions)
        output(f'{item.symbol} '
               f'[Gain {sum(pos.gain for pos in item.positions)}, Theta {sum(pos.theta for pos in item.positions):.2f},'
               f' Shares {shares:.1f}, Gamma {sum(pos.gamma for pos in item.positions):.2f},'
               f' Price {item.price}, Value {shares * item.price:.0f},'
               f' Collateral {sum(pos.maximum for pos in item.positions)}]:')
        if verbose:
            for pos in sorted(item.positions, key=lambda e: e.name):
                output(f' - {pos.name} '
                       f'[Gain {pos.gain}, Theta {pos.theta},'
                       f' Shares {pos.shares}, Gamma {pos.gamma},'
                       f' Health {pos.health}%]')

    output()
    dd = defaultdict(lambda: [0, 0, 0, 0])
    for item in positions.values():
        for pos in item.positions:
            dd[pos.expiry][0] += pos.gain
            dd[pos.expiry][1] += pos.theta
            dd[pos.expiry][2] += abs(pos.shares) * item.price
            dd[pos.expiry][3] += pos.maximum
    for expiry in sorted(dd):
        output(f'Week {expiry}\'s Gain: {dd[expiry][0]}, Theta: {dd[expiry][1]:.2f},'
               f' Value: {dd[expiry][2]:.0f}, Collateral: {dd[expiry][3]}')

    today = datetime.today()
    days = {0: 4, 1: 3, 2: 2, 3: 1, 4: 7, 5: 6, 6: 5}[today.weekday()]
    expiry_date = (today + timedelta(days=days)).strftime('%m/%d')
    expiry_date = {
        '07/03': '07/02',
    }.get(expiry_date, expiry_date)
    aapl = sum(pos.shares for pos in positions['AAPL'].positions
               if pos.expiry > expiry_date) * positions['AAPL'].price
    msft = sum(pos.shares for pos in positions['MSFT'].positions
               if pos.expiry > expiry_date) * positions['MSFT'].price
    qqq = sum(pos.shares for pos in positions['QQQ'].positions
              if pos.expiry > expiry_date) * positions['QQQ'].price
    amq = aapl + msft + qqq
    spy = sum(-pos.shares for pos in positions['SPY'].positions
              if pos.expiry > expiry_date) * positions['SPY'].price
    output(f'AAPL:MSFT:QQQ:SPY    {aapl / amq * 100:.0f}:{msft / amq * 100:.0f}'
           f':{qqq / amq * 100:.0f}:{spy / amq * 100:.0f}')

    def list_spreads(symbol, strategy, price, chain, ratio1, intervals, expiry_date):
        expiry_date = expiry_date.strftime('%Y-%m-%d')
        output(f'{symbol} candidates: [stock price: {price}, expiry date: {expiry_date}]')
        spreads = find_option_spreads(req, strategy, chain, expiry_date, price, ratio1, intervals)
        for spread in spreads:
            output(f' - {spread.name} [Shares {spread.shares}, Price {spread.price}'
                   f', Maximum {spread.maximum}, Health {spread.health}%')

    output()
    days = 28 + {0: 4, 1: 3, 2: 2, 3: 1, 4: 7, 5: 6, 6: 5}[today.weekday()]
    buy_date = (today + timedelta(days=days))
    buy_date_str = buy_date.strftime('%m/%d')
    if not any(pos.expiry == buy_date_str for pos in positions['AAPL'].positions):
        list_spreads('AAPL', 'short_put', positions['AAPL'].price, positions['AAPL'].chain, .55, [5.0], buy_date)
    if not any(pos.expiry == buy_date_str for pos in positions['MSFT'].positions):
        list_spreads('MSFT', 'short_put', positions['MSFT'].price, positions['MSFT'].chain, .55, [5.0], buy_date)
    if not any(pos.expiry == buy_date_str for pos in positions['QQQ'].positions):
        list_spreads('QQQ',  'short_put', positions['QQQ'].price,  positions['QQQ'].chain,  .60, [3.0], buy_date)
    if not any(pos.expiry == buy_date_str for pos in positions['SPY'].positions):
        list_spreads('SPY', 'short_call', positions['SPY'].price,  positions['SPY'].chain,  .65, [2.0], buy_date)


def get_summary_with_notif():
    def output(line=None):
        notification[0] += f'{line or ""}\n'

    notification = ['']
    get_summary(output, verbose=False)
    from wallet.util.plivo import send
    send(notification[0])


def get_option_positions(req, additions):
    Position = namedtuple('Position', 'name gain shares health gamma theta expiry maximum')
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

        expiry = datetime.fromisoformat(legs[0]['expiration_date']).strftime('%m/%d')
        expiring_today = expiry == datetime.today().strftime('%m/%d')
        market_data = _get_options_market_data(req, [leg['option'] for leg in legs], allow_none=expiring_today)
        maximum = round(abs(float(legs[0]['strike_price']) - float(legs[1]['strike_price'])) * 100 * quantity)
        strike_prices = '/'.join(str(float(leg['strike_price'])) for leg in legs)
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
                if not expiring_today:
                    shares += float(data['delta']) * 100 * quantity
                    gamma += float(data['gamma']) * quantity * price  # the change of shares per 1%
                    theta += float(data['theta']) * 100 * quantity  # the change of equity per day
            else:
                equity -= round(float(data['mark_price']) * 100 * quantity)
                if not expiring_today:
                    shares -= float(data['delta']) * 100 * quantity
                    gamma -= float(data['gamma']) * quantity * price  # the change of shares per 1%
                    theta -= float(data['theta']) * 100 * quantity  # the change of equity per day
        cost = round(float(position['average_open_price']) * quantity)  # always positive
        gain = equity - cost
        health = equity / maximum
        if position['direction'] == 'credit':
            gain = equity + cost
            health = 1 + equity / maximum
        positions[symbol].positions.append(Position(name, gain, round(shares, 1),
                                                    round(health * 100), round(gamma, 2), round(theta, 2),
                                                    expiry, maximum))

    for symbol in additions:
        if symbol not in positions:
            price = float(req.get(f'{HOST}/marketdata/quotes/{symbol}/').json()['last_trade_price'])
            chain = req.get(f'{HOST}/instruments/', params={'symbol': symbol}).json()['results'][0]['tradable_chain_id']
            positions[symbol] = SymbolPositions(symbol, [], price, chain)

    return positions


def find_option_spreads(req, strategy, chain_id, expiry_date, stock_price, ratio1, intervals):
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
            shares = (options[j].delta - options[i].delta) * 100
            price = round(options[j].mark_price - options[i].mark_price, 2)
            maximum = round(abs(options[j].strike_price - options[i].strike_price), 2)
            if maximum not in intervals:
                continue
            gamma = round((options[j].gamma - options[i].gamma) * stock_price, 2)
            theta = round((options[j].theta - options[i].theta) * 100, 2)
            health = price / maximum
            if 'short' in strategy:
                health = 1 + price / maximum
            strike_prices = f'{options[j].strike_price}/{options[i].strike_price}'
            name = {
                'long_call': lambda: f'{strike_prices} Calls Debit Spread',
                'long_put': lambda: f'{strike_prices} Puts Debit Spread',
                'short_call': lambda: f'{strike_prices} Calls Credit Spread',
                'short_put': lambda: f'{strike_prices} Puts Credit Spread',
            }[strategy]()
            spreads.append(Spread(name, round(shares, 1), price, maximum, round(health * 100), gamma, theta))
    spreads.sort(key=lambda c: (c.maximum, c.health))
    interval_backlogs = 3  # if len(intervals) > 1 else 4
    result = []
    for spread in spreads:
        if len(result) < interval_backlogs or result[-interval_backlogs].maximum != spread.maximum:
            result.append(spread)
    return result


def get_portfolio():
    req = _init_request_session()
    json = req.get(f'{HOST}/portfolios/').json()
    if 'results' not in json:
        raise ValueError(json['detail'])
    result = json['results'][0]
    Portfolio = namedtuple('Portfolio', 'value start_value')
    return Portfolio(float(result['equity']), float(result['equity_previous_close']))


def _init_request_session():
    req = Session()
    req.headers['Authorization'] = f'Bearer {current_app.config["RH_TOKEN"]}'
    req.headers['User-Agent'] = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36'
                                 ' (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36')
    req.headers['Referer'] = 'https://robinhood.com/'
    req.headers['Cache-Control'] = 'no-cache'
    req.headers['Pragma'] = 'no-cache'
    return req


def _get_options_market_data(req, option_list, allow_none=False):
    result = [[] for _ in range(len(option_list))]
    for _ in range(15):
        market_data = req.get(f'{HOST}/marketdata/options/',
                              params={'instruments': ','.join(option_list)}).json()['results']
        for i, data in enumerate(market_data):
            if data['delta'] is not None or allow_none:
                result[i].append(data)
        if all(len(data_list) >= 11 for data_list in result):
            break
        sleep(.1)
    assert min(len(data_list) for data_list in result) > 2
    return [sorted(data_list, key=lambda d: float(d['delta']) if d['delta'] else 0)[len(data_list) // 2] for data_list in result]


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
