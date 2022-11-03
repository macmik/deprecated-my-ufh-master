from datetime import datetime as DT


class Dumper:
    DUMP_FILE_NAME = 'heating.csv'

    def __init__(self, config):
        self._config = config

    def dump(self, slave_readers):
        if not self._config['dump_enabled']:
            return

        data_to_dump = [str(DT.now())]
        for slave_reader in slave_readers:
            state = slave_reader.get_state()
            if state is None:
                return
            for zone_state in state.values():
                data_to_dump += zone_state['location']
                data_to_dump += str(int(zone_state['heating']))

        with open(self.DUMP_FILE_NAME, 'a') as fo:
            fo.write(','.join(data_to_dump + ['\n']))
