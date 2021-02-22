#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

from collections import namedtuple
import os.path as path
import multiprocessing
import socket
import sys
import time
import tempfile
import inspect

from bes.system.log import logger
from bes.system.command_line import command_line
from bes.system.host import host
from bes.common.check import check
from bes.common.string_util import string_util
from bes.fs.file_find import file_find
from bes.fs.file_util import file_util
from bes.fs.temp_file import temp_file
from bes.archive.archiver import archiver

from .vmware_app import vmware_app
from .vmware_error import vmware_error
from .vmware_local_vm import vmware_local_vm
from .vmware_options import vmware_options
from .vmware_power import vmware_power
from .vmware_preferences import vmware_preferences
from .vmware_session import vmware_session
from .vmware_vm import vmware_vm
from .vmware_vmrun import vmware_vmrun
from .vmware_vmrun_exe import vmware_vmrun_exe
from .vmware_vmx_file import vmware_vmx_file

class vmware(object):

  _log = logger('vmware')
  
  def __init__(self, options = None):
    self._options = options or vmware_options()
    self._preferences_filename = vmware_preferences.default_preferences_filename()
    self._preferences = vmware_preferences(self._preferences_filename)
    vm_dir = self._options.vm_dir or self._default_vm_dir()
    if not vm_dir:
      raise vmware_error('no vm_dir given in options and no default configured in {}'.format(self._preferences_filename))
    self.local_vms = {}
    vmx_files = file_find.find(vm_dir, relative = False, match_patterns = [ '*.vmx' ])
    for vmx_filename in vmx_files:
      local_vm = vmware_local_vm(vmx_filename)
      self.local_vms[local_vm.nickname] = local_vm
    self._session = None
    self._app = vmware_app()
    self._runner = vmware_vmrun(login_credentials = self._options.login_credentials)

  def _default_vm_dir(self):
    if self._preferences.has_value('prefvmx.defaultVMPath'):
      return self._preferences.get_value('prefvmx.defaultVMPath')
    return None

  @property
  def session(self):
    if not self._session:
      self._log.log_d('session: creating session')
      self._session = vmware_session(port = self._options.vmrest_port,
                                     credentials = self._options.vmrest_credentials)
      self._log.log_d('session: starting session')
      self._session.start()
      self._log.log_d('session: starting session done')
    return self._session

  def vm_run_program(self, vm_id, program, interactive):
    check.check_string(vm_id)
    check.check_string_seq(program)
    check.check_bool(interactive)

    self._log.log_method_d()
    
    vmx_filename = self._resolve_vmx_filename(vm_id)
    target_vm_id, target_vmx_filename = self._clone_vm_if_needed(vm_id,
                                                                 vmx_filename,
                                                                 self._options.clone_vm)
    
    if not self._options.dont_ensure or self._options.clone_vm:
      self._ensure_running_if_needed(target_vm_id)
      self._log.log_d('vm_run_package:{}: ensuring vm can run programs'.format(target_vm_id))
      self.vm_wait_for_can_run_programs(target_vm_id, interactive)
      
    rv = self._do_run_program(target_vmx_filename, program, interactive)

    if self._options.clone_vm and not self._options.debug:
      self._runner.vm_stop(target_vmx_filename)
      self._runner.vm_delete(target_vmx_filename)

    return rv

  def vm_run_script(self, vm_id, program, interactive):
    check.check_string(vm_id)
    check.check_string_seq(program)
    check.check_bool(interactive)

    self._log.log_method_d()
    
    vmx_filename = self._resolve_vmx_filename(vm_id)
    target_vm_id, target_vmx_filename = self._clone_vm_if_needed(vm_id,
                                                                 vmx_filename,
                                                                 self._options.clone_vm)
    
    if not self._options.dont_ensure or self._options.clone_vm:
      self._ensure_running_if_needed(target_vm_id)
      self._log.log_d('vm_run_package:{}: ensuring vm can run programs'.format(target_vm_id))
      self.vm_wait_for_can_run_programs(target_vm_id, interactive)
      
    rv = self._do_run_program(target_vmx_filename, program, interactive)

    if self._options.clone_vm and not self._options.debug:
      self._runner.vm_stop(target_vmx_filename)
      self._runner.vm_delete(target_vmx_filename)

    return rv
  
  def _do_run_program(self, vmx_filename, program, interactive):
    assert path.isfile(vmx_filename)

    program_args = command_line.parse_args(program)
    interactive_args = [ '-interactive' ] if interactive else []
    args = [
      'runProgramInGuest',
      vmx_filename,
    ] + interactive_args + program_args
    self._log.log_d('vm_run_program: args={}'.format(args))
    return self._runner.run(args)

  @classmethod
  def _tmp_nickname_part(clazz):
    d = tempfile.mkdtemp()
    b = path.basename(d)
    file_util.remove(d)
    return string_util.remove_head(b, 'tmp')
  
  def _clone_vm_if_needed(self, vm_id, vmx_filename, clone_vm):
    if not clone_vm:
      return vm_id, vmx_filename
    
    vms_root_dir = path.normpath(path.join(path.dirname(vmx_filename), path.pardir))
    self.vm_set_power(vm_id, 'off', None, None, None, 1)
    src_vmx_nickname = vmware_vmx_file.nickname(vmx_filename)
    tmp_nickname_part = self._tmp_nickname_part()
    new_vmx_nickname = '{}_clone_{}'.format(src_vmx_nickname, tmp_nickname_part)
    new_vm_root_dir_basename = '{}.vmwarevm'.format(new_vmx_nickname)
    new_vm_root_dir = path.join(vms_root_dir, new_vm_root_dir_basename)
    file_util.mkdir(new_vm_root_dir)
    new_vmx_basename = '{}.vmx'.format(new_vmx_nickname)
    new_vmx_filename = path.join(new_vm_root_dir, new_vmx_basename)
    rv = self.vm_clone(vm_id,
                       new_vmx_filename,
                       full = False,
                       snapshot_name = None,
                       clone_name = new_vmx_nickname)
    if rv.exit_code != 0:
      print('clone failed: {}'.format(rv.stdout))
    assert rv.exit_code == 0
    new_vm_id = self._vmx_filename_to_id(new_vmx_filename)
    self._log.log_d('clone worked: new_mv_id={} new_vmx_filename={}'.format(new_vm_id, new_vmx_filename))
    return new_vm_id, new_vmx_filename
  
  def vm_can_run_programs(self, vm_id, interactive):
    check.check_string(vm_id)
    check.check_bool(interactive)

    self._log.log_method_d()
    
    vmx_filename = self._resolve_vmx_filename(vm_id)
    try:
      rv = self._do_run_program(vmx_filename, '/bin/bash --version', interactive)
      self._log.log_d('vm_can_run_programs: exit_code={}'.format(rv.exit_code))
      if rv.exit_code != 0:
        self._log.log_d('vm_can_run_programs: output:\n'.format(rv.stdout))
      return rv.exit_code == 0
    except vmware_error as ex:
      pass
    return False

  def vm_wait_for_can_run_programs(self, vm_id, interactive):
    check.check_string(vm_id)
    check.check_bool(interactive)

    self._log.log_method_d()
    
    num_tries = self._options.wait_programs_num_tries
    sleep_time = self._options.wait_programs_sleep_time
    self._log.log_d('vm_wait_for_can_run_programs: num_tries={} sleep_time={}'.format(num_tries,
                                                                                      sleep_time))
    for i in range(1, num_tries + 1):
      self._log.log_d('vm_wait_for_can_run_programs: try {} of {}'.format(i, num_tries))
      if self.vm_can_run_programs(vm_id, interactive):
        self._log.log_d('vm_wait_for_can_run_programs: try {} success'.format(i))
        return
      self._log.log_d('vm_wait_for_can_run_programs: sleeping for {} seconds'.format(sleep_time))
      time.sleep(sleep_time)
    self._log.log_d('vm_wait_for_can_run_programs: timed out waiting for vm to be able to run programs.')
    raise vmware_error('vm_wait_for_can_run_programs: timed out waiting for vm to be able to run programs.')
  
  def vm_run_package(self, vm_id, package_dir, entry_command, entry_command_args,
                     interactive, output_filename, tail_log):
    check.check_string(vm_id)
    check.check_string(package_dir)
    check.check_string(entry_command)
    check.check_string_seq(entry_command_args)
    check.check_bool(interactive)
    check.check_string(output_filename, allow_none = True)
    check.check_bool(tail_log)

    self._log.log_method_d()

    debug = self._options.debug
    
    if not path.isdir(package_dir):
      raise vmware_error('package_dir not found or not a dir: "{}"'.format(package_dir))

    vmx_filename = self._resolve_vmx_filename(vm_id)
    self._log.log_d('vm_run_package: vmx_filename={} dont_ensure={}'.format(vmx_filename,
                                                                            self._options.dont_ensure))

    target_vm_id, target_vmx_filename = self._clone_vm_if_needed(vm_id, vmx_filename, self._options.clone_vm)
    assert target_vm_id
    assert path.isfile(target_vmx_filename)
    self._log.log_d('vm_run_package: target_vm_id={} target_vmx_filename={}'.format(target_vm_id,
                                                                                    target_vmx_filename))
    
    if not self._options.dont_ensure or self._options.clone_vm:
      self._ensure_running_if_needed(target_vm_id)
      self._log.log_d('vm_run_package:{}: ensuring vm can run programs'.format(target_vm_id))
      self.vm_wait_for_can_run_programs(target_vm_id, interactive)
      
    tmp_dir_local = temp_file.make_temp_dir(suffix = '-run_package.dir', delete = not debug)
    if debug:
      print('tmp_dir_local={}'.format(tmp_dir_local))

    tmp_remote_dir = path.join('/tmp', path.basename(tmp_dir_local))
    self._log.log_d('      vm_run_package: tmp_remote_dir={}'.format(tmp_remote_dir))

    rmdir_cmd = '/bin/rm -rf {}'.format(tmp_remote_dir)
    mkdir_cmd = '/bin/mkdir -p {}'.format(tmp_remote_dir)
    rv = self._do_run_program(target_vmx_filename, rmdir_cmd, interactive)
    if rv.exit_code != 0:
      raise vmware_error('vm_run_package: failed to: "{}"'.format(rmdir_cmd))
    rv = self._do_run_program(target_vmx_filename, mkdir_cmd, interactive)
    if rv.exit_code != 0:
      raise vmware_error('vm_run_package: failed to: "{}" - {}\n{}\n'.format(mkdir_cmd,
                                                                             rv.exit_code,
                                                                             rv.stdout))
    
    tmp_package = self._make_tmp_file_pair(tmp_dir_local, 'package.zip')
    tmp_caller_script = self._make_tmp_file_pair(tmp_dir_local, 'caller_script.py')
    tmp_output_log = self._make_tmp_file_pair(tmp_dir_local, 'output.log')

    archiver.create(tmp_package.local, package_dir)
    file_util.save(tmp_caller_script.local,
                   content = self._RUN_PACKAGE_CALLER_PYTHON,
                   mode = 0o0755)
    self._log.log_d('      vm_run_package: tmp_package={}'.format(tmp_package))
    self._log.log_d('      vm_run_package: tmp_caller_script={}'.format(tmp_caller_script))
    self._log.log_d('      vm_run_package: tmp_output_log={}'.format(tmp_output_log))

    self._runner.vm_file_copy_to(target_vmx_filename, tmp_package.local, tmp_package.remote)
    self._runner.vm_file_copy_to(target_vmx_filename, tmp_caller_script.local, tmp_caller_script.remote)

    parsed_entry_command_args = command_line.parse_args(entry_command_args)
    debug_args = []
    if self._options.debug:
      debug_args.append('--debug')
    if self._options.tty:
      debug_args.extend([ '--tty', tty ])

    process = None
    if tail_log:
      debug_args.extend([ '--tail-log-port', str(9000) ])
      resolved_target_vm_id = self.session.resolve_vm_id(target_vm_id)
      ip_address = self.session.call_client('vm_get_ip_address', resolved_target_vm_id)
      print('ip_address={}'.format(ip_address))

      def _process_main(*args, **kargs):
        print('_process_main: args={}'.format(args))
        print('_process_main: kargs={}'.format(kargs))
        ip_address = args[0]
        port = args[1]
        print('_process_main: ip_address={} port={}'.format(ip_address, port))
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        address = ( ip_address, port )
        print('client connecting...')
        sock.connect(address)
        while True:
          data = sock.recv(1024)
          s = data.decode('utf-8')
          print('client got: "{}"'.format(s))
          if s == 'byebye':
            break
        return 0
      
      process = multiprocessing.Process(name = 'caca', target = _process_main, args = ( ip_address, 9000 ))
      process.daemon = True
      process.start()

    caller_args = [ tmp_caller_script.remote ] + debug_args + [
      tmp_package.remote,      
      entry_command,
      tmp_output_log.remote,      
    ] + parsed_entry_command_args
    rv = self._do_run_program(target_vmx_filename, caller_args, interactive)

    self._runner.vm_file_copy_from(target_vmx_filename, tmp_output_log.remote, tmp_output_log.local)

    with file_util.open_with_default(filename = output_filename) as f:
      log_content = file_util.read(tmp_output_log.local, codec = 'utf-8')
      f.write(log_content)

    # cleanup the tmp dir but only if debug is False
    if not debug:
      rv = self._do_run_program(target_vmx_filename, rmdir_cmd, interactive)
      if rv.exit_code != 0:
        raise vmware_error('vm_run_package: failed to: "{}"'.format(rmdir_cmd))

    if self._options.clone_vm and not self._options.debug:
      self._runner.vm_stop(target_vmx_filename)
      self._runner.vm_delete(target_vmx_filename)
      
    if process:
      print('joining process')
      process.join()
      
    return rv

  _tmp_file_pair = namedtuple('_tmp_file_pair', 'local, remote')
  def _make_tmp_file_pair(self, tmp_dir_local, name):
    local = path.join(tmp_dir_local, name)
    remote = path.join('/tmp', path.basename(tmp_dir_local), name)
    return self._tmp_file_pair(local, remote)
    
  def _make_temp_tmp_filename(self, local_tmp_filename):
    tmp_basename = path.basename(local_tmp_filename)
    tmp_remote_filename = path.join('/tmp', tmp_basename)
    return tmp_remote_filename
  
  def _ensure_running_if_needed(self, vm_id):
    self._log.log_d('_ensure_running_if_needed: ensuring vmware is running')
    self._app.ensure_running()
    
    resolved_vm_id = self.session.resolve_vm_id(vm_id)
    assert resolved_vm_id
    vm_label = '{}:{}'.format(vm_id, resolved_vm_id)
    self._log.log_d('_ensure_running_if_needed:{}: ensuring vm is running'.format(vm_label))
    self.session.ensure_vm_running(resolved_vm_id)
  
  def vm_clone(self, vm_id, clone_name, where = None, full = False, snapshot_name = None, shutdown = False):
    check.check_string(vm_id)
    check.check_string(clone_name)
    check.check_string(where, allow_none = True)
    check.check_bool(full)
    check.check_string(snapshot_name, allow_none = True)
    check.check_bool(shutdown)

    self._log.log_method_d()
    
    src_vmx_filename = self._resolve_vmx_filename(vm_id)
    self._log.log_d('vm_delete: vmx_filename={}'.format(vmx_filename))
    return self._runner.vm_clone(src_vmx_filename,
                                 dst_vmx_filename,
                                 full = full,
                                 snapshot_name = snapshot_name,
                                 clone_name = clone_name)

  def vm_delete(self, vm_id, shutdown = False):
    check.check_string(vm_id)
    check.check_bool(shutdown)

    self._log.log_method_d()

    vmx_filename = self._resolve_vmx_filename(vm_id)
    self._log.log_d('vm_delete: vmx_filename={}'.format(vmx_filename))
    if shutdown:
      self._runner.vm_set_power_state(vmx_filename, 'stop')
    return self._runner.vm_delete(vmx_filename)
                    
  def _resolve_vmx_filename(self, vm_id, raise_error = True):
    vmx_filename = self._resolve_vmx_filename_local_vms(vm_id) or self._resolve_vmx_filename_rest_vms(vm_id)
    if not vmx_filename and raise_error:
      raise vmware_error('failed to resolve vmx filename for id: "{}"'.format(vm_id))
    self._log.log_d('_resolve_vmx_filename: vm_id={} vmx_filename={}'.format(vm_id, vmx_filename))
    return vmx_filename
  
  def _resolve_vmx_filename_local_vms(self, vm_id):
    if vmware_vmx_file.is_vmx_file(vm_id):
      return vm_id
    for nickname, vm in self.local_vms.items():
      if vm_id in [ nickname, vm.vmx_filename ]:
        return vm.vmx_filename
    return None

  def _resolve_vmx_filename_rest_vms(self, vm_id):
    rest_vms = self.session.client.vms()
    for vm in rest_vms:
      if vm_id in [ vm.name, vm.vm_id, vm.vmx_filename ]:
        return vm.vmx_filename
    return None

  def _vmx_filename_to_id(self, vmx_filename):
    rest_vms = self.session.client.vms()
    for vm in rest_vms:
      if vmx_filename == vm.vmx_filename:
        return vm.vm_id
    return None
  
  def _authentication_args(self, username = None, password = None):
    args = [ '-T', self._app.host_type() ]
    if username:
      args.extend([ '-gu', username ])
    if password:
      args.extend([ '-gp', password ])
    return args

  def vm_file_copy_to(self, vm_id, local_filename, remote_filename):
    check.check_string(vm_id)
    check.check_string(local_filename)
    check.check_string(remote_filename)

    self._log.log_method_d()
    
    src_vmx_filename = self._resolve_vmx_filename(vm_id)
    
    local_filename = path.abspath(local_filename)
    if not path.isfile(local_filename):
      raise vmware_error('local filename not found: "{}"'.format(local_filename))

    return self._runner.vm_file_copy_to(src_vmx_filename, local_filename, remote_filename)

  def vm_file_copy_from(self, vm_id, remote_filename, local_filename):
    check.check_string(vm_id)
    check.check_string(remote_filename)
    check.check_string(local_filename)

    self._log.log_method_d()
    
    src_vmx_filename = self._resolve_vmx_filename(vm_id)

    file_util.remove(local_filename)
    result = self._runner.vm_file_copy_from(src_vmx_filename, remote_filename, local_filename)
    assert path.isfile(local_filename)
    return result

  def vm_set_power_state(self, vm_id, state, wait):
    check.check_string(vm_id)
    check.check_string(state)
    check.check_bool(wait)

    self._log.log_method_d()
    
    vmware_power.check_state(state)
    
    self._app.ensure_running()

    vmx_filename = self._resolve_vmx_filename(vm_id)
    
    self._log.log_d('vm_set_power: vm_id={} state={} wait={}'.format(vm_id,
                                                                     state,
                                                                     wait))

    self._runner.vm_set_power_state(vmx_filename, state)
    if wait and state in ( 'start', 'unpause' ):
      self.vm_wait_for_can_run_programs(vm_id, False)

  def vm_command(self, vm_id, command, command_args):
    check.check_string(vm_id)
    check.check_string(command)
    check.check_string_seq(command_args)

    self._log.log_method_d()
    
    vmx_filename = self._resolve_vmx_filename(vm_id)
    self._log.log_d('vm_command: vm_id={} vmx_filename={} command={} command_args={}'.format(vm_id,
                                                                                             vmx_filename,
                                                                                             command,
                                                                                             command_args))
    command_args = command_args or []
    args = [ command, vmx_filename ] + command_args
    return self._runner.run(args)
      
  _RUN_PACKAGE_CALLER_PYTHON = r'''#!/usr/bin/env python

import argparse
import os
import os.path as path
import platform
import socket
import subprocess
import sys
import sys
import tarfile
import tempfile
import zipfile

class package_caller(object):

  def __init__(self):
    pass
  
  def main(self):
    p = argparse.ArgumentParser()
    p.add_argument('-v', '--verbose', action = 'store_true', default = False,
                   help = 'Verbose log output [ False ]')
    p.add_argument('--debug', action = 'store_true', default = False,
                   help = 'Debug mode.  Save temp files and log the script itself [ False ]')
    p.add_argument('--tty', action = 'store', default = None,
                   help = 'tty to log to in debug mode [ False ]')
    p.add_argument('--tail-log-port', action = 'store', default = None, type = int,
                   help = 'port to send to for tailing [ False ]')
    p.add_argument('package_zip', action = 'store', default = None,
                   help = 'The package []')
    p.add_argument('entry_command', action = 'store', default = None,
                   help = 'The entry command []')
    p.add_argument('output_log', action = 'store', default = None,
                   help = 'The output log file []')
    p.add_argument('entry_command_args', action = 'store', default = [], nargs = '*',
                   help = 'Optional entry command args [ ]')
    args = p.parse_args()
    # make sure the log exists so even if the command fails theres something
    with open(args.output_log, 'w') as fout:
      fout.write('')
      fout.flush()
    self._debug = args.debug
    self._name = path.basename(sys.argv[0])
    self._console_device = args.tty or self._find_console_device()
    self._socket = None
    for key, value in sorted(args.__dict__.items()):
      self._log('args: {}={}'.format(key, value))
    tmp_dir = path.join(path.dirname(args.package_zip), 'work')
    self._log('tmp_dir={}'.format(tmp_dir))

    self._log('package_zip={} entry_command={} output_log={}'.format(args.package_zip,
                                                                     args.entry_command,
                                                                     args.output_log))

    self._unpack_package(args.package_zip, tmp_dir)
    self._start_socket(args.tail_log_port)
    exit_code = self._execute(tmp_dir,
                              args.entry_command,
                              args.output_log,
                              args.entry_command_args)
    self._stop_socket(args.tail_log_port)
    return exit_code

  def _start_socket(self, port):
    if not port:
      return
    address = ( 'localhost', port )
    self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self._log('binding socket to port {}'.format(port))
    self._socket.bind(address)

  def _stop_socket(self):
    self._socket.close()
    self._socket = None
    
  def _execute(self, dest_dir, command, output_log, entry_command_args):
    entry_command_args = entry_command_args or []
    stdout_pipe = subprocess.PIPE
    stderr_pipe = subprocess.STDOUT
    command_abs = path.join(dest_dir, command)
    if not path.isfile(command_abs):
      raise IOError('entry command not found: "{}"'.format(command_abs))
    args = [ command_abs ] + entry_command_args
    self._log('args={} cwd={}'.format(args, dest_dir))
    os.chmod(command_abs, 0o0755)
    process = subprocess.Popen(args,
                               stdout = stdout_pipe,
                               stderr = stderr_pipe,
                               shell = False,
                               cwd = dest_dir,
                               universal_newlines = True)

    if self._socket:
      self._log('socket listening')
      self._socket.listen(1)
      self._log('calling accept')
      connection, client_address = self._socket.accept()
      self._log('connection={} client_address={}'.format(connection, client_address))

    stdout_lines = []
    if False:
      # Poll process for new output until finished
      while True:
        nextline = process.stdout.readline()
        if nextline == '' and process.poll() != None:
            break
        stdout_lines.append(nextline)
        self._log('process: {}'.format(nextline))

    output = process.communicate()
    exit_code = process.wait()
    self._mkdir(path.dirname(output_log))
    stdout = output[0]
    with open(output_log, 'a') as fout:
      fout.write(stdout)
      fout.flush()
    return exit_code

  @classmethod
  def _mkdir(clazz, p):
    if path.isdir(p):
      return
    os.makedirs(p)
  
  def _unpack_package_zip(self, package_zip, dest_dir):
    with zipfile.ZipFile(package_zip, mode = 'r') as f:
      f.extractall(path = dest_dir)

  def _unpack_package_tar(self, package_tar, dest_dir):
    with tarfile.open(package_tar, mode = 'r') as f:
      f.extractall(path = dest_dir)

  def _unpack_package(self, package, dest_dir):
    if zipfile.is_zipfile(package):
      self._unpack_package_zip(package, dest_dir)
    elif tarfile.is_tarfile(package):
      self._unpack_package_tar(package, dest_dir)
    else:
      raise RuntimeError('unknown archive type: "{}"'.format(package))
      
  def _log(self, message):
    if not self._debug:
      return
    s = '{}: {}\n'.format(self._name, message)
    with open(self._console_device, 'w') as f:
      f.write(s)
      f.flush()

  @classmethod
  def _find_console_device(clazz):
    system = platform.system()
    if system == 'Windows':
      return 'con:'
    elif system == 'Darwin':
      return '/dev/ttys000'
    elif system == 'Linux':
      return '/dev/console'
    else:
      raise RuntimeError('unknown platform: "{}"'.format(system))

  @classmethod
  def run(clazz):
    raise SystemExit(package_caller().main())

if __name__ == '__main__':
  package_caller.run()
'''  
