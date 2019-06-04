#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

from bes.system.host import host

_has_xattr=False
try:
  import xattr
  _has_xattr=True
except ImportError as ex:
  pass

if _has_xattr:
  from ._file_attributes_xattr import _file_attributes_xattr as _file_attributes_super_class
elif host.SYSTEM == 'macos':
  from ._file_attributes_macos import _file_attributes_macos as _file_attributes_super_class
elif host.SYSTEM == 'linux':
  from ._file_attributes_linux import _file_attributes_linux as _file_attributes_super_class
else:
  raise RuntimeError('unsupported system: %s' % (host.SYSTEM))

class file_attributes(_file_attributes_super_class):
  pass
