import logging
import requests


logger = logging.getLogger(__name__)


class SlaveReader:
    def __init__(self, config):
        self._config = config
        self._address = None
        self._name = None
        self._state_known = False
        self._current_state = None
        self._heating_required = False
        self._initialize()

    def _initialize(self):
        self._address = self._config['address']
        self._name = self._config['name']

    def get_name(self):
        return self._name

    def get_state(self):
        return self._current_state

    @property
    def heating_required(self):
        if not self._state_known:
            logger.debug(f'State not known, heating disabled on {self._name}.')
            return False
        return self._heating_required

    def update(self):
        try:
            req = requests.get(self._address + '/heating', timeout=5.0)
        except Exception as e:
            logger.error(str(e))
            self._state_known = False
            return
        if req.status_code != 200:
            self._state_known = False
            return

        js = req.json()
        self._current_state = js
        self._state_known = True
        self._heating_required = any(zone['heating'] for zone in js.values())
        zones_required_heating = [zone['location'] for zone in js.values() if zone['heating']]
        logger.debug(f'{self._name} heating required = {self._heating_required}.')
        logger.debug(f'Zones required heating in {self._name} = {zones_required_heating}.')
