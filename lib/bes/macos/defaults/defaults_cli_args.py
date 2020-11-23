#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

class defaults_cli_args(object):

  def __init__(self):
    pass
  
  def defaults_add_args(self, subparser):

    # read_domain
    p = subparser.add_parser('read_domain', help = 'Read domain defaults.')
    p.add_argument('domain', action = 'store', default = None,
                   help = 'The domain [ None ]')
    p.add_argument('-s', '--style', action = 'store', default = 'json',
                   choices = ( 'raw', 'json', 'plist' ),
                   help = 'The output style.  Etiher json or raw [ json ]')
    
  def _command_defaults(self, command, *args, **kargs):
    from .defaults_cli_command import defaults_cli_command
    return defaults_cli_command.handle_command(command, **kargs)
