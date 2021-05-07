#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

from bes.credentials.credentials import credentials
from bes.common.check import check
from bes.cli.cli_options import cli_options
from bes.fs.file_util import file_util

from .git_error import git_error
from .git_clone_options import git_clone_options

class git_download_options(git_clone_options):
  
  def __init__(self, **kargs):
    super(git_download_options, self).__init__(**kargs)

  @classmethod
  #@abstractmethod
  def default_values(clazz):
    'Return a dict of defaults for these options.'
    v = super(git_download_options, clazz).default_values()
    v.update({
      'verbose': False,
      'ssh_public_key': None,
      'ssh_private_key': None,
    })
    return v

  @classmethod
  #@abstractmethod
  def sensitive_keys(clazz):
    'Return list of keys that are secrets and should be protected from __str__.'
    return ( 'ssh_public_key', 'ssh_private_key' )

  @classmethod
  #@abstractmethod
  def value_type_hints(clazz):
    v = super(git_download_options, clazz).value_type_hints()
    v.update({
      'verbose': bool,
    })
    return v

  @classmethod
  #@abstractmethod
  def config_file_key(clazz):
    return super(git_download_options, clazz).config_file_key()

  @classmethod
  #@abstractmethod
  def config_file_env_var_name(clazz):
    return super(git_download_options, clazz).config_file_env_var_name()
  
  @classmethod
  #@abstractmethod
  def config_file_section(clazz):
    return super(git_download_options, clazz).config_file_section()

  @classmethod
  #@abstractmethod
  def error_class(clazz):
    return git_error

  #@abstractmethod
  def check_value_types(self):
    'Check the type of each option.'
    super(git_download_options, self).check_value_types()
    check.check_bool(self.verbose)
    check.check_string(self.ssh_public_key, allow_none = True)
    check.check_string(self.ssh_private_key, allow_none = True)
  
  @property
  def ssh_key_pair(self):
    if self.ssh_public_key and not self.ssh_private_key:
      raise git_error('both ssh_public_key and ssh_private_key need to be given.')
    if self.ssh_private_key and not self.ssh_public_key:
      raise git_error('both ssh_private_key and ssh_public_key need to be given.')
    if not self.ssh_public_key:
      assert not self.ssh_private_key
      return None
    try:
      ssh_public_key_content = file_util.read(self.ssh_public_key, codec = 'utf-8')
    except Exception as ex:
      raise git_error('Failed to ready public ssh key: "{}" - {}'.format(self.ssh_public_key,
                                                                         str(ex)))
    try:
      ssh_private_key_content = file_util.read(self.ssh_private_key, codec = 'utf-8')
    except Exception as ex:
      raise git_error('Failed to ready private ssh key: "{}" - {}'.format(self.ssh_private_key,
                                                                         str(ex)))
    return credentials('<cli>',
                       ssh_public_key = ssh_public_key_content,
                       ssh_private_key = ssh_private_key_content)
    
check.register_class(git_download_options)
