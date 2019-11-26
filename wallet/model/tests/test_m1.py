from wallet.model.m1 import M1Portfolio


def test_portfolio_inspection(context):
    assert context

    def test(name):
        ps = M1Portfolio.query.filter_by(name=name).order_by(M1Portfolio.date).all()
        if not ps:
            return
        ps[0].inspect()
        for i in range(1, len(ps)):
            ps[i].inspect(ps[i - 1])

    test('Individual')
    test('Roth IRA')
