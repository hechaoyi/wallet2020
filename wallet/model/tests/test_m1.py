from wallet.model.m1 import M1Portfolio


def _inspect(current, previous=None):
    assert current.value == round(current.start_value + current.net_cash_flow + current.capital_gain, 2)
    assert current.gain == round(current.capital_gain + current.dividend_gain, 2)
    assert current.rate == round(current.gain / (current.start_value + current.net_cash_flow) * 100, 2)
    if previous:
        assert current.start_value == previous.value


def test_portfolio_inspection(context):
    assert context
    ps = M1Portfolio.query.order_by(M1Portfolio.date).all()
    _inspect(ps[0])
    for i in range(1, len(ps)):
        _inspect(ps[i], ps[i - 1])
