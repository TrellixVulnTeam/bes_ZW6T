#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

from os import path

from bes.common.check import check
from bes.property.cached_property import cached_property
from bes.system.host import host
from bes.system.log import logger
from bes.system.os_env import os_env
from bes.fs.file_mime import file_mime
from bes.fs.filename_util import filename_util

from .pip_error import pip_error

class pip_installation_values(object):
  'Class to determine the filename and directory values of a pip installatiuon.'

  _log = logger('pip')
  
  def __init__(self, install_dir, python_version, system = None):
    check.check_string(install_dir)
    check.check_string(python_version)

    self._install_dir = install_dir
    self._python_version = python_version
    self._system = system or host.SYSTEM

  @cached_property
  def exe(self):
    'Return the pip executable'
    if self._system == host.WINDOWS:
      pip_exe_basename = 'pip{}.exe'.format(self._python_version)
      python_dir = 'Python{}'.format(self._python_version.replace('.', ''))
      if self._python_version == '2.7':
        pexe = path.join(self._install_dir, 'Scripts', pip_exe_basename)
      else:
        pexe = path.join(self._install_dir, python_dir, 'Scripts', pip_exe_basename)
    elif self._system in ( host.LINUX, host.MACOS ):
      pip_exe_basename = 'pip{}'.format(self._python_version)
      pexe = path.join(self._install_dir, 'bin', pip_exe_basename)
    else:
      host.raise_unsupported_system()
    return pexe
    
    return self._pip_exe

  @cached_property
  def site_packages_dir(self):
    'Return the pip site-packages dir sometimes needed for PYTHONPATH'
    if self._system == host.WINDOWS:
      python_dir = 'Python{}'.format(self._python_version.replace('.', ''))
      site_packaged_dir = path.join(self._install_dir, python_dir, 'site-packages')
    elif self._system in ( host.LINUX, host.MACOS ):
      site_packaged_dir = path.join(self._install_dir, 'lib/python/site-packages')
    else:
      host.raise_unsupported_system()
    return site_packaged_dir

  @cached_property
  def env(self):
    'Make a clean environment for python or pip'
    extra_env = {
      'PYTHONUSERBASE': self._install_dir,
      'PYTHONPATH': self.site_packages_dir,
    }
    return os_env.make_clean_env(update = extra_env)

  @classmethod
  def find_install_dir(clazz, pip_exe, system = None):
    'Find the install dir from the pip exe'
    check.check_string(pip_exe)

    if self._system == host.WINDOWS:
      result = self._find_install_dir_windows(pip_exe)
    elif self._system in ( host.LINUX, host.MACOS ):
      result = self._find_install_dir_unix(pip_exe)
    else:
      host.raise_unsupported_system()
    return result

  @classmethod
  def _find_install_dir_unix(clazz, pip_exe):
    parent_dir = file_path.parent_dir(pip_exe)
    print('CACA: parent_dir={}'.format(parent_dir))
    
    root_dir = path.dirname(pip_exe)
    lib_dir = path.normpath(path.join(path.join(root_dir, path.pardir), 'lib'))
    possible_python_libdirs = file_path.glob(lib_dir, 'python*')
    num_possible_python_libdirs = len(possible_python_libdirs)
    if num_possible_python_libdirs == 1:
      python_libdir = possible_python_libdirs[0]
    else:
      python_libdir = None
    if not python_libdir:
      return None
    if not python_libdir:
      return None
    possible_site_packages_dir = path.join(python_libdir, 'site-packages')
    if path.isdir(possible_site_packages_dir):
      return possible_site_packages_dir
    return None
  
  @classmethod
  def _find_install_dir_windows(clazz, pip_exe):
    basename = path.basename(pip_exe)

    f = re.findall(r'^pip(\d+\.\d+)\....$', basename, flags = re.IGNORECASE)
    if not f:
      raise pip_error('pip_exe does not contain a python version: "{}"'.format(pip_exe))
    if len(f) != 1:
      raise pip_error('pip_exe does not contain a python version: "{}"'.format(pip_exe))
    python_version = f[0]
    parent_dir = file_path.parent_dir(pip_exe)

    if python_version == '2.7':
      result = file_path.parent_dir(parent_dir)
    else:
      result = file_path.parent_dir(parent_dir)
      
    
    return 'caca'
    root_dir = path.dirname(pip_exe)
    lib_dir = path.normpath(path.join(path.join(root_dir, path.pardir), 'lib'))
    possible_python_libdirs = file_path.glob(lib_dir, 'python*')
    num_possible_python_libdirs = len(possible_python_libdirs)
    if num_possible_python_libdirs == 1:
      python_libdir = possible_python_libdirs[0]
    else:
      python_libdir = None
    if not python_libdir:
      return None
    if not python_libdir:
      return None
    possible_site_packages_dir = path.join(python_libdir, 'site-packages')
    if path.isdir(possible_site_packages_dir):
      return possible_site_packages_dir
    return None
  
