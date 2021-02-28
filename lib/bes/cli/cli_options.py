# -*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

import pprint
import os.path as path

from abc import abstractmethod, ABCMeta

from bes.system.compat import with_metaclass
from bes.common.dict_util import dict_util
from bes.common.check import check
from bes.config.simple_config import simple_config
from bes.system.log import logger

_HINT_CACHE = {}

class cli_options(with_metaclass(ABCMeta, object)):

  _log = logger('cli_options')
  
  def __init__(self, **kargs):
    default_values = self.default_values()
    self._log.log_d('__init__: default_values={}'.format(pprint.pformat(default_values)))
    self._do_update_values(default_values)
    config_values = self._read_config_file(kargs)
    self._log.log_d('__init__: config_values={}'.format(pprint.pformat(config_values)))
    self._do_update_values(config_values)
    self._log.log_d('__init__: kargs={}'.format(pprint.pformat(kargs)))
    non_default_kargs = self._extract_valid_non_default_values(kargs, default_values)
    self._log.log_d('__init__: non_default_kargs={}'.format(pprint.pformat(non_default_kargs)))
    self._do_update_values(non_default_kargs)
    self.check_value_types()
    
  def __str__(self):
    sensitive_keys = self.sensitive_keys() or {}
    d = dict_util.hide_passwords(self.__dict__, sensitive_keys)
    return pprint.pformat(d)
    
  @classmethod
  @abstractmethod
  def default_values(clazz):
    'Return a dict of default values for these options.'
    raise NotImplemented('default_values')

  @classmethod
  @abstractmethod
  def sensitive_keys(clazz):
    'Return a tuple of keys that are secrets and should be protected from __str__.'
    raise NotImplemented('sensitive_keys')

  @classmethod
  @abstractmethod
  def value_type_hints(clazz):
    raise NotImplemented('morph_value_types')

  @classmethod
  @abstractmethod
  def config_file_key(clazz):
    raise NotImplemented('config_file_key')

  @classmethod
  @abstractmethod
  def config_file_section(clazz):
    raise NotImplemented('config_file_section')

  @classmethod
  @abstractmethod
  def error_class(clazz):
    raise NotImplemented('error_class')

  @abstractmethod
  def check_value_types(self):
    'Check the type of each option.'
    raise NotImplemented('check_value_types')
  
  def _valid_keys(self):
    'Return a list of valid keys for values in these options'
    return [ key for key in self.__dict__.keys() ]

  def update_values(self, values):
    'Update the options values and check their types'
    check.check_dict(values)
    
    self._do_update_values(values)
    self.check_value_types()

  def _do_update_values(self, values):
    'update values only with no checking'
    self._log.log_d('_do_update_values: update before: {}'.format(str(self)))
    for key, value in values.items():
      self._do_set_value(key, value)
    self._log.log_d('_do_update_values: update after: {}'.format(str(self)))

  def _get_value_type_hint(self, key):
    global _HINT_CACHE
    if not self.__class__ in _HINT_CACHE:
      _HINT_CACHE[self.__class__] = self.value_type_hints()
    value_type_hints = _HINT_CACHE[self.__class__]
    return value_type_hints.get(key, None)
    
  def _do_set_value(self, key, value):
    'update one value'
    self._log.log_d('_do_update_value: setattr({}, {}, {}:{})'.format(id(self), key, value, type(value)))
    value_type_hint = self._get_value_type_hint(key)
    if value_type_hint and value != None:
      value = value_type_hint(value)
    setattr(self, key, value)

  @classmethod
  def _read_config_file(clazz, cli_values):
    check.check_dict(cli_values)

    config_file_key = clazz.config_file_key()
    if not config_file_key:
      return {}
    
    config_filename = None
    if config_file_key in cli_values:
      config_filename = cli_values[config_file_key]
      del cli_values[config_file_key]

    if config_filename == None:
      return {}
    return clazz._values_from_config_file(config_filename)

  def _extract_valid_non_default_values(clazz, values, default_values):
    'Extract and return only the valid non default values'
    result = {}
    for key, value in values.items():
      if key in default_values:
        default_value = default_values[key]
        if value != default_value:
          result[key] = value
    return result

  @classmethod
  def _values_from_config_file(clazz, config_filename):
    error_class = clazz.error_class()
    if not path.exists(config_filename):
      raise error_class('Config file not found: "{}"'.format(config_filename))
      
    if not path.isfile(config_filename):
      raise error_class('Config file is not a file: "{}"'.format(config_filename))

    try:
      config = simple_config.from_file(config_filename)
    except Exception as ex:
      raise error_class(str(ex))

    config_file_section = clazz.config_file_section()
    if not config.has_section(config_file_section):
      raise error_class('No section "{}" found in config file: "{}"'.format(config_file_section,
                                                                                  config_filename))
    section = config.section(config_file_section)
    values = section.to_dict()

    valid_keys = clazz.default_values().keys()
    filtered_values = dict_util.filter_with_keys(values, valid_keys)
    return filtered_values
  
  @classmethod
  def from_config_file(clazz, config_filename):
    values = clazz._values_from_config_file(config_filename)
    return clazz(**values)