from bottle import Bottle, request, response, abort
from html import escape
from time import time
from src.sharelib import create_slug, config
from sys import stderr
from os.path import join
import re


app = Bottle()

MAX_TITLE_SIZE = 200


def get_url_from_req():
    host = request.get_header('host',
                              f'{config["listen_addr"]}:{config["port"]}')
    scheme = request.get_header('X-Forwarded-Proto',
                                config['scheme'])
    return f'''{scheme}://{host}{config['pasty_route_prefix']}'''


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


@app.get('/')
@app.get('/upload')
def upload_page():
    response.content_type = 'text/plain; charset=utf-8'
    return f'''curl '{get_url_from_req()}upload' -d "uploader=nerd" -d "title=something" -d "text=some text to paste here"'''


@app.post('/upload', method='POST')
def upload_handler():
    uploader = request.forms.uploader or 'anonymous'
    title = request.forms.title or 'untitled'
    text = request.forms.text
    timestamp = int(time())

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
    # they're supposed to be processed by nginx or apache
    page = '<!-- server side includes -->\n'
    page = page + '<!--#set var="paste_uploader" value="{}" -->\n'.format(clean(uploader))
    page = page + '<!--#set var="paste_title" value="{}" -->\n'.format(clean(title))
    page = page + '<!--#set var="paste_timestamp" value="{}" -->\n'.format(timestamp)
    page = page + '<!--#include file="paste_header.html" -->\n'
    page = page + '<div id="paste">{}</div>\n'.format(escape(text))
    page = page + '<!--#include file="paste_footer.html" -->\n'

    if write_file(name + '.html', page) is False:
        abort(500, 'cant save the html file')
        return

    return get_url_from_req() + name
