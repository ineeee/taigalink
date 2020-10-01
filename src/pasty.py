from bottle import Bottle, request, response, abort
from html import escape
from time import time
from src.sharelib import create_slug, config, write_paste
import re

app = Bottle()
PUBLIC_URL = config['public_url'] + config['pasty_route_prefix']


def clean(text):
    return escape(re.sub('[^0-9a-zA-Z ]+', '*', text))


@app.get('/')
@app.get('/upload')
def upload_page():
    response.content_type = 'text/plain; charset=utf-8'
    return f'curl "{PUBLIC_URL}upload" -d "title=something" -d "text=some text to paste here"'


@app.post('/upload', method='POST')
def upload_handler():
    uploader = request.forms.uploader or 'anonymous'
    title = request.forms.title or 'untitled'
    text = request.forms.text
    timestamp = int(time())

    if not text:
        abort(400, 'you need to upload something')
        return

    if len(uploader) > config['max_paste_title']:
        abort(413, 'uploader too long. max is {}'.format(config['max_paste_title']))
        return

    if len(title) > config['max_paste_title']:
        abort(413, 'title too long. max is {}'.format(config['max_paste_title']))
        return

    if len(text) > config['max_paste_size']:
        abort(413, 'upload too big. max is {}'.format(config['max_paste_size']))
        return

    # write actual paste (plain text file)
    name = create_slug()
    if write_paste(name + '.txt', text) is False:
        abort(500, 'cant save the plain text file')
        return

    # write html page with some information
    # feed it to nginx's server side includes
    page = (
        f'<!--#set var="paste_uploader" value="{clean(uploader)}" -->'
        f'<!--#set var="paste_title" value="{clean(title)}" -->'
        f'<!--#set var="paste_timestamp" value="{timestamp}" -->'
        '<!--#include file="paste_header.html" -->\n'
        f'<div id="paste">{escape(text)}</div>\n'
        '<!--#include file="paste_footer.html" -->\n'
    )

    if write_paste(name + '.html', page) is False:
        abort(500, 'cant save the html file')
        return

    response.content_type = 'text/plain; charset=utf8'
    return PUBLIC_URL + name
