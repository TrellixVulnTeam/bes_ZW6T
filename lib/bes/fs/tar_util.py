#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

import os.path as path, os, re, tarfile
from collections import namedtuple

from bes.common import check
from bes.system import execute, host, os_env_var

from .file_util import file_util
from .file_find import file_find
from .file_path import file_path
from .temp_file import temp_file

class tar_util(object):

  def _find_tar_exe_tar():
    'Find the tar executable explicitly in the system default place in case the user aliased it somehow'
    if host.is_linux():
      return '/bin/tar'
    elif host.is_macos():
      return '/usr/bin/tar'
    else:
      raise RuntimeError('Unknown host system')

  TAR_EXE = _find_tar_exe_tar()
      
  @classmethod
  def copy_tree_with_tar(clazz, src_dir, dst_dir):
    if not path.isdir(src_dir):
      raise RuntimeError('src_dir is not a directory: %s' % (src_dir))
    file_util.mkdir(dst_dir)
    unreadable = file_find.find_unreadable(src_dir)
    exclude_flags = []
    for filename in unreadable:
      exclude_flags.append('--exclude \"%s\"' % (filename))
    if exclude_flags:
      exclude_flags_flat = ' '.join(exclude_flags)
    else:
      exclude_flags_flat = ''
    cmd = '%s %s -C %s -pcf - . | ( cd %s ; %s -pxf - )' % (clazz.TAR_EXE, exclude_flags_flat,
                                                            src_dir, dst_dir, clazz.TAR_EXE)
    with os.popen(cmd) as pipe:
      pipe.read()
      pipe.close()

  @classmethod
  def members(clazz, filename):
    cmd = 'tar tf %s' % (filename)
    rv = execute.execute(cmd)
    return [ i for i in rv.stdout.split('\n') if i ]

  @classmethod
  def extract(clazz, filename, dest_dir):
    execute.execute('tar xf {filename} -C {dest_dir}'.format(filename = filename, dest_dir = dest_dir))

  _tar_info = namedtuple('_tar_exe_info', 'flavor, version')
  @classmethod
  def tar_exe_info(clazz, filename):
    rv = execute.execute('tar --version', raise_error = False)
    flavor = clazz._tar_flavor(rv.stdout)
    version = clazz._tar_version(flavor, rv.stdout)
    return clazz._tar_info(flavor, version)

  @classmethod
  def extract(clazz, filename, dest_dir):
    execute.execute('tar xf {filename} -C {dest_dir}'.format(filename = filename, dest_dir = dest_dir))

  @classmethod
  def _tar_flavor(clazz, version_text):
    if 'GNU tar' in version_text:
      return 'gnu'
    if 'bsdtar' in version_text:
      return 'bsd'
    return 'unknown'
  
  @classmethod
  def _tar_version(clazz, flavor, version_text):
    if flavor == 'gnu':
      r = re.findall('^tar\s+\(GNU\s+tar\)\s+([0-9\.]+)', version_text)
      return r[0] if r and len(r) == 1 else None
    elif flavor == 'bsd':
      r = re.findall(r'^bsdtar\s+([0-9\.]+)\s+.*$', version_text)
      return r[0] if r and len(r) == 1 else None
    return None

  _POSSIBLE_TARS = [ 'tar', 'gtar', 'gnutar', 'bsdtar' ]
  @classmethod
  def find_tar(clazz, shell_path, flavor):
    check.check_string_seq(shell_path)
    for p in shell_path:
      for possible_tar in clazz._POSSIBLE_TARS:
        exe_file = path.join(p, possible_tar)
        if file_path.is_executable(exe_file):
          info = clazz.tar_exe_info(exe_file)
          if info and info.flavor == flavor:
            return exe_file
    return None

  @classmethod
  def find_tar_in_env_path(clazz, flavor):
    return clazz.find_tar(os_env_var('PATH').path, flavor)
