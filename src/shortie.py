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

from time import time
from bottle import Bottle, request, response, abort
from src.sharelib import create_slug, config, write_urls, load_urls


app = Bottle()
PUBLIC_URL = config['public_url'] + config['shortie_route_prefix']

URL_CACHE = load_urls()


def store_short(url, id=create_slug()):
    # if collision, try again with longer slug
    if id in URL_CACHE:
        return store_short(url, create_slug(config['slug_size'] + 2))

    timestamp = int(time())
    URL_CACHE[id] = [timestamp, url]

    if write_urls(URL_CACHE):
        return id
    else:
        return False


@app.post('/short')
def shorten():
    long_url = request.forms.get('url', '')
    if long_url == '':
        abort(400, 'url must be non zero')
    elif len(long_url) > 4096:
        abort(400, 'url too long')
    elif '\n' in long_url or '\r' in long_url or ' ' in long_url:
        abort(400, 'url not valid: it has whitespace')
    elif long_url[:7] != 'http://' and long_url[:8] != 'https://':
        abort(400, 'url must have a HTTP uri schema')  # why?

    id = store_short(long_url)

    if id is False:
        abort(500, 'cant shorten the url')

    return PUBLIC_URL + id


@app.get('/')
@app.get('/<short>')
def get_short(short=''):
    if short == '':
        return f'''curl '{PUBLIC_URL}short' -d "url=$url"\n'''

    location = URL_CACHE.get(short)
    if not location:
        abort(404, 'No such link')

    response.status = 301
    response.content_type = 'text/plain'
    response.add_header('Location', location)
    return 'Redirecting...'
