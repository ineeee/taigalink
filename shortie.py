#!/usr/bin/env python3
# Copyright (C) 2020  Anthony DeDominic <adedomin@gmail.com>

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from os import environ, path
from sys import stderr
from bottle import get, post, request, response, abort, run
from random import choices
from string import ascii_letters, digits
from collections import OrderedDict
import json


class LRU():
    def __init__(self, size):
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


CONFIG_PATHS = [path.join(environ.get('XDG_CONFIG_HOME',
                                      environ.get('HOME', './')),
                          'shortie-config.json'),
                '/etc/shortie-conf.json']

DEFAULT_CONFIG = {'short_id_size': 8,
                  'scheme': 'http',
                  'listen_addr': '0.0.0.0',
                  'port': 1997}

URL_CACHE = LRU(65536)

config = DEFAULT_CONFIG.copy()
for config_path in CONFIG_PATHS:
    try:
        with open(config_path, 'r') as c:
            config = {**DEFAULT_CONFIG, **json.load(c)}
    except FileNotFoundError:
        pass

if not config:
    print(f'WARNING: No config loaded; using defaults.',
          file=stderr)


def get_url_from_req():
    host = request.get_header('host',
                              f'{config["listen_addr"]}:{config["port"]}')
    scheme = request.get_header('X-Forwarded-Proto',
                                config['scheme'])
    return f'{scheme}://{host}'


@post('/short')
def shorten():
    short_url = request.forms.get('url', '')
    if short_url == '':
        abort(400, 'url must be non zero')
    elif len(short_url) > 4096:
        abort(400, 'url too long')
    elif '\n' in short_url or '\r' in short_url:
        abort(400, 'url not valid')
    elif short_url[:7] != 'http://' and short_url[:8] != 'https://':
        abort(400, 'url must have a HTTP uri schema')

    link_id = ''.join(choices(ascii_letters + digits,
                              k=config['short_id_size']))
    URL_CACHE.put(link_id, short_url)

    return f'{get_url_from_req()}/{link_id}\n'


@get('/')
@get('/<short>')
def get_short(short=''):
    if short != '':
        location = URL_CACHE.get(short)
        if not location:
            abort(404, 'No such link')

        response.status = 301
        response.add_header('Location', location)
    else:
        return f'''curl '{get_url_from_req()}/short' -d "url=$url"\n'''


if __name__ == '__main__':
    run(host=config['listen_addr'],
        port=config['port'])
