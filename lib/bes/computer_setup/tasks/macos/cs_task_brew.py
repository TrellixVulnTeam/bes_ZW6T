#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

from bes.common.check import check

from bes.computer_setup.computer_setup_task_base import computer_setup_task_base

from bes.unix.brew.brew import brew
from bes.unix.brew.brew_cli_options import brew_cli_options

class cs_task_brew(computer_setup_task_base):

  def __init__(self, *args, **kargs):
    super(cs_task_brew, self).__init__(*args, **kargs)

  #@abstractmethod
  def name(self):
    'Name for task.'
    return 'brew'

  #@abstractmethod
  def description(self):
    'Description for task.'
    return 'Install brew'

  #@abstractmethod
  def average_duration(self):
    'Average duration in seconds.'
    return 8 * 600

  @abstractmethod
  def is_needed(self):
    'Return True of the task needs to run.'
    return not brew.has_brew()
  
  #@abstractmethod
  def run(self):
    'Run the task.'
    options = brew_cli_options()
    options.verbose = self.options.verbose
    options.password = self.options.password
    options.blurber = self.options.blurber
    brew.install(options)
