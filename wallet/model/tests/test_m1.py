from wallet.model.m1 import M1Portfolio


def test_portfolio_inspection(context):
    assert context
    ps = M1Portfolio.query.order_by(M1Portfolio.date).all()
    ps[0].inspect()
    for i in range(1, len(ps)):
        ps[i].inspect(ps[i - 1])
