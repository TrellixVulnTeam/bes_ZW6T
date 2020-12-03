#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

from abc import abstractmethod, ABCMeta
from collections import namedtuple

from bes.common.check import check
from bes.system.compat import with_metaclass
from bes.script.blurber import blurber

class python_installer_base(with_metaclass(ABCMeta, object)):

  def __init__(self, blurber):
    check.check_blurber(blurber)
    
    self.blurber = blurber
  
  @abstractmethod
  def available_versions(self, include_all):
    'Return a list of python versions available to install.'
    raise NotImplemented('available_versions')
  
  @abstractmethod
  def installed_versions(self):
    'Return a list of installed python versions.'
    raise NotImplemented('installed_versions')

  @abstractmethod
  def install(self, full_version):
    'Install the major.minor.revision full version of python.'
    raise NotImplemented('install_full_version')

  @abstractmethod
  def uninstall(self, full_version):
    'Uninstall the major.minor.revision full version of python.'
    raise NotImplemented('uninstall_full_version')
  
  def blurb(self, message, output = None, fit = False):
    'Print a blurb'
    self.blurber.blurb(message, output = output, fit = fit)

  def blurb_verbose(self, message, output = None, fit = False):
    'Print a blurb but only in verbose mode'
    self.blurber.blurb_verbose(message, output = output, fit = fit)
    