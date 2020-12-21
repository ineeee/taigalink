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
from os.path import join
from src.sharelib import create_slug, config


app = Bottle()


def get_url_from_req():
    host = request.get_header('host',
                              f'{config["listen_addr"]}:{config["port"]}')
    scheme = request.get_header('X-Forwarded-Proto',
                                config['scheme'])
    return f'''{scheme}://{host}{config['shortie_route_prefix']}'''


def get_url(slug):
    '''Return the link stored in a file'''
    try:
        with open(join(config['short_dir'], slug), 'r') as link_file:
            return link_file.read()
    # 404
    except FileNotFoundError:
        return ''
    # bubble up all other exceptions


def put_url(slug, url):
    # if the file exists, weirdly unlucky (thus 'w' and not 'x')
    with open(join(config['short_dir'], slug), 'w') as link_file:
        link_file.write(url)


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

    link_slug = create_slug()
    put_url(link_slug, short_url)

    return f'{get_url_from_req()}{link_slug}\n'


@app.get('/')
@app.get('/<short>')
def get_short(short=''):
    if short != '':
        location = get_url(short)
        if not location:
            abort(404, 'No such link')

        response.status = 301
        response.add_header('Location', location)
    else:
        return f'''curl '{get_url_from_req()}short' -d "url=$url"\n'''
