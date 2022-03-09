#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

import sqlite3
import os.path as path
from collections import namedtuple

from bes.common.check import check
from bes.common.string_util import string_util
from bes.fs.file_util import file_util
from bes.system.log import log

class sqlite(object):

  # https://stackoverflow.com/questions/16335772/mapping-result-rows-to-namedtuple-in-python-sqlite
  @staticmethod
  def _namedtuple_factory(cursor, row):
    'Returns sqlite rows as named tuples'
    fields = [ col[0] for col in cursor.description ]
    _row_class = namedtuple('_row', fields)
    return _row_class(*row)

  def __init__(self, filename, log_tag = None):
    log.add_logging(self, tag = log_tag or 'sqlite')
    self.log_i('sqlite(filename=%s)' % (filename))
    self._filename = filename
    if self._filename != ':memory:':
      file_util.ensure_file_dir(self._filename)
    self._filename_log_label = path.basename(self._filename)
    self._connection = sqlite3.connect(self._filename, isolation_level = 'IMMEDIATE')
    self._cursor = self._connection.cursor()

  @property
  def filename(self):
    return self._filename
    
  @property
  def fetch_namedtuples(self):
    return self._connection.row_factory != None
    
  @fetch_namedtuples.setter
  def fetch_namedtuples(self, value):
    check.check_bool(value)
    if value == self.fetch_namedtuples:
      return
    if value:
      self._connection.row_factory = sqlite._namedtuple_factory
    else:
      self._connection.row_factory = None
    self._cursor = self._connection.cursor()
      
  def execute(self, sql, *args, **kwargs):
    self.log_i('%s: execute(%s, %s, %s)' % (self._filename_log_label, sql, args, kwargs))
    try:
      self._cursor.execute(sql, *args, **kwargs)
    except Exception as ex:
      print('Failed execute SQL: %s' % (sql))
      raise
      
  def executemany(self, sql, *args, **kwargs):
    self.log_i('%s: executemany(%s, %s, %s)' % (self._filename_log_label, sql, args, kwargs))
    try:
      self._cursor.executemany(sql, *args, **kwargs)
    except Exception as ex:
      print('Failed executemany SQL: %s' % (sql))
      raise
      
  def begin(self):
    self.log_i('%s: begin()' % (self._filename_log_label))
    self._cursor.execute('begin transaction')
   
  def commit(self):
    self.log_i('%s: commit()' % (self._filename_log_label))
    self._connection.commit()
   
  def rollback(self):
    self.log_i('%s: rollback()' % (self._filename_log_label))
    self._cursor.execute('rollback')
   
  def executescript(self, sql, *args, **kwargs):
    self.log_i('%s: executescript(%s)' % (self._filename_log_label, sql))
    self._cursor.executescript(sql, *args, **kwargs)

  def has_table(self, table_name):
    check.check_string(table_name)

    self._cursor.execute('select count(*) from sqlite_master where type=? and name=?',
                         ( 'table', table_name, ))
    return self._cursor.fetchone()[0] == 1
    
  def has_index(self, index_name):
    check.check_string(index_name)
    
    self._cursor.execute('select count(*) from sqlite_master where type=? and name=?',
                         ( 'index', index_name, ))
    return self._cursor.fetchone()[0] == 1
  
  def ensure_table(self, table_name, table_schema):
    check.check_string(table_name)
    check.check_string(table_schema)
    if self.has_table(table_name):
      return
    self._cursor.execute(table_schema)

  def ensure_index(self, index_name, index_schema):
    check.check_string(index_name)
    check.check_string(index_schema)
    if self.has_index(index_name):
      return
    self._cursor.execute(index_schema)
    
  def fetchone(self):
    return self._cursor.fetchone()

  def fetchall(self):
    return self._cursor.fetchall()
  
  def select_all(self, sql, *args, **kwargs):
    self.execute(sql, *args, **kwargs)
    return self.fetchall()

  def select_one(self, sql, *args, **kwargs):
    self.execute(sql, *args, **kwargs)
    return self.fetchone()

  def select_namedtuples(self, sql, *args, **kwargs):
    save_fetch_namedtuples = self.fetch_namedtuples
    self.fetch_namedtuples = True
    try:
      self.execute(sql, *args, **kwargs)
      return self.fetchall()
    finally:
      self.fetch_namedtuples = save_fetch_namedtuples
  
  def create_function(self, name, num_params, func):
    self.log_i('%s: create_function(%s, %s, %s)' % (self._filename_log_label, name, num_params, func))
    self._connection.create_function(name, num_params, func)

  @classmethod
  def encode_string(clazz, s, quoted = True):
    if s is None:
      return 'null'
    if quoted:
      return string_util.quote(s, quote_char = "'")
    return s
    
  @classmethod
  def encode_bool(clazz, value):
    return 'false' if value else 'true'

  @property
  def user_version(self):
    self._cursor.execute('PRAGMA user_version')
    return self._cursor.fetchone()[0]
    
  @user_version.setter
  def user_version(self, user_version):
    check.check_int(user_version)
    
    self._cursor.execute(f'PRAGMA user_version = {user_version}')
    self.commit()
