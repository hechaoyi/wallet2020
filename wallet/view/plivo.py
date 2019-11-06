from flask import Blueprint, current_app, request

bp = Blueprint('plivo', __name__)


@bp.route('/message', methods=['POST'])
def message():
    current_app.logger.info(f'plivo message received: [{request.form["Text"]}] - {request.form}')
    return 'Message Received'
