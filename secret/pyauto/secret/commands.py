from pyauto.secret import config as secret_config
from pyauto.core import config


def secret_get(config, group, tag, namespace=None, key=None):
    return config.secret.get_value(group, tag, namespace, key)


def secret_delete(config, group, tag, namespace=None, key=None):
    return config.secret.delete_value(group, tag, namespace, key)


def secret_reset(config, group, tag, namespace=None, key=None):
    secret_delete(config, group, tag, namespace, key)
    return secret_get(config, group, tag, namespace, key)
