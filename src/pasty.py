from bottle import Bottle, request, response, abort, static_file
from html import escape
from time import time
from src.sharelib import create_slug, config
from sys import stderr
from os.path import join
import re
import os
import sys
from datetime import datetime


if not os.path.isdir(config['paste_dir']):
    print('error: the pastebin upload directory does not exist')
    print('try running mkdir -p ' + config['paste_dir'])
    sys.exit(1)

app = Bottle()

MAX_TITLE_SIZE = 200


def get_url_from_req():
    return config['public_url'] + config['pasty_route_prefix']


def write_file(name, content):
    try:
        with open(join(config['paste_dir'], name), 'w') as file:
            file.write(content)
            file.close()
            return True
    except IOError as exception:
        print(f'error while saving file {exception}',
              file=stderr)
        return False


def clean(text):
    return escape(re.sub('[^0-9a-zA-Z ]+', '*', text))


def transform_template(title: str, uploader: str, timestamp: str, content: str) -> str:
    with open('./uploads/paste_template.html') as file:
        html = file.read()

    html = html.replace('<!-- TITLE -->', clean(title))
    html = html.replace('<!-- UPLOADER -->', clean(uploader))
    html = html.replace('<!-- TIMESTAMP -->', timestamp)
    html = html.replace('<!-- CONTENT -->', content)

    return html


@app.get('/')
@app.get('/upload')
def upload_page():
    response.content_type = 'text/plain; charset=utf-8'
    return f'''curl '{get_url_from_req()}upload' -d "uploader=nerd" -d "title=something" -d "text=some text to paste here"'''


@app.get('/<paste>')
def get_paste(paste):
    response.content_type = 'text/plain; charset=utf-8'
    return static_file(f'{paste}.txt', root=config['paste_dir'])


@app.post('/upload', method='POST')
def upload_handler():
    uploader = request.forms.uploader or 'anonymous'
    title = request.forms.title or 'untitled'
    text = request.forms.text
    format = request.forms.format or 'text'

    response.content_type = 'text/plain; charset=utf8'

    if not text:
        abort(400, 'you need to upload something')
        return

    if len(uploader) > MAX_TITLE_SIZE:
        abort(413, 'uploader too long. max is {}'.format(MAX_TITLE_SIZE))
        return

    if len(title) > MAX_TITLE_SIZE:
        abort(413, 'title too long. max is {}'.format(MAX_TITLE_SIZE))
        return

    if len(text) > config['max_paste_size']:
        abort(413, 'upload too big. max is {}'.format(config['max_paste_size']))
        return

    if '\n' in uploader:
        uploader = uploader.replace('\n', '')

    if '\n' in title:
        title = title.replace('\n', '')

    # write actual paste (plain text file)
    name = create_slug()
    if write_file(name + '.txt', text) is False:
        abort(500, 'cant save the plain text file')
        return

    # write html page with some information
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if format == 'html':
        page = transform_template(title, uploader, timestamp, text)
    else:
        page = transform_template(title, uploader, timestamp, escape(text))

    if write_file(name + '.html', page) is False:
        abort(500, 'cant save the html file')
        return

    return get_url_from_req() + name
