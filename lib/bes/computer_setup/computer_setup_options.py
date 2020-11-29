#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

from bes.common.check import check
from bes.common.dict_util import dict_util
from bes.script.blurber import blurber

class computer_setup_options(object):
  
  def __init__(self, *args, **kargs):
    self.verbose = False
    self.password = None
    self.blurber = blurber()
    self.dry_run = False
    for key, value in kargs.items():
      setattr(self, key, value)
    check.check_bool(self.verbose)
    check.check_string(self.password, allow_none = True)
    check.check_blurber(self.blurber)
    check.check_bool(self.dry_run)

  def __str__(self):
    return str(dict_util.hide_passwords(self.__dict__, [ 'password' ]))

check.register_class(computer_setup_options)
