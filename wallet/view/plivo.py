import re
from threading import Thread

from flask import Blueprint, current_app, request

from wallet.util.plivo import send
from wallet.util.swapsy import search_then_create

bp = Blueprint('plivo', __name__)
_uuid_dedup = set()


@bp.route('/message', methods=['POST'])
def message():
    text = request.form['Text']
    current_app.logger.info(f'plivo message received: [{text}] - {request.form}')
    uuid = request.form['MessageUUID']
    if uuid not in _uuid_dedup:
        _uuid_dedup.add(uuid)
        m = re.match(r'(\d+)-(\d+)', text)
        if m:
            def swapsy(app):
                with app.app_context():
                    trade = search_then_create(int(m[1]), int(m[2]), 20)
                    if trade:
                        send(f'匹配成功\n${trade.amount} -> ¥{trade.receive_amount}\n{trade.actual_rate}')
                    else:
                        send('匹配超时')

            Thread(target=swapsy, args=(current_app._get_current_object(),)).start()
    return 'Message Received'
