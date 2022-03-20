#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

from bes.common.check import check
from bes.fs.file_multi_ignore import file_multi_ignore
from bes.fs.file_check import file_check
from bes.property.cached_property import cached_property

class file_ignore_options_mixin(object):

  def __init__(self):
    pass

  @cached_property
  def file_ignorer(self):
    return file_multi_ignore(self.ignore_files)
    
  def should_ignore_file(self, ford):
    ford = file_check.check_file_or_dir(ford)
    
    return self.file_ignorer.should_ignore(ford)