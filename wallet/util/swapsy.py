from collections import namedtuple
from time import sleep

from click import argument
from flask import current_app
from requests import session
from simplejson import loads

HOST = 'https://theswapsy.com'
Trade = namedtuple('Trade', 'trade_id amount receive_amount rate actual_rate')
swapsy_session = session()
swapsy_session.csrf = None
swapsy_session.block = None


def search_then_create(lo, hi, tries=1):
    while True:
        trade = search(lo, hi)
        if trade:
            create(trade)
            return trade
        tries -= 1
        if tries == 0:
            return None
        current_app.logger.info('Swapsy no match, will retry later')
        sleep(60)


def init_app(app):
    @app.cli.command()
    @argument('lo', default=400)
    @argument('hi', default=600)
    def create_swapsy_trade(lo, hi):
        """ Create Swapsy Trade """
        search_then_create(lo, hi)


def search(lo, hi):
    _access_trade2_page()
    swapsy_session.block['sendAmount'] = (lo + hi) >> 1
    swapsy_session.block['sendCurrency'] = 'USD'
    swapsy_session.block['receiveCurrency'] = 'CNY'
    data = {'_frontendCSRF': swapsy_session.csrf, **_json_to_form(swapsy_session.block, 'block', {})}
    swapsy_session.block = swapsy_session.post(HOST + '/trade2/search', data=data).json()
    trades = [
        Trade(
            item['tradeId'], item['amount'], item['receiveAmount'], item['rate'],
            round(item['receiveAmount'] / item['amount'], 4)
        ) for item in swapsy_session.block['extra']['tradeSearch']['zelle']['items']
    ]
    current_app.logger.info('Swapsy matches:\n%s', '\n'.join(str(t) for t in trades))
    return max(
        (trade for trade in trades if lo <= trade.amount <= hi and trade.actual_rate >= trade.rate),
        key=lambda t: t.actual_rate, default=None
    )


def create(trade):
    swapsy_session.block['sendWallet'] = 'zelle'
    swapsy_session.block['receiveWallets'] = []
    swapsy_session.block['matchedTradeId'] = trade.trade_id
    swapsy_session.block['sendAmount'] = trade.amount
    swapsy_session.block['receiveAmount'] = trade.receive_amount
    swapsy_session.block['selectedExchangeRate'] = trade.rate
    swapsy_session.block['isOwnRequest'] = False
    swapsy_session.block['extra']['isRecommended'] = False
    data = {'_frontendCSRF': swapsy_session.csrf, **_json_to_form(swapsy_session.block, 'block', {})}
    assert swapsy_session.post(HOST + '/trade2/init', data=data).json()['extra']['status'] == 'success'
    _access_trade2_page()
    swapsy_session.block['receiveWallets'] = 'wxpay,alipay'
    data = {'_frontendCSRF': swapsy_session.csrf, **_json_to_form(swapsy_session.block, 'block', {})}
    assert swapsy_session.post(HOST + '/trade2/create', data=data).json()['extra']['status'] == 'success'
    current_app.logger.info(f'Swapsy created:  {trade}')


def _access_trade2_page():
    resp = swapsy_session.get(HOST + '/trade2')
    if resp.url == HOST + '/login':
        data = {
            '_frontendCSRF': _regex_search(resp, b'csrf-token', b'content="([^"]+)'),
            'LoginForm[credential]': current_app.config['SWAPSY_USERNAME'],
            'LoginForm[password]': current_app.config['SWAPSY_PASSWORD'],
        }
        resp = swapsy_session.post(HOST + '/login', data=data)
        current_app.logger.info('Swapsy logged in')
    assert resp.url == HOST + '/trade2'
    swapsy_session.csrf = _regex_search(resp, b'csrf-token', b'content="([^"]+)')
    swapsy_session.block = loads(_regex_search(resp, b'block: {', b'block: ({.+}),$'))


def _regex_search(resp, keyword, pattern):
    from re import search
    return search(
        pattern,
        next(line for line in resp.iter_lines() if keyword in line)
    ).group(1)


def _json_to_form(json, prefix, result):
    for key, value in json.items():
        prop = '{}[{}]'.format(prefix, key)
        if value is None:
            result[prop] = ''
        elif isinstance(value, bool):
            result[prop] = 'true' if value else 'false'
        elif isinstance(value, (int, float, str)):
            result[prop] = value
        elif isinstance(value, dict):
            _json_to_form(value, prop, result)
        elif isinstance(value, list):
            for i, e in enumerate(value):
                _json_to_form(e, '{}[{}]'.format(prop, i), result)
        else:
            assert 0
    return result