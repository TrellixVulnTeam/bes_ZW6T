#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

from ..system.check import check

from .sqlite_error import sqlite_error

class sqlite_item_mixin:
  'This mixing assumes that "self" is a namedtuple'

  def sql_for_insert(self, table_name):
    check.check_string(table_name)
    
    fields = self._fields
    values = ', '.join('?' * len(fields))
    keys = ', '.join(fields)
    return f'insert into {table_name}({keys}) values({values})'

  def sql_for_replace(self, table_name):
    check.check_string(table_name)

    fields = self._fields
    values = ', '.join('?' * len(fields))
    keys = ', '.join(fields)
    return f'replace into {table_name}({keys}) values({values})'

  @classmethod
  def from_sql_row(clazz, row, error_class = None):
    check.check_tuple(row)
    check.check_class(error_class, allow_none = True)

    error_class = error_class or sqlite_error
    
    length = len(row)
    expected_length = len(clazz._fields)
    if len(row) != len(clazz._fields):
      raise error_class(f'Length of row should be {expected_length} instead of {length} - {row}')
    return clazz(*row)
  
