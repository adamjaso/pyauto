import yaml
from collections import OrderedDict


def dump_dict(data_dict, **kwargs):
    kwargs['allow_unicode'] = True
    kwargs['default_flow_style'] = False
    if 'width' not in kwargs:
        kwargs['width'] = 240
    return yaml.dump(data_dict, **kwargs)


def load_dict(stream, **kwargs):
    Loader = kwargs.get('Loader', yaml.Loader)
    object_pairs_hook = kwargs.get('object_pairs_hook', OrderedDict)

    class OrderedLoader(Loader):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))

    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping)
    return yaml.load(stream, OrderedLoader)


def _should_use_block(value):
    for c in u"\u000a\u000d\u001c\u001d\u001e\u0085\u2028\u2029":
        if c in value:
            return True
    return False


def _represent_scalar(self, tag, value, style=None):
    if style is None:
        if _should_use_block(value):
            style = '|'
        else:
            style = self.default_style

    node = yaml.representer.ScalarNode(tag, value, style=style)
    if self.alias_key is not None:
        self.represented_objects[self.alias_key] = node
    return node


def _represent_dict_order(self, data):
    return self.represent_mapping('tag:yaml.org,2002:map', data.items())


yaml.add_representer(OrderedDict, _represent_dict_order)
yaml.representer.BaseRepresenter.represent_scalar = _represent_scalar
