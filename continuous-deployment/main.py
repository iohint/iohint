from flask import Flask, request, abort
import subprocess
import os

app = Flask(__name__)
REGISTRY_BEARER_TOKEN = os.environ.get('REGISTRY_BEARER_TOKEN')


@app.route('/event', methods=['POST'])
def login():
    if request.headers.get('Authorization') != REGISTRY_BEARER_TOKEN:
        abort(401)
        return None

    for event in request.json['events']:
        if event['action'] != 'push':
            continue
        if event['target']['tag'] != 'latest':
            continue
        if event['target']['repository'] == 'iohint-celery-beat' or \
           event['target']['repository'] == 'iohint-celery-worker':
            print('Deploying celery-beat')
            subprocess.run('/usr/bin/sudo -E '
                           '/usr/src/app/deploy-iohint-app.sh',
                           shell=True)
    return "OK!"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6000)
