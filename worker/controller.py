import time
import logging
from threading import Thread
import RPi.GPIO as GPIO
from datetime import datetime as DT

from dumper import Dumper

logger = logging.getLogger(__name__)


class Controller(Thread):
    def __init__(self, config, event, heating_event, slave_readers):
        super().__init__()
        self._config = config
        self._event = event
        self._heating_event = heating_event
        self._slave_readers = slave_readers
        self._is_heating = False
        self._ts_heating_started = None
        self._ts_heating_ended = None
        self._last_update_ts = None
        self._dumper = Dumper(config)
        GPIO.cleanup()
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self._config['gpio'], GPIO.OUT)

    def run(self):
        logger.debug('Controller started')
        while not self._event.is_set():
            if not self._heating_event.is_set():
                logger.info('Heating disabled.')
                if self._is_heating:
                    self._stop_heating()
                time.sleep(self._config['interval'])
                continue

            [reader.update() for reader in self._slave_readers]
            heating_required = [reader.heating_required for reader in self._slave_readers]
            logger.debug(f'Controller heating required = {heating_required}, is_heating = {self._is_heating}')
            if any(heating_required) and not self._is_heating:
                self._start_heating()
            elif not any(heating_required) and self._is_heating:
                self._stop_heating()

            self._dumper.dump(self._slave_readers)
            time.sleep(self._config['interval'])

    def _start_heating(self):
        logger.debug('Heating started.')
        GPIO.output(self._config['gpio'], GPIO.HIGH)
        self._is_heating = True
        self._ts_heating_started = DT.now()

    def _stop_heating(self):
        logger.debug('Heating stopped.')
        GPIO.output(self._config['gpio'], GPIO.LOW)
        self._is_heating = False
        self._ts_heating_ended = DT.now()

    def get_status(self):
        return {
            'heating': self._is_heating,
            'heating_started': str(self._ts_heating_started),
            'heating_ended': str(self._ts_heating_ended),
        }

