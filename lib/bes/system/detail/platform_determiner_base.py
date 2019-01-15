#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

from abc import abstractmethod, ABCMeta
from bes.system.compat import with_metaclass

class platform_determiner_base(with_metaclass(ABCMeta, object)):
  'Abstract base class for determining what platform we are on.'
  
  @abstractmethod
  def system(self):
    'system.'
    pass

  @abstractmethod
  def distro(self):
    'distro.'
    pass
  
  @abstractmethod
  def family(self):
    'distro family.'
    pass

  @abstractmethod
  def distributor(self):
    'the distro distributor.'
    pass

  @abstractmethod
  def codename(self):
    'distro codename.'
    pass

  @abstractmethod
  def version(self):
    'distro version.'
    pass

  @abstractmethod
  def arch(self):
    'arch.'
    pass
