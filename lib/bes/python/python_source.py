#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

from .detail.python_source_base import python_source_base

from bes.system.host import host

class python_source(python_source_base):

  def _find_impl_class(system):
    result = None
    if system == host.LINUX:
      from .detail.python_source_linux import python_source_linux
      result = python_source_linux
    elif system == host.MACOS:
      from .detail.python_source_macos import python_source_macos
      result = python_source_macos
    elif system == host.WINDOWS:
      from .detail.python_source_windows import python_source_windows
      result = python_source_windows
    else:
      host.raise_unsupported_system(system = system)
    return result
  
  _impl_class = _find_impl_class(host.SYSTEM)
  
  @classmethod
  #@abstractmethod
  def exe_source(clazz, exe):
    'Return the source of the python executable.  Stuff like brew, xcode, system, python.org.'
    return clazz._impl_class.exe_source(exe)

  @classmethod
  #@abstractmethod
  def possible_python_bin_dirs(clazz):
    'Return a list of possible dirs where the python executable might be.'
    return clazz._impl_class.possible_python_bin_dirs()

  @classmethod
  #@abstractmethod
  def possible_python_exe_patterns(clazz):
    'Return a list of possible python exe fnmatch patters.'
    return clazz._impl_class.possible_python_exe_patterns()

  @classmethod
  #@abstractmethod
  def possible_python_dir_should_be_ignored(clazz, dirname):
    'Return True if dirname should be ignored as a possible python bin dir.'
    return clazz._impl_class.possible_python_dir_should_be_ignored(dirname)

  @classmethod
  #@abstractmethod
  def exe_name(clazz, exe):
    'Return the name of a python exe.  without possible extensions or absolute paths.'
    return clazz._impl_class.exe_name(exe)

  @classmethod
  #@abstractmethod
  def possible_python_dot_org_installer_filenames(self, full_version):
    'Return a list of possible python.org installer filenames for full version.'
    return clazz._impl_class.possible_python_dot_org_installer_filenames(full_version)

  @classmethod
  def find_impl(clazz, system):
    'Return the system specific python source impl.'
    return clazz._find_impl_class(system)