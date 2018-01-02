from pyauto import deploy
from . import config


def do_thing(config, thing_id):
    return config.example.get_thing(thing_id)


if '__main__' == __name__:
    deploy.main()
