import re
from threading import Thread

from flask import Blueprint, current_app, request

from wallet.util.plivo import send
from wallet.util.swapsy import search_then_create

bp = Blueprint('plivo', __name__)


@bp.route('/message', methods=['POST'])
def message():
    text = request.form['Text']
    current_app.logger.info(f'plivo message received: [{text}] - {request.form}')
    uuid = request.form['MessageUUID']
    if current_app.redis.set(f'plivo:message-dedup:{uuid}', '', ex=3600, nx=True):
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
