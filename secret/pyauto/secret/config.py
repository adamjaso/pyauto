from . import store
from pyauto.core import config


class Secret(config.Config):
    def __init__(self, config, parent=None):
        super(Secret, self).__init__(config, parent)
        self.store = store.Store(self.filename)
        self['groups'] = [GroupDefinition(g, self) for g in self.groups]

    def get_group(self, tag):
        for g in self.groups:
            if g.get_id() == tag:
                return g
        raise Exception('unknown group: {0}'.format(tag))

    def get_value(self, group_tag, tag, namespace=None, key=None):
        value = self.get_group(group_tag).get_dict(tag)
        if namespace is None:
            return value
        if key is None:
            return value[namespace]
        return value[namespace][key]

    def delete_value(self, group_tag, tag, namespace=None, key=None):
        return self.get_group(group_tag).delete_keys(tag, namespace, key)


class GroupDefinition(config.Config):
    def __init__(self, config, parent=None):
        super(GroupDefinition, self).__init__(config, parent)
        self.definition = store.GroupDefinition(self.get_id(), self.namespaces)

    def get_group(self, tag):
        return self.config.store.get_group(self.owner_type, tag)

    def get_dict(self, tag):
        return self.get_group(tag).get_dict(self.definition.definition)

    def delete_keys(self, tag, namespace=None, key=None):
        group = self.get_group(tag)
        if namespace is not None and key is not None:
            group.delete(namespace, key)
        elif namespace is not None:
            group.delete_keys(namespace, None)
        else:
            for namespace, value in self.definition.definition.items():
                group.delete_keys(namespace, value.keys())


config.set_config_class('secret', Secret.wrap)
