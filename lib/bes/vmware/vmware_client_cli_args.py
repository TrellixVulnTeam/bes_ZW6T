#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

class vmware_client_cli_args(object):

  def __init__(self):
    pass
  
  def vmware_client_add_args(self, subparser):

    # vms
    p = subparser.add_parser('vms', help = 'Return a list of vms.')
    self.__vmware_client_add_common_args(p)

    # vm_settings
    p = subparser.add_parser('vm_settings', help = 'Return settings for a vm.')
    self.__vmware_client_add_common_args(p)
    p.add_argument('vm_id', action = 'store', type = str, default = None,
                   help = 'The vm id [ ]')

    # vm_config
    p = subparser.add_parser('vm_config', help = 'Return config for a vm.')
    self.__vmware_client_add_common_args(p)
    p.add_argument('vm_id', action = 'store', type = str, default = None,
                   help = 'The vm id [ ]')
    p.add_argument('key', action = 'store', type = str, default = None,
                   help = 'Config param key [ ]')

    # vm_power
    p = subparser.add_parser('vm_power', help = 'Get or set the vm power.')
    self.__vmware_client_add_common_args(p)
    p.add_argument('vm_id', action = 'store', type = str, default = None,
                   help = 'The vm id [ ]')
    p.add_argument('state', action = 'store', type = str, default = None, nargs = '?',
                   choices = ( 'on', 'off', 'shutdown', 'suspend', 'pause', 'unpause' ),
                   help = 'The new power state [ ]')

    # request
    p = subparser.add_parser('request', help = 'Make a generic request.')
    self.__vmware_client_add_common_args(p)
    p.add_argument('endpoint', action = 'store', default = None, type = str,
                   help = 'The request end point. [ None ]')
    p.add_argument('args', action = 'store', default = [], nargs = '*',
                   help = 'The script args. [ None ]')

    # vm_mac_address
    p = subparser.add_parser('vm_mac_address', help = 'Return mac_address for a vm.')
    self.__vmware_client_add_common_args(p)
    p.add_argument('vm_id', action = 'store', type = str, default = None,
                   help = 'The vm id [ ]')

    # vm_ip_address
    p = subparser.add_parser('vm_ip_address', help = 'Return ip_address for a vm.')
    self.__vmware_client_add_common_args(p)
    p.add_argument('vm_id', action = 'store', type = str, default = None,
                   help = 'The vm id [ ]')
    
  def __vmware_client_add_common_args(self, p):
    p.add_argument('-v', '--verbose', action = 'store_true', default = False,
                   help = 'Verbose output [ False ]')
    p.add_argument('-p', '--port', action = 'store', type = int, default = 8697,
                   help = 'Port [ 8697 ]')
    p.add_argument('--hostname', action = 'store', type = str, default = 'localhost',
                   help = 'Hostname [ localhost ]')
    p.add_argument('--username', action = 'store', type = str, default = None,
                   help = 'Username [ ]')
    p.add_argument('--password', action = 'store', type = str, default = None,
                   help = 'Password [ ]')
    
  def _command_vmware_client(self, command, *args, **kargs):
    from .vmware_client_cli_command import vmware_client_cli_command
    return vmware_client_cli_command(kargs).handle_command(command)