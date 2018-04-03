#!/usr/bin/env python
#-*- coding:utf-8 -*-

import json, os.path as path, hashlib
from collections import namedtuple
from bes.common import check, json_util, object_util, type_checked_list
from .file_check import file_check
from .file_util import file_util

class file_checksum(namedtuple('file_checksum', 'filename,checksum')):

  def __new__(clazz, filename, checksum):
    check.check_string(filename)
    check.check_string(checksum)
    return clazz.__bases__[0].__new__(clazz, filename, checksum)

  @classmethod
  def from_file(clazz, filename, root_dir = None):
    if root_dir:
      filepath = path.join(root_dir, filename)
    else:
      filepath = filename
    file_check.check_file(filepath)
    content = file_util.read(filepath)
    checksum = hashlib.sha1(content).hexdigest()
    return clazz(filename, checksum)

  @classmethod
  def file_checksum(clazz, filename):
    return clazz.from_file(filename).checksum

class file_checksum_list(type_checked_list):

  def __init__(self, values = None):
    super(file_checksum_list, self).__init__(file_checksum, values = values)

  def to_json(self):
    return json_util.to_json(self._values, indent = 2)
    
  @classmethod
  def from_json(clazz, text):
    o = json.loads(text)
    check.check_list(o)
    result = clazz()
    for item in o:
      check.check_list(item, check.STRING_TYPES)
      assert len(item) == 2
      result.append(file_checksum(item[0], item[1]))
    return result
    
  @classmethod
  def from_files(clazz, filenames, root_dir = None):
    filenames = object_util.listify(filenames)
    result = clazz()
    for filename in filenames:
      result.append(file_checksum.from_file(filename, root_dir = root_dir))
    return result

  def save_checksums_file(self, filename):
    file_util.save(filename, content = self.to_json(), codec = 'utf8')

  @classmethod
  def load_checksums_file(clazz, filename):
    try:
      content = file_util.read(filename)
    except IOError as ex:
      return None
    return clazz.from_json(content)
  
  def filenames(self):
    return [ c.filename for c in self ]

  def reload(self, root_dir = None):
    new_values = []
    for value in self:
      new_values.append(file_checksum.from_file(value.filename, root_dir = root_dir))
    self._values = new_values
  
  def verify(self, root_dir = None):
    current = self[:]
    current.reload(root_dir = root_dir)
    return self == current
