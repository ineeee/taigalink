from string import ascii_letters, digits
from random import choices
import json


with open('./taigalink.json', 'r') as file:
    config = json.load(file)

SLUG_CHAR = ascii_letters + digits

def create_slug(length=config['slug_size']):
    return ''.join(choices(SLUG_CHAR, k=length))
