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

from bottle import Bottle, request, response, abort
from src.sharelib import LRU, create_slug, config


app = Bottle()

URL_CACHE = LRU()


def get_url_from_req():
    host = request.get_header('host',
                              f'{config["listen_addr"]}:{config["port"]}')
    scheme = request.get_header('X-Forwarded-Proto',
                                config['scheme'])
    return f'''{scheme}://{host}{config['shortie_route_prefix']}'''


@app.post('/short')
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

    link_id = create_slug()
    URL_CACHE.put(link_id, short_url)

    return f'{get_url_from_req()}{link_id}\n'


@app.get('/')
@app.get('/<short>')
def get_short(short=''):
    if short != '':
        location = URL_CACHE.get(short)
        if not location:
            abort(404, 'No such link')

        response.status = 301
        response.add_header('Location', location)
    else:
        return f'''curl '{get_url_from_req()}short' -d "url=$url"\n'''
