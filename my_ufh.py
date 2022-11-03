import logging
import sys
import json
from pathlib import Path
from os import environ
from flask import Flask, jsonify, render_template
from threading import Event

import requests

from slave_reader import SlaveReader
from worker.controller import Controller


def setup_logging():
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    log_level = environ.get("LOG_LVL", "dump")
    if log_level == "dump":
        level = logging.DEBUG
    elif log_level == "info":
        level = logging.INFO
    elif log_level == "error":
        level = logging.ERROR
    elif log_level == "warning":
        level = logging.WARNING
    else:
        logging.error('"%s" is not correct log level', log_level)
        sys.exit(1)
    if getattr(setup_logging, "_already_set_up", False):
        logging.warning("Logging already set up")
    else:
        logging.basicConfig(format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s", level=level)
        setup_logging._already_set_up = True


def create_app():
    app = Flask(__name__, static_folder='templates')

    setup_logging()
    config = json.loads(Path('config.json').read_text())
    event = Event()
    heating_event = Event()
    heating_event.set()

    slave_readers = [SlaveReader(cfg) for cfg in config['slaves']]

    controller = Controller(config, event, heating_event, slave_readers)
    controller.start()

    app.heating_event = heating_event
    app.controller = controller
    app.app_config = config

    return app


app = create_app()


@app.route('/enable')
def enable_heating():
    app.heating_event.set()
    return 'ok'


@app.route('/disable')
def disable_heating():
    app.heating_event.clear()
    return 'ok'


@app.route('/status')
def status():
    return jsonify(app.controller.get_status())


@app.route('/table')
def table():
    state = []
    for slave in app.app_config['slaves']:
        try:
            r = requests.get(slave['address'] + '/heating', timeout=5.0)
            if r.status_code != 200:
                continue
            for zone_id, zone_state in r.json().items():
                state.append({
                    'name': zone_state['location'][0],
                    'temperature': zone_state['temperature'],
                    'required_temperature': zone_state['required_temperature'],
                    'heating': zone_state['heating'],
                    'heating_started': zone_state['heating_started'],
                })

        except Exception as e:
            print(e)

    return render_template('table.html', title='status', locations=state)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
