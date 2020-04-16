from flask import current_app

from wallet.util.plivo import error_notifier, send

SCOPES = ['https://www.googleapis.com/auth/drive']


def init_app(app):
    @app.cli.command()
    @error_notifier
    def discover_google_drive_files():
        """ Discover Google Drive Files """
        discover_new_files()


def generate_token(client_config):
    from google_auth_oauthlib.flow import InstalledAppFlow
    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    credentials = flow.run_local_server()
    return credentials.to_json()


def init_google_drive_service():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    info = {
        'refresh_token': current_app.config['GOOGLE_DRIVE_REFRESH_TOKEN'],
        'client_id': current_app.config['GOOGLE_DRIVE_CLIENT_ID'],
        'client_secret': current_app.config['GOOGLE_DRIVE_CLIENT_SECRET'],
    }
    credentials = Credentials.from_authorized_user_info(info, SCOPES)
    credentials.refresh(Request())
    return build('drive', 'v3', credentials=credentials)


def discover_new_files():
    drive = init_google_drive_service()
    folder_id = current_app.config['GOOGLE_DRIVE_FOLDER_ID']
    request = drive.files().list(q=f'\'{folder_id}\' in parents', fields="files(id, name)")
    # {'files': [{'id': '1b_mozqUvDEyHQDHBkLfU5zJG4qCVS2gA', 'name': 'WishCash_10.1.19-1.31.20.xlsm'}]}
    for file in request.execute()['files']:
        file_id, file_name = file['id'], file['name']
        if current_app.redis.setnx(f'google-drive:file-dedup:{file_id}', file_name):
            current_app.logger.info(f'new file discovered: {file_name}')
            send(f'发现新文件\n{file_name}')
