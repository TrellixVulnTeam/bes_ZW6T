#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

from collections import namedtuple

from os import path

from bes.common.check import check
from bes.fs.file_find import file_find
from bes.property.cached_property import cached_property
from bes.system.log import logger

from .vmware_clone_util import vmware_clone_util
from .vmware_command_interpreter_manager import vmware_command_interpreter_manager
from .vmware_error import vmware_error
from .vmware_run_program_options import vmware_run_program_options
from .vmware_vmx_file import vmware_vmx_file
from .vmware_clone_util import vmware_clone_util

class vmware_local_vm(object):

  _log = logger('vmware_local_vm')
  
  def __init__(self, runner, vmx_filename, login_credentials):
    check.check_vmware_vmrun(runner)
    check.check_string(vmx_filename)
    check.check_credentials(login_credentials)

    self._runner = runner
    self.vmx_filename = path.abspath(vmx_filename)
    self.vmx = vmware_vmx_file(self.vmx_filename)
    self.login_credentials = login_credentials
    
  def __str__(self):
    return self.vmx_filename

  def __repr__(self):
    return self.vmx_filename
  
  @cached_property
  def nickname(self):
    return self.vmx.nickname

  @cached_property
  def uuid(self):
    return self.vmx.uuid

  @property
  def is_running(self):
    return self._runner.vm_is_running(self.vmx_filename)

  @property
  def ip_address(self):
    return self._runner.vm_get_ip_address(self.vmx_filename)

  @property
  def snapshots(self):
    return self._runner.vm_snapshots(self.vmx_filename)

  @cached_property
  def system(self):
    return self.vmx.system
  
  @cached_property
  def system_info(self):
    return self.vmx.system_info

  @property
  def display_name(self):
    return self.vmx.display_name

  @property
  def interpreter(self):
    return self.vmx.interpreter

  _clone_names = namedtuple('_clone_names', 'clone_name, snapshot_name')
  def make_clone_names(self):
    timestamp = vmware_clone_util.timestamp()
    clone_name = '{}_clone_{}'.format(self.nickname, timestamp)
    snapshot_name = 'snapshot_{}'.format(timestamp)
    return self._clone_names(clone_name, snapshot_name)
  
  def stop(self):
    if not self.is_running:
      return
    self._runner.vm_set_power_state(self.vmx_filename, 'stop')
  
  def can_run_programs(self, run_program_options = None):
    'Return True if the vm can run programs'
    check.check_vmware_run_program_options(run_program_options, allow_none = True)

    self._log.log_method_d()
    if not self.is_running:
      return False

    if not self.ip_address:
      return False
    
    # "exit 0" works on all the default interpreters for both windows and unix
    script = 'exit 0'
    rv = self.run_script(script,
                         run_program_options = run_program_options,
                         interpreter_name = None)
    return rv.exit_code == 0

  def run_script(self,
                 script,
                 run_program_options = None,
                 interpreter_name = None):
    'Return True if the vm can run programs'
    check.check_string(script)
    check.check_vmware_run_program_options(run_program_options, allow_none = True)
    check.check_string(interpreter_name, allow_none = True)

    run_program_options = run_program_options or vmware_run_program_options()

    self._log.log_method_d()
    
    if not self.ip_address:
      raise vmware_error('vm not running: {}'.format(self.nickname))
  
    cim = vmware_command_interpreter_manager.instance()
    interpreter = cim.resolve_interpreter(self.system, interpreter_name)
    self._log.log_d('run_script: interpreter={}'.format(interpreter))
    command = interpreter.build_command(script)
    self._log.log_d('run_script: command={}'.format(command))

    rv = self._runner.vm_run_script(self.vmx_filename,
                                    command.interpreter_path,
                                    command.script_text,
                                    run_program_options,
                                    self.login_credentials)
    self._log.log_d('run_script: exit_code={}'.format(rv.exit_code))
    return rv

  def clone(self, clone_name, where = None, full = False,
            snapshot_name = None, shutdown = False):
    check.check_string(clone_name)
    check.check_string(where, allow_none = True)
    check.check_bool(full)
    check.check_string(snapshot_name, allow_none = True)
    check.check_bool(shutdown)

    self._log.log_method_d()

    dst_vmx_filename = vmware_clone_util.make_dst_vmx_filename(self.vmx_filename,
                                                               clone_name,
                                                               where)
    self._log.log_d('clone: dst_vmx_filename={}'.format(dst_vmx_filename))
    if path.exists(dst_vmx_filename):
      raise vmware_error('Cloned vm already exists: "{}"'.format(dst_vmx_filename))

    if shutdown:
      self.stop()
      
    self._runner.vm_clone(self.vmx_filename,
                          dst_vmx_filename,
                          full = full,
                          snapshot_name = snapshot_name,
                          clone_name = clone_name)
    return vmware_local_vm(self._runner,
                           dst_vmx_filename,
                           self.login_credentials)

  def snapshot(self, snapshot_name):
    self._log.log_method_d()
    self._runner.vm_snapshot_create(self.vmx_filename, snapshot_name)
  
  def snapshot_and_clone(self, where = None, full = False,
                         shutdown = False):
    check.check_string(where, allow_none = True)
    check.check_bool(full)
    check.check_bool(shutdown)

    self._log.log_method_d()
    clone_name, snapshot_name = self.make_clone_names()
    self._log.log_d('snapshot_and_clone: clone_name={} snapshot_name={}'.format(clone_name,
                                                                                snapshot_name))
    self.stop()
    self.snapshot(snapshot_name)
    return self.clone(clone_name,
                      where = where,
                      full = full,
                      snapshot_name = snapshot_name,
                      shutdown = shutdown)

  _info = namedtuple('_info', 'nickname, display_name, vmx_filename, interpreter, ip_address, is_running, can_run_programs, system, system_arch, system_distro, system_family, system_version, uuid')

  @property
  def info(self):
    return self._info(self.nickname,
                      self.display_name,
                      self.vmx_filename.replace(path.expanduser('~'), '~'),
                      self.interpreter,
                      self.ip_address,
                      self.is_running,
                      self.can_run_programs(),
                      self.system_info.system,
                      self.system_info.arch,
                      self.system_info.distro or '',
                      self.system_info.family or '',
                      self.system_info.version,
                      self.uuid)
  
check.register_class(vmware_local_vm)
