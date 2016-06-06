import os
from flask import Flask, request
import json
import logging
import requests

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')

class ClubHouse_Config(object):
    CH_URL_BASE = 'https://api.clubhouse.io'
    CH_ADD_STORY_PATH = 'api/v1/stories'
    CH_API_TOKEN = os.environ.get('CH_API_TOKEN')


app.config.from_object(ClubHouse_Config)


@app.route('/card', methods=['POST'])
def create_clubhouse_story():
    secret_key = request.args.get('k')
    project_id = request.args.get('project_id', type=int)
    workflow_state_id = request.args.get('workflow_state_id', type=int)
    assigned_user_ids = request.args.getlist('assigned_user_id')

    if not app.secret_key or secret_key != app.secret_key:
        print 'Bad secret key: {}'.format(secret_key)
        return 'Not found', 404

    if not project_id:
        print 'Missing project id'
        return 'Missing project id', 400

    if not workflow_state_id:
        print 'Missing workflow state id'
        return 'Missing workflow state id', 400

    try:
        loggly_alert = json.loads(request.get_data())
        if app.debug:
            print loggly_alert

        desc = "\n\n".join([r.strip() for r in
                           loggly_alert.get('recent_hits', ['No data'])])
        ch_card = {
            "name": "{alert_name} (Hits: {num_hits}) [{start_time}]".format(
                **loggly_alert),
            "project_id": project_id,
            "workflow_state_id": workflow_state_id,
            "story_type": "bug",
            "owner_ids": assigned_user_ids,
            "follower_ids": assigned_user_ids,
            "description": "```\n{}\n```".format(desc)

        }
        if app.debug:
            print ch_card

        add_card_url_tmpl = "{CH_URL_BASE}/{CH_ADD_STORY_PATH}".format(
            **app.config)
        res = requests.post(
            add_card_url_tmpl,
            json=ch_card,
            params={'token': app.config['CH_API_TOKEN']})
        res.raise_for_status()
    except Exception, ex:
        logging.exception(ex)
        raise

    return ':)'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)),
            debug=os.environ.get('DEBUG', False))
