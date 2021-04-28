#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

import codecs
import os
import os.path as path
import sys
import subprocess

from collections import namedtuple

from bes.common.check import check
from bes.common.string_util import string_util
from bes.fs.file_path import file_path
from bes.fs.file_symlink import file_symlink
from bes.fs.file_util import file_util
from bes.fs.temp_file import temp_file
from bes.system.execute import execute
from bes.system.host import host
from bes.system.user import user
from bes.system.log import logger
from bes.system.os_env import os_env_var
from bes.system.which import which
from bes.unix.brew.brew import brew
from bes.version.software_version import software_version

from .python_error import python_error
from .python_version import python_version

class python_exe(object):
  'Class to deal with the python executable.'

  _log = logger('python_exe')
  
  @classmethod
  def full_version(clazz, exe):
    'Return the full version of a python executable'
    cmd = [ exe, '--version' ]
    rv = execute.execute(cmd, stderr_to_stdout = True)
    parts = string_util.split_by_white_space(rv.stdout, strip = True)
    if len(parts) != 2:
      raise python_error('not a valid python version for {}: "{}"'.format(exe, rv.stdout))
    if parts[0] != 'Python':
      raise python_error('not a valid python name for {}: "{}"'.format(exe, rv.stdout))
    return parts[1]

  @classmethod
  def version(clazz, exe):
    'Return the major.minor version of a python executable'
    full_version = clazz.full_version(exe)
    sv = software_version.parse_version(full_version)
    return '{}.{}'.format(sv.parts[0], sv.parts[1])

  @classmethod
  def major_version(clazz, exe):
    'Return the major version of a python executable'
    full_version = clazz.full_version(exe)
    sv = software_version.parse_version(full_version)
    return sv.parts[0]
  
  @classmethod
  def find_version(clazz, version, exclude_sources = None):
    'Return the python executable for major.minor version or None if not found'
    check.check_string(version)
    check.check_seq(exclude_sources, check.STRING_TYPES, allow_none = True)
    
    exclude_sources = set(exclude_sources or [])
    all_info = python_exe.find_all_exes_info()
    for next_exe, info in all_info.items():
      next_version = clazz.version(next_exe)
      if exclude_sources and info.source in exclude_sources:
        continue
      if next_version == version:
        return next_exe
    return None

  @classmethod
  def find_full_version(clazz, full_version):
    'Return the python executable for major.minor.revision full_version or None if not found'
    version = python_version.version(full_version)
    exe = clazz.find_version(version)
    if not exe:
      return None
    if clazz.full_version(exe) != full_version:
      return None
    return exe
  
  @classmethod
  def has_version(clazz, version):
    'Return True if python version major.minor is found'
    return clazz.find_version(version) != None

  @classmethod
  def has_full_version(clazz, full_version):
    'Return True if python version major.minor.revision is found'
    return clazz.find_full_version(full_version) != None

  @classmethod
  def source(clazz, exe):
    '''Return the source of the python executable.  One of:
          brew: brew (macos or linux)
    python.org: python.org (macos)
        system: builtin to system (macos or linux)
       unknown: none of the above
         xcode: part of xcode
    '''
    clazz.check_exe(exe)

    if host.is_macos():
      result = clazz._determine_source_macos(exe)
    elif host.is_linux():
      result = clazz._determine_source_linux(exe)
    elif host.is_windows():
      result = clazz._determine_source_windows(exe)
    else:
      host.raise_unsupported_system()
    return result

  @classmethod
  def _determine_source_macos(clazz, exe):
    'Determine the source of a python exe on macos'

    if clazz._source_is_xcode(exe):
      return 'xcode'
    elif clazz._source_is_unix_system(exe):
      return 'system'
    elif clazz._source_is_brew(exe):
      return 'brew'
    elif clazz._source_is_python_org(exe):
      return 'python.org'
    else:
      return 'unknown'

  @classmethod
  def _determine_source_windows(clazz, exe):
    'Determine the source of a python exe on windows'

    return 'unknown'

  @classmethod
  def _determine_source_linux(clazz, exe):
    'Determine the source of a python exe on linux'

    if clazz._source_is_unix_system(exe):
      return 'system'
    else:
      return 'unknown'
  
  @classmethod
  def _source_is_brew(clazz, exe):
    'Return True if python executable is from brew'

    if not brew.has_brew():
      return False

    # This is slighlty faster than checking inodes, but it does
    # not always work depending on the python version and perhaps
    # whether its the main one
    if host.is_macos():
      actual_exe = file_symlink.resolve(exe)
      if 'cellar' in actual_exe.lower():
        return True

    # Check if the inode for exe matches a file in a python package in brew.
    # Checking the inode deals with links, indirection and other tricks
    # brew does to obfuscate the real exe
    exe_inode = file_util.inode_number(exe)
    b = brew()
    packages = b.installed()
    python_packages = [ p for p in packages if p.startswith('python@') ]
    for next_package in python_packages:
      files = b.files(next_package)
      for f in files:
        next_file_inode = file_util.inode_number(f)
        if exe_inode == next_file_inode:
          return True
    return False

  @classmethod
  def _source_is_xcode(clazz, exe):
    'Return True if python executable is from brew'

    real_exe = clazz.sys_executable(exe)
    return 'Applications/Xcode.app' in real_exe
      
  @classmethod
  def _source_is_unix_system(clazz, exe):
    'Return True if the given python executable came builtin to the current system'

    if host.is_unix():
      return exe.lower().startswith('/usr/bin/python')
    else:
      host.raise_unsupported_system()

  @classmethod
  def _source_is_python_org(clazz, exe):
    'Return True if the given python executable is from python.org'

    return False
      
  @classmethod
  def check_exe(clazz, python_exe, check_abs = True):
    'Check that python_exe appears to be a valid python exe and raise an error if not'
    check.check_string(python_exe)
    check.check_bool(check_abs)

    if check_abs and not path.isabs(python_exe):
      raise python_error('not an absolute path: "{}"'.format(python_exe))
  
    if not file_path.is_executable(python_exe):
      raise python_error('not a valid executable: "{}"'.format(python_exe))

    return clazz.full_version(python_exe)

  _run_script_result = namedtuple('_run_script_result', 'exit_code, output')
  @classmethod
  def run_script(clazz, exe, script, args = None):
    'Run the script and return the result.'
    clazz.check_exe(exe)
    check.check_string(script)
    check.check_string_seq(args, allow_none = True)

    args = list(args or [])
    tmp_script = temp_file.make_temp_file(content = script, suffix = '.py')
    cmd = [ exe, tmp_script ] + args
    clazz._log.log_d('run_script: exe={} cmd={}'.format(exe, cmd))
    clazz._log.log_d('run_script: script=\n{}\n'.format(script))

    try:
      output_bytes = subprocess.check_output(cmd, stderr = subprocess.STDOUT)
      exit_code = 0
      clazz._log.log_d('run_script: success')
    except subprocess.CalledProcessError as ex:
      clazz._log.log_d('run_script: caught: {}'.format(str(ex)))
      output_bytes = ex.output
      exit_code = ex.returncode
      clazz._log.log_d('run_script: failed')
    finally:
      file_util.remove(tmp_script)
    output = codecs.decode(output_bytes, 'utf-8').strip()
    clazz._log.log_d('run_script: exit_code={} output="{}"')
    return clazz._run_script_result(exit_code, output)
    
  @classmethod
  def sys_executable(clazz, exe):
    'Return the value of sys.executable for the given python executable'
    clazz.check_exe(exe)

    script = r'''\
import sys
assert len(sys.argv) == 2
_filename = sys.argv[1]
with open(_filename, 'w') as f:
  f.write(sys.executable)
raise SystemExit(0)
'''
    tmp_output = temp_file.make_temp_file()
    clazz.run_script(exe, script, [ tmp_output ])
    return file_util.read(tmp_output, codec = 'utf-8').strip()

  @classmethod
  def site_packages_path(clazz, exe):
    'Return a list of paths needed for the site-packages of the given python'
    clazz.check_exe(exe)

    script = r'''\
import site
for p in site.getsitepackages():
  print(p)
raise SystemExit(0)
'''
    rv = clazz.run_script(exe, script)
    lines = [ line for line in rv.output.splitlines() if line ]
    return lines
  
  _python_exe_info = namedtuple('_python_exe_info', 'exe, version, full_version, source, sys_executable, real_executable, exe_links, pip_exe')
  @classmethod
  def info(clazz, exe):
    'Return info for python executables'
    clazz.check_exe(exe)
    
    main_exe, exe_links = clazz._determine_main_exe_and_links(exe)
    from .python_installation_v2 import python_installation_v2
    piv = python_installation_v2(main_exe)
    sys_executable = clazz.sys_executable(main_exe)
    real_executable = file_symlink.resolve(sys_executable)
    source = clazz.source(main_exe)
    version = clazz.version(main_exe)
    full_version = clazz.full_version(main_exe)
    return clazz._python_exe_info(main_exe,
                                  version,
                                  full_version,
                                  source,
                                  sys_executable,
                                  real_executable,
                                  exe_links,
                                  piv.pip_exe)

  @classmethod
  def _determine_main_exe_and_links(clazz, exe):
    'Return info for python executables'
    inode = file_util.inode_number(exe)
    exes = clazz._find_all_exes_in_PATH()
    inode_map = clazz._inode_map(exes)
    if not inode in inode_map:
      return exe, []
    links = inode_map[inode]
    main_exe = links.pop(0)
    return main_exe, links
  
  @classmethod
  def find_all_exes(clazz):
    'Return all the executables in PATH that match any patterns'
    all_exes = clazz._find_all_exes_in_PATH()
    inode_map = clazz._inode_map(all_exes)
    result = []
    for inode, exes in inode_map.items():
      main_exe = exes.pop(0)
      result.append(main_exe)
    return result
  
  @classmethod
  def find_all_exes_info(clazz):
    'Return info about all the executables in PATH that match any patterns'
    all_exes = clazz.find_all_exes()
    result = {}
    for next_exe in all_exes:
      result[next_exe] = clazz.info(next_exe)
    return result

  # Order in which versions are checked to return the default exe
  _DEFAULT_EXE_VERSION_LOOKUP_ORDER = [
    '3.7',
    '3.8',
    '3.9',
    '2.7',
  ]
  @classmethod
  def default_exe(clazz):
    'Return the default python executable'

    all_info = python_exe.find_all_exes_info()
    if not all_info:
      return None
    by_version = {}
    for _, next_info in all_info.items():
      by_version[next_info.version] = next_info
    for version in clazz._DEFAULT_EXE_VERSION_LOOKUP_ORDER:
      info = by_version.get(version, None)
      if info:
        return info.exe
    return by_version.items()[0].exe
  
  @classmethod
  def _find_all_exes_in_PATH(clazz):
    'Return all the executables in PATH that match any patterns'
    patterns = [
      'python',
      'python[0-9]',
      'python[0-9].[0-9]',
    ]
    patterns_with_extensions = []
    for pattern in patterns:
      if host.is_windows():
        patterns_with_extensions.extend([ pattern + os.extsep + ext for ext in which.EXE_EXTENSIONS ])
      elif host.is_unix():
        patterns_with_extensions.append(pattern)
      else:
        host.raise_unsupported_system()
    env_path = os_env_var('PATH').path + clazz._find_extra_PATH()
    sanitized_env_path = clazz._sanitize_env_path(env_path)
    result = file_path.glob(sanitized_env_path, patterns_with_extensions)
    clazz._log.log_d('patterns_with_extensions={}'.format(patterns_with_extensions))
    clazz._log.log_d('                env_path={}'.format(env_path))
    clazz._log.log_d('      sanitized_env_path={}'.format(sanitized_env_path))
    clazz._log.log_d('                  result={}'.format(result))
    return result

  @classmethod
  def _find_extra_PATH(clazz):
    'Platform specific extra PATH where to search for pythons'
    result = []
    if host.is_windows():
      result.extend([
        r'C:\Program Files\Python37',
        r'C:\Program Files\Python38',
        r'C:\Program Files\Python39',
        r'C:\Python27',
      ])
    elif host.is_macos():
      result.extend([
        '/usr/local/opt/python@3.7/bin',
        '/usr/local/opt/python@3.8/bin',
        '/usr/local/opt/python@3.9/bin',
      ])
    return result

  @classmethod
  def _sanitized_env_path_should_skip(clazz, entry):
    # Windows has some exes named pythonX.exe which call the app store to
    # install python if invoked - not real python so ignore those
    if r'Microsoft\WindowsApps' in entry:
      return True
    if entry.startswith(user.HOME):
      return True
    return False
  
  @classmethod
  def _sanitize_env_path(clazz, env_path):
    return [ entry for entry in env_path if not clazz._sanitized_env_path_should_skip(entry) ]
  
  @classmethod
  def _inode_map(clazz, exes):
    'Return an inode to list of executable map'
    result = {}
    for exe in exes:
      inode = file_util.inode_number(exe)
      if not inode in result:
        result[inode] = []
      result[inode].append(exe)
    sorted_result = {}
    for inode, links in result.items():
      sorted_result[inode] = sorted(result[inode], key = lambda exe: len(exe), reverse = True)
    return sorted_result

  @classmethod
  def exe_for_sys_version(clazz, absolute = True):
    'Return the python executable binary for sys.version (python2.7, python3.7, etc)'
    check.check_bool(absolute)

    exe = 'python{major}.{minor}'.format(major = sys.version_info.major,
                                         minor = sys.version_info.minor)
    if absolute:
      return which.which(exe)
    else:
      return exe
