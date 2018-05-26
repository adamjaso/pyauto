from pyauto.core import config


class Thing(config.Config):
    """A representation of a thing"""

    def get_thing(self, tag):
        """Gets a thing"""

    def do_thing(self, tag):
        """Does a thing"""

    def _do_thing(self, tag):
        """Does an internal thing"""


config.set_config_class('things', Thing.wrap)
