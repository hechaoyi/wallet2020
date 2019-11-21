from functools import wraps
from hashlib import md5

from flask import current_app
from requests import post
from requests.auth import HTTPBasicAuth


def send(text):
    post(f'https://api.plivo.com/v1/Account/{current_app.config["PLIVO_ID"]}/Message/',
         auth=HTTPBasicAuth(
             current_app.config['PLIVO_ID'],
             current_app.config['PLIVO_TKN']
         ),
         data={
             'src': current_app.config['PLIVO_SRC'],
             'dst': current_app.config['PLIVO_DST'],
             'text': text
         })


def error_notifier(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            text = '{}.{}\n{!r}'.format(func.__module__, func.__name__, e)
            tid = md5(text.encode('utf-8')).hexdigest()
            if current_app.redis.set(f'plivo:error-dedup:{tid}', text, ex=3600 * 4, nx=True):
                send(text)
            raise

    return wrapper
