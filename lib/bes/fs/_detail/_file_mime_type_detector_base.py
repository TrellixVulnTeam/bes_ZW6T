#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

from abc import abstractmethod, ABCMeta
from bes.system.compat import with_metaclass

from bes.system.check import check

class _file_mime_type_detector_base(with_metaclass(ABCMeta, object)):

  @classmethod
  @abstractmethod
  def is_supported(clazz):
    'Return True if this class is supported on the current platform.'
    raise NotImplemented('is_supported')
  
  @classmethod
  @abstractmethod
  def detect_mime_type(clazz, filename):
    'Detect the mime type for file.'
    raise NotImplemented('detect_mime_type')
