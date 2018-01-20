from pyauto.core import config


class Example(config.Config):
    def __init__(self, config, parent=None):
        super(Example, self).__init__(config, parent)
        self['things'] = [Thing(t, self) for t in self['things']]

    def get_thing(self, thing_id):
        for thing in self.things:
            if thing.id == thing_id:
                return thing
        raise Exception('unknown example thing: {0}'.format(thing_id))


class Thing(config.Config):
    pass


config.set_config_class('example', Example.wrap)
config.set_config_class('example_list', Thing.wrap)
