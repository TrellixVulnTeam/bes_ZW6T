#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

from os import path

from bes.common.check import check

from bes.fs.dir_util import dir_util
from bes.fs.file_util import file_util
from bes.system.execute import execute
from bes.system.log import logger
from bes.system.os_env import os_env
from bes.url.url_util import url_util

from bes.python.python_exe import python_exe
from bes.python.python_version import python_version

from .pip_error import pip_error
from .pip_exe import pip_exe
from .pip_installer_options import pip_installer_options

class pip_installer(object):
  'Pip installer.'

  _log = logger('pip_installer')
  
  def __init__(self, options = None):
    check.check_pip_installer_options(options, allow_none = True)

    self._options = options or pip_installer_options()
    self._python_exe = self._options.resolve_python_exe()
    python_exe.check_exe(self._python_exe)
    self._root_dir = self._options.resolve_root_dir()
    self._cache_dir = path.join(self._root_dir, '.pip_cache')
    self._install_dir = path.join(self._root_dir, self._options.name)
    self._common_pip_args = [
      '--user',
      '--cache-dir', self._cache_dir,
    ]
    python_exe_version = python_exe.version(self._python_exe)
    pip_exe_basename = 'pip{}'.format(python_exe_version)
    self._pip_exe = path.join(self._install_dir, 'bin', pip_exe_basename)
    self._pip_env = self._make_env(self._install_dir)
    
  _GET_PIP_27_URL = 'https://bootstrap.pypa.io/pip/2.7/get-pip.py'
  _GET_PIP_36_URL = 'https://bootstrap.pypa.io/get-pip.py'

  def install(self, pip_version, clobber_install_dir):
    'Install pip on an empty root directory'
    check.check_string(pip_version)
    check.check_bool(clobber_install_dir)

    self._log.log_method_d()
    self._log.log_d('install: root_dir={} python_exe={}'.format(self._root_dir,
                                                                self._python_exe))

    if path.exists(self._install_dir):
      if not path.isdir(self._install_dir):
        raise pip_error('Not a directory: "{}"'.format(self._install_dir))
      if clobber_install_dir:
        file_util.remove(self._install_dir)
      if path.isdir(self._install_dir) and not dir_util.is_empty(self._install_dir):
        raise pip_error('Directory not empty: "{}"'.format(self._install_dir))

    url = self._determine_get_pip_url(self._python_exe)
    tmp_get_pip = url_util.download_to_temp_file(url, suffix = '.py')
    self._log.log_d('install: url={} tmp_get_pip={}'.format(url, tmp_get_pip))
      
    cmd = [
      self._python_exe,
      tmp_get_pip,
      'install',
    ] + self._common_pip_args
    file_util.mkdir(self._root_dir)
    self._log.log_d('install: cmd={} env={}'.format(cmd, self._pip_env))
    execute.execute(cmd, env = self._pip_env)
    self._update_pip(pip_version)
    
  def update(self, pip_version):
    'Update pip to the given version or install it if needed'
    check.check_string(pip_version)

    if not path.exists(self._install_dir):
      self.install(pip_version, False)
    
    self._update_pip(pip_version)

  def _update_pip(self, pip_version):
    'Update pip to the given version or install it if needed'

    if not path.exists(self._pip_exe):
      raise pip_error('Pip not found: {}'.format(self._pip_exe))
      
    old_pip_version = pip_exe.version(self._pip_exe)
    if old_pip_version == pip_version:
      return
    cmd = [
      self._python_exe,
      self._pip_exe,
      'install',
    ] + self._common_pip_args + [
      'pip=={}'.format(pip_version),
    ]
    self._log.log_d('update: cmd={} env={}'.format(cmd, self._pip_env))
    execute.execute(cmd, env = self._pip_env)
    
  def _determine_get_pip_url(clazz, py_exe):
    version = python_exe.version(py_exe)
    if version == '2.7':
      return clazz._GET_PIP_27_URL
    major, minor = version.split('.')
    major = int(major)
    minor = int(minor)
    if major == 3:
      if minor >= 6:
        return clazz._GET_PIP_36_URL
    raise pip_error('Unsupported python version "{}" for {}'.format(version, py_exe))
    
  def _install_pip(self, py_exe, pip_version):
    'Install pip from scratch'
    tmp_get_pip = url_util.download_to_temp_file(self._GET_PIP_URL)

    #--cache-dir    

    cmd = [ py_exe, tmp_get_pip ]
    execute.execute(cmd, env = self._make_clean_env())
    exe = pip_exe.pip_exe(py_exe)
    if not pip_exe.pip_exe_is_valid(exe):
      raise pip_error('failed to install pip version {}'.format(pip_version))
    self._update_pip(py_exe, pip_version)

  @classmethod
  def _list_python_dir(clazz, py_exe):
    python_bin_dir = path.dirname(py_exe)
    return dir_util.list(python_bin_dir)

  def status(self, py_exe):
    'Return the current pip situation'
    check.check_string(py_exe)
    
    if not path.isabs(py_exe):
      raise pip_error('py_exe needs to be an absolute path')
    
    version = python_version.version(py_exe)
    tmp_get_pip = url_util.download_to_temp_file(self, url._GET_PIP_URL)
    cmd = [ py_exe, tmp_get_pip ]
    env = os_env.clone_current_env(d = { 'PYTHONPATH': ''})
    list_before = self._list_python_dir(py_exe)
    execute.execute(cmd, env = env)
    list_after = self._list_python_dir(py_exe)
    pip_basename = 'pip{}'.format(version)
    pip_exe = next(iter([ f for f in list_after if f.endswith(pip_basename) ]), None)
    if not pip_exe:
      raise pip_error('failed to install {}'.format(pip_basename))
    cmd = [ pip_exe, 'install', 'pip=={}'.format(pip_version) ]
    execute.execute(cmd, env = env)
    return pip_exe

  @classmethod
  def _make_env(clazz, install_dir):
    'Make a clean environment for python or pip'
    extra_env = {
      'PYTHONUSERBASE': path.join(install_dir),
      'PYTHONPATH': path.join(install_dir, 'lib/python/site-packages'),
    }
    return os_env.make_clean_env(update = extra_env)

  def uninstall(self):
    'Uninstall pip for the given python executable'

    python_exe.check_exe(py_exe)
    exe = pip_exe.pip_exe(py_exe)
    if not pip_exe.pip_exe_is_valid(exe):
      return
    cmd = [ exe, 'uninstall', '--yes', 'pip' ]
    execute.execute(cmd, env = self._make_clean_env())
