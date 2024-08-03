from bottle import Bottle
from src.sharelib import config
from src import pasty, shortie

main = Bottle()
main.mount(config['shortie_route_prefix'], shortie.app)
main.mount(config['pasty_route_prefix'], pasty.app)

@main.get('/')
def index():
    return 'taiga.link is running!'

if __name__ == '__main__':
    main.run(host=config['listen_addr'],
             port=config['port'],
             quiet=True)
