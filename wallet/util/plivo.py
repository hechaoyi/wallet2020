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
