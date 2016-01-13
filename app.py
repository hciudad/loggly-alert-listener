import os
from flask import Flask, request
import json
import logging
import requests

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')


class LeanKit_Config(object):
    LK_USERNAME = os.environ['LK_USERNAME']
    LK_PASSWORD = os.environ['LK_PASSWORD']
    LK_CARD_TYPE_ID = os.environ.get('LK_CARD_TYPE_ID')
    LK_URL_BASE = 'https://{}.leankit.com'.format(os.environ['LK_DOMAIN'])
    LK_ADD_CARD_PATH = ('kanban/api/board/{board_id}/AddCard/'
                        'Lane/{lane_id}/Position/0')

app.config.from_object(LeanKit_Config)


@app.route('/card', methods=['POST'])
def create_leankit_card():
    secret_key = request.args.get('k')
    board_id = request.args.get('board_id')
    lane_id = request.args.get('lane_id')
    assigned_user_ids = request.args.getlist('assigned_user_id')

    if not app.secret_key or secret_key != app.secret_key:
        print 'Bad secret key: {}'.format(secret_key)
        return 'Not found', 404

    if not board_id:
        print 'Missing board id'
        return 'Missing board id', 400

    if not lane_id:
        print 'Missing lane id'
        return 'Missing lane id', 400

    try:
        loggly_alert = json.loads(request.get_data())
        if app.debug:
            print loggly_alert

        lk_card = {
            "Title": "{alert_name} (Hits: {num_hits}) [{start_time}]".format(
                **loggly_alert),
            "TypeId": (int(app.config['LK_CARD_TYPE_ID'])
                       if app.config['LK_CARD_TYPE_ID'] else None),
            "Description": "\n\n".join(
                loggly_alert.get('recent_hits', ['No data'])),
            "Priority": 1,
            "Size": 0,
            "AssignedUserIds": assigned_user_ids,
            "ExternalCardID": "Loggly Alerts",
            "ExternalSystemName": "Loggly Alert Search",
            "ExternalSystemUrl": loggly_alert['search_link'],
            "IsBlocked": False
        }

        add_card_url_tmpl = "{LK_URL_BASE}/{LK_ADD_CARD_PATH}".format(
            **app.config)
        res = requests.post(
            add_card_url_tmpl.format(board_id=board_id, lane_id=lane_id),
            data=lk_card,
            auth=(app.config['LK_USERNAME'], app.config['LK_PASSWORD']))
        res.raise_for_status()
    except Exception, ex:
        logging.exception(ex)
        raise

    return ':)'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)),
            debug=os.environ.get('DEBUG', False))
