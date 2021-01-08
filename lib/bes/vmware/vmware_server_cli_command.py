#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

from bes.cli.cli_command_handler import cli_command_handler
from bes.common.Script import Script
from bes.common.check import check
from bes.script.blurber import blurber

from .vmware_server import vmware_server
from .vmware_server_options import vmware_server_options
from .vmware_server_app import vmware_server_app

class vmware_server_cli_command(cli_command_handler):
  'vmware server cli handler.'

  def __init__(self, cli_args):
    super(vmware_server_cli_command, self).__init__(cli_args, options_class = vmware_server_options)
    check.check_vmware_server_options(self.options)

  def shell(self, shell_args):
    check.check_string_seq(shell_args)
    
    args = []
    if self.options.port:
      args.extend([ '--port', self.options.port ])
    raise SystemExit(vmware_server_app().main(args = args, shell_args = shell_args))
    return 0