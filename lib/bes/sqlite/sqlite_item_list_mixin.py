#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

from bes.system.check import check

class sqlite_item_list_mixin:
  '''
  This mixing assumes that "self" is an instance of type_checked_list
  '''

  @classmethod
  def from_sql_rows(clazz, rows):
    check.check_list(rows, tuple)

    item_type = getattr(clazz, '__value_type__', None)
    if not item_type:
      raise AttributeError('No "__value_type__" attribute found in {clazz}')
    result = clazz()
    for row in rows:
      item = item_type.from_sql_row(row)
      result.append(item)
    return result
