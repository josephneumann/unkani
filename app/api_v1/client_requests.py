import requests
from flask import url_for, current_app

url_base = 'http://127.0.0.1:5000'

user = current_app.config.get('UNKANI_ADMIN_EMAIL')
pw = current_app.config.get('UNKANI_ADMIN_PASSWORD')

headers = {
    'content-type': "application/x-www-form-urlencoded",
    'accept': "application/json",
    'cache-control': "no-cache"
}


def get_token():
    url = url_base + url_for('api_v1.new_token')

    if headers.get('authorization'):
        del headers['authorization']
    response = requests.request("POST", url, headers=headers, auth=(user, pw))
    data = response.json()
    return 'Bearer ' + data.get('token')
