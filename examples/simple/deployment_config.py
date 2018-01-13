# deployment_config.py

from pyauto import config
import os


class App(config.Config):
    def get_source_dir(self):
        return os.path.abspath(self.source_dir)


config.set_config_class('apps', App.wrap)

