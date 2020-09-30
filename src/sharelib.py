from string import ascii_letters, digits
from random import choices
from os.path import join
from os import environ
import json
from sys import stderr
from collections import OrderedDict


SLUG_CHAR = ascii_letters + digits

# Parse config
CONFIG_PATHS = [join(environ.get('XDG_CONFIG_HOME',
                                 environ.get('HOME', './')),
                     'taigalink.json'),
                '/etc/taigalink.json',
                './taigalink.json']

DEFAULT_CONFIG = {'slug_size': 6,
                  'link_storage_size': 8196,
                  'max_paste_size': 1024 * 8,
                  'paste_dir': '/var/www/taigalink/p/',
                  'shortie_route_prefix': '/s/',  # must end with /
                  'pasty_route_prefix': '/p/',  # must end with /
                  'scheme': 'http',
                  'listen_addr': '127.0.0.1',
                  'port': 1997}


config = DEFAULT_CONFIG.copy()
config_loaded = False
for config_path in CONFIG_PATHS:
    try:
        with open(config_path, 'r') as c:
            config = {**DEFAULT_CONFIG, **json.load(c)}
            config_loaded = True
            break
    except FileNotFoundError:
        pass

if not config_loaded:
    print(f'WARNING: No config loaded; using defaults.',
          file=stderr)
    try:
        with open('./taigalink.json', 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
            print(f'WARNING: wrote default config to working directory.',
                  file=stderr)
    except Exception:
        pass

if not config['shortie_route_prefix'].endswith('/') or \
   not config['shortie_route_prefix'].startswith('/'):
    raise RuntimeError('shortie Route Prefix must start and end with a /')
if not config['pasty_route_prefix'].endswith('/') or \
   not config['pasty_route_prefix'].startswith('/'):
    raise RuntimeError('pasty Route Prefix must start and end with a /')


def create_slug(length=config['slug_size']):
    return ''.join(choices(SLUG_CHAR, k=length))


class LRU():
    def __init__(self, size=config['link_storage_size']):
        self._lru = OrderedDict()
        self._len = size

    def __len__(self):
        return len(self._lru)

    def get(self, key, default=None):
        try:
            self._lru.move_to_end(key)
            return self._lru[key]
        except KeyError:
            return default

    def put(self, key, value):
        self._lru[key] = value
        if len(self._lru) > self._len:
            self._lru.popitem(last=False)
