#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

import atexit
from os import path
import copy, os, tempfile
from functools import wraps

from .env_var import env_var
from .filesystem import filesystem
from .host import host
from .os_env import os_env

class env_override(object):

  def __init__(self, env = None):
    self._original_env = os_env.clone_current_env()
    self._stack = []
    if env:
      self.update(env)
    
  def __enter__(self):
    return self
  
  def __exit__(self, type, value, traceback):
    self.reset()
    
  def __getitem__(self, key):
    return os.environ.get(key)
    
  def __setitem__(self, key, value):
    os.environ[key] = value
    
  def reset(self):
    os_env.set_current_env(self._original_env)

  def push(self):
    self._stack.append(os_env.clone_current_env())

  def pop(self):
    d = self._stack.pop()
    os_env.set_current_env(d)

  def set(self, key, value):
    os.environ[key] = value
    
  def get(self, key, default_value = None):
    return os.environ.get(key, default_value)
    
  def update(self, d):
    os.environ.update(d)

  def to_dict(self):
    return copy.deepcopy(os.environ)

  
  @classmethod
  def temp_home(clazz):
    'Return an env_override object with a temporary HOME'
    tmp_dir = tempfile.mkdtemp(suffix = '.home')

    def _delete_tmp_dir(*args, **kargs):
      _arg_tmp_dir = args[0]
      filesystem.remove_directory(_arg_tmp_dir)
    atexit.register(_delete_tmp_dir, [ tmp_dir ])

    if host.is_unix():
      env = { 'HOME': tmp_dir }
    elif host.is_windows():
      homedrive, homepath = path.splitdrive(tmp_dir)
      env = {
        'HOME': tmp_dir,
        'HOMEDRIVE': homedrive,
        'HOMEPATH': homepath,
        'APPDATA': path.join(tmp_dir, 'AppData\\Roaming')
      }
    return env_override(env = env)

  @classmethod
  def clean_env(clazz):
    'Return a clean env useful for testing where a determintate clean environment is needed.'
    return env_override(env = os_env.make_clean_env())

  @classmethod
  def path_append(clazz, p):
    'Return an env_override object with p appended to PATH'
    v = env_var(os_env.clone_current_env(), 'PATH')
    v.append(p)
    env = { 'PATH': v.value }
    return env_override(env = env)

def env_override_temp_home_func():
  'A decarator to override HOME for a function.'
  def _wrap(func):
    @wraps(func)
    def _caller(self, *args, **kwargs):
      with env_override.temp_home() as env:
        return func(self, *args, **kwargs)
    return _caller
  return _wrap
