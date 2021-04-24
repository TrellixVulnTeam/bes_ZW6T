#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

import sys
import os, subprocess
from os import path
import tempfile

from .host import host
from .which import which

class python(object):
  'Class to deal with system specific python things.'

  @classmethod
  def find_python_exe(clazz):
    'Return the full path to the platform specific python executable.'
    exe_name = clazz._find_python_exe_sys_executable()
    if exe_name:
      return exe_name
    exe_name = clazz._python_exe_name()
    return which.which(exe_name)

  @classmethod
  def exe_version(clazz, exe, revision = False):
    'Return the result of python --version.'
    which_exe = which.which(exe)
    if not which_exe:
      raise RuntimeError('python not found: {}'.format(exe))
    s = subprocess.check_output([ which_exe, '--version' ], stderr = subprocess.STDOUT).decode('utf-8').strip()
    version = s.split(' ')[1]
    if revision:
      return version
    return '.'.join(version.split('.')[0:2])

  _UNIX_POSSIBLE_EXE = [ 'python2', 'python2.7', 'python', 'python3' ]
  @classmethod
  def _python_exe_name(clazz):
    'Return the platform specific name of the python exe.'
    if host.is_unix():
      for exe in clazz._UNIX_POSSIBLE_EXE:
        if which.which(exe):
          return path.basename(exe)
      raise RuntimeError('python not found.')
    elif host.is_windows():
      return 'python.exe'
    else:
      host.raise_unsupported_system()

  @classmethod
  def is_python_script(clazz, filename):
    if filename.lower().endswith('.py'):
      return True
    try:
      with open(filename, 'r') as fin:
        line = fin.readline()
        return line.startswith('#!/') and 'python' in line.lower()
    except Exception as ex:
      pass
    return False

  @classmethod
  def _find_python_exe_sys_executable(clazz):
    test_script = '''
raise SystemExit(0)
'''
    tmp = tempfile.NamedTemporaryFile(prefix = 'test-program-',
                                      suffix = '.py',
                                      mode = 'w+b',
                                      delete = False)
    content = test_script.encode('utf-8')
    tmp.write(content)
    tmp.flush()
    tmp.close()
    exit_code = subprocess.check_call([ sys.executable, tmp.name ])
    os.remove(tmp.name)
    if exit_code == 0:
      return sys.executable
    return None
