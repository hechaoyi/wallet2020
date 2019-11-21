import re

from flask import Blueprint, current_app, request
from flask.json import dumps

bp = Blueprint('plivo', __name__)


@bp.route('/message', methods=['POST'])
def message():
    text = request.form['Text']
    current_app.logger.info(f'plivo message received: [{text}] - {request.form}')
    uuid = request.form['MessageUUID']
    if current_app.redis.set(f'plivo:message-dedup:{uuid}', dumps(request.form), ex=3600, nx=True):
        m = re.match(r'(\d+)-(\d+)', text)
        if m:
            from wallet.util.swapsy import create_with_notification
            current_app.queue.enqueue(create_with_notification, int(m[1]), int(m[2]), job_timeout=1800)
    return 'Message Received'
