from bottle import route, request, run, response, abort
import random
from html import escape
from time import time
import re

URL_CHARS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
MAX_TITLE_SIZE = 200
MAX_PASTE_SIZE = 1024 * 4


def create_slug(length=6):
    return ''.join(random.choices(URL_CHARS, k=length))


def write_file(name, content):
    try:
        file = open('uploads/' + name, 'w')
        file.write(content)
        file.close()
        return True
    except IOError as exception:
        print('error while saving file', exception)
        return False


def clean(text):
    return escape(re.sub('[^0-9a-zA-Z ]+', '*', text))


@route('/p/')
@route('/p/upload')
def upload_page():
    # some dumb form
    return '''
        <meta charset="utf-8">
        <title>upload pastes</title>
        <h2>upload pastes</h2>
        <style>
            body { max-width: 500px; margin: 0 auto; }
            input, textarea { width: 100% }
            div { margin: 1em 0 }
        </style>
        <form action="/p/upload" method="post">
            <div>Uploader: <input name="uploader" type="text" /></div>
            <div>Title: <input name="title" type="text" /></div>
            <div>Text: <textarea required name="text"></textarea></div>
            <div><input value="Upload" type="submit" /></div>
        </form>
    '''


@route('/p/upload', method='POST')
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

    if len(text) > MAX_PASTE_SIZE:
        abort(413, 'upload too big. max is {}'.format(MAX_PASTE_SIZE))
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

    return name


run(host='localhost', port=8088, quiet=True)
