#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

from bes.cli.cli_options import cli_options
from bes.common.check import check
from bes.common.time_util import time_util

from .files_cli_options import files_cli_options

class file_poto_options(files_cli_options):

  def __init__(self, **kargs):
    super(file_poto_options, self).__init__(**kargs)

  @classmethod
  #@abstractmethod
  def default_values(clazz):
    'Return a dict of defaults for these options.'
    return clazz.super_default_values({
      'small_checksum_size': 1024 * 1024,
    })
  
  @classmethod
  #@abstractmethod
  def value_type_hints(clazz):
    return clazz.super_value_type_hints({
      'small_checksum_size': int,
    })

  #@abstractmethod
  def check_value_types(self):
    'Check the type of each option.'
    super(file_poto_options, self).check_value_types()
    check.check_int(self.small_checksum_size)

check.register_class(file_poto_options)
