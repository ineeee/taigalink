from string import ascii_letters, digits
from random import choices
import json
from os.path import join
from collections import OrderedDict


DEFAULT_CONFIG = {'slug_size': 6,
                  'slug_chars': ascii_letters + digits,
                  'link_storage_size': 8196,
                  'max_paste_size': 1024 * 8,
                  'max_paste_title': 200,
                  'paste_dir': 'uploads/',
                  'shortie_database': 'urls.json',
                  'shortie_route_prefix': '/s/',  # must start and end with /
                  'pasty_route_prefix': '/p/',  # must start and end with /
                  'public_url': 'http://paste.wolowolo.com',  # no / at the end!
                  'listen_addr': '127.0.0.1',
                  'port': 1997}


config = DEFAULT_CONFIG.copy()
try:
    with open('./config.json', 'r') as c:
        config = {**DEFAULT_CONFIG, **json.load(c)}
except FileNotFoundError:
    print('WARNING: no config.json exists, using defaults')
    try:
        with open('./config.json', 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
            print('WARNING: wrote defaults to config.json')
    except Exception:
        pass
    pass

if not config['shortie_route_prefix'].endswith('/') or not config['shortie_route_prefix'].startswith('/'):
    raise RuntimeError('shortie Route Prefix must start and end with a /')
if not config['pasty_route_prefix'].endswith('/') or not config['pasty_route_prefix'].startswith('/'):
    raise RuntimeError('pasty Route Prefix must start and end with a /')
if config['public_url'].endswith('/'):
    raise RuntimeError('public_url must not end with a path')


def create_slug(length=config['slug_size']):
    return ''.join(choices(config['slug_chars'], k=length))


def write_paste(name, content):
    try:
        with open(join(config['paste_dir'], name), 'w') as file:
            file.write(content)
            file.close()
            return True
    except IOError as exception:
        print(f'error while saving file {exception}')
        return False


def write_urls(data):
    try:
        with open(config['shortie_database'], 'w') as f:
            json.dump(data, f)
    except IOError as exception:
        print('ERROR: cant write shortie db')
        print(exception)
        return False

    return True


def load_urls():
    try:
        with open(config['shortie_database'], 'r') as c:
            return json.load(c)
    except FileNotFoundError:
        print('WARNING: shortie db is empty (ignore if first boot)')
        return {}
