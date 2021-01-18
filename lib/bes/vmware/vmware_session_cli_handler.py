#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

import pprint

from bes.cli.cli_command_handler import cli_command_handler
from bes.common.check import check
from bes.common.string_util import string_util
from bes.key_value.key_value_list import key_value_list
from bes.text.text_table import text_table

from .vmware_client_commands import vmware_client_commands
from .vmware_error import vmware_error
from .vmware_server import vmware_server
from .vmware_session import vmware_session
from .vmware_session_options import vmware_session_options

class vmware_session_cli_handler(cli_command_handler):
  'vmware session cli handler.'

  def __init__(self, cli_args):
    super(vmware_session_cli_handler, self).__init__(cli_args, options_class = vmware_session_options)
    check.check_vmware_session_options(self.options)

  def _handle_session_command(self, command_name, *args, **kwargs):
    session = vmware_session(port = None, credentials = None)
    session.start()
    commands = vmware_client_commands(session.client, self.options)
    func = getattr(commands, command_name)
    result = func(*args, **kwargs)
    session.stop()
    return result
    
  def vms(self):
    return self._handle_session_command('vms')

  def vm_settings(self, vm_id):
    return self._handle_session_command('vm_settings', vm_id)
  
  def vm_config(self, vm_id, key):
    return self._handle_session_command('vm_config', vm_id, key)

  def vm_power(self, vm_id, state, wait):
    return self._handle_session_command('vm_power', vm_id, state, wait)

  def request(self, endpoint, args):
    return self._handle_session_command('request', endpoint, args)
  
  def vm_mac_address(self, vm_id):
    return self._handle_session_command('vm_mac_address', vm_id)

  def vm_ip_address(self, vm_id):
    return self._handle_session_command('vm_ip_address', vm_id)

  def vm_shared_folders(self, vm_id):
    return self._handle_session_command('vm_shared_folders', vm_id)

  def vm_update_shared_folder(self, vm_id, folder_id, host_path, flags):
    return self._handle_session_command('vm_update_shared_folder', vm_id, folder_id, host_path, flags)

  def vm_add_shared_folder(self, vm_id, folder_id, host_path, flags):
    return self._handle_session_command('vm_add_shared_folder', vm_id, folder_id, host_path, flags)

  def vm_delete_shared_folder(self, vm_id, folder_id):
    return self._handle_session_command('vm_delete_shared_folder', vm_id, folder_id)

  def vm_copy(self, vm_id, new_vm_id):
    return self._handle_session_command('vm_copy', vm_id, new_vm_id)

  def vm_delete(self, vm_id):
    return self._handle_session_command('vm_delete', vm_id)
  
  def vm_restart(self, vm_id, wait):
    return self._handle_session_command('vm_restart', vm_id, wait)