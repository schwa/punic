__all__ = ['Defaults', 'DictionaryDefaultsProvider', 'EnvironDefaultsProvider', 'JSONFileDefaultsProvider', 'YAMLFileDefaultsProvider', 'LambdaDefaultsProvider']

import os
import sys
import yaml
import json
#import configparser
from pathlib2 import Path

class Defaults(object):

    def __init__(self, key_synonyms = None):
        # type: (list, dict) -> None
        self._obj = ObjWrapper(self, key_synonyms = key_synonyms)
        self.type_converters = None

        self.memory_store = {}

        self.providers = [
            EnvironDefaultsProvider(),
            self.memory_store,
        ]

    def named_provider(self, name):
        return dict(self.providers)[name]

    def insert_provider(self, index, name, provider):
        assert(name not in dict(self.providers))
        self.providers.insert(index, (name, provider))

    def __getitem__(self, item):
        for provider in reversed(self.resolved_providers):
            if item in provider:
                return self.convert_type(item, provider[item])
        raise KeyError(item)

    def __setitem__(self, item, value):
        self.memory_store[item] = value

    def __contains__(self, item):
        for provider in reversed(self.resolved_providers):
            if provider is None:
                return
            if item in provider:
                return True
        return False

    def get(self, item, default):
        if item in self:
            return self[item]
        else:
            return default

    @property
    def resolved_providers(self):
        return [provider[1] for provider in self.providers]

    def keys(self):
        # TODO: Return iterators instead of actual values
        return [key for key, value in self.items()]

    def values(self):
        # TODO: Return iterators instead of actual values
        return [value for key, value in self.items()]

    def items(self):
        # TODO: Return iterators instead of actual values
        items = dict()
        for provider in self.resolved_providers:
            items.update(provider)
        return [(key, self.convert_type(key, value)) for key, value in items.items()]

    def convert_type(self, key, value):
        if self.type_converters and key in self.type_converters:
            converter = self.type_converters[key]
            return converter(value)
        else:
            return value

    @property
    def obj(self):
        return self._obj

    def dump(self):
        for name, provider in self.providers:
            print('#' * 80)
            print('# {}'.format(name))
            for key, value in sorted(provider.items()):
                print('{}: {} ({})'.format(key, value, type(value).__name__))

class DictionaryDefaultsProvider(object):
    def __init__(self, d = None, prefix = None):
        super(DictionaryDefaultsProvider, self).__init__()
        self._d = d
        
    @property
    def d(self):
        if not hasattr(self, '_d'):
            self._d = dict()
        return self._d

    def __contains__(self, key):
        return key in self.d

    def __getitem__(self, key):
        return self.d[key]

    def keys(self):
        return self.d.keys()

    def values(self):
        return self.d.values()

    def items(self):
        return self.d.items()

class EnvironDefaultsProvider(DictionaryDefaultsProvider):
    def __init__(self):
        super(EnvironDefaultsProvider, self).__init__()

    @property
    def d(self):
        return os.environ

class JSONFileDefaultsProvider(DictionaryDefaultsProvider):
    def __init__(self, path):
        # type: (Path) -> None

        d = json.load(path.open())
        if not isinstance(d, dict):
            raise TypeError()
        super(JSONFileDefaultsProvider, self).__init__(d)
        self.path = path

class YAMLFileDefaultsProvider(DictionaryDefaultsProvider):
    def __init__(self, path, prefix_key = None):
        # type: (Path) -> None

        d = yaml.load(path.open())
        if not isinstance(d, dict):
            raise TypeError()

        if prefix_key:
            d = d[prefix_key]

        super(YAMLFileDefaultsProvider, self).__init__(d)
        self.path = path


# class ConfigFileDefaultsProvider(object):
#     def __init__(self, path, section = None):
#         # type: (Path, str) -> None
#
#
#         super(ConfigFileDefaultsProvider, self).__init__()
#         self.path = path
#         self._config = configparser.ConfigParser()
#         self._config.read_file(path.open())
#         self._section = section
#
#     def __contains__(self, key):
#         assert(isinstance(key, str))
#         return self._config.has_option(section = self._section, option = key)
#
#     def __getitem__(self, key):
#         assert(isinstance(key, str))
#         return self._config.get(section = self._section, option = key)
#
#     # def keys(self):
#     #     return self.d.keys()
#     #
#     # def values(self):
#     #     return self.d.values()
#     #
#     # def items(self):
#     #     return self.d.items()


class LambdaDefaultsProvider():
    def __init__(self, lambdas, arg):
        self._lambdas = lambdas
        self._arg = arg

    def __contains__(self, key):
        assert(isinstance(key, str))
        return key in self._lambdas

    def __getitem__(self, key):
        assert(isinstance(key, str))
        return self._lambdas[key](self._arg)

    def keys(self):
        return self._lambdas.keys()

    def values(self):
        return [self[key] for key in self.keys]

    def items(self):
        return [(key, self[key]) for key in self.keys()]


class ObjWrapper(object):
    def __init__(self, dictlike, key_synonyms):
        self._dictlike = dictlike
        self._key_synonyms = key_synonyms

    def __getattr__(self, item):
        if self._key_synonyms:
            item = self._key_synonyms.get(item, item)
        if item in self._dictlike:
            return self._dictlike[item]
        return None

    def keys(self):
        return self._dictlike.keys()

    def values(self):
        return self._dictlike.values()

    def items(self):
        return self._dictlike.items()
