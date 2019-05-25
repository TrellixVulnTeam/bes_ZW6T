#!/usr/bin/env python
#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

from os import path
from bes.fs import file_util, temp_file

from bes.testing.unit_test import unit_test
from bes.config_file.config_file_editor import config_file_editor as CFE

class test_config_file_editor(unit_test):

  def test_set_value_non_existent_file(self):
    'Set the first value for a non existent config file.'
    tmp = temp_file.make_temp_file()
    file_util.remove(tmp)
    e = CFE(tmp)
    e.set_value('something', 'fruit', 'kiwi')
    expected = '''\
[something]
fruit = kiwi
'''
    self.assertMultiLineEqual(expected, file_util.read(tmp, codec = 'utf-8') )
    
  def test_replace_value(self):
    'Set the first value for a non existent config file.'
    tmp = temp_file.make_temp_file()
    file_util.remove(tmp)
    e = CFE(tmp)
    e.set_value('something', 'fruit', 'kiwi')
    expected = '''\
[something]
fruit = kiwi
'''
    self.assertMultiLineEqual(expected, file_util.read(tmp, codec = 'utf-8') )
    e.set_value('something', 'fruit', 'apple')
    expected = '''\
[something]
fruit = apple
'''
    self.assertMultiLineEqual(expected, file_util.read(tmp, codec = 'utf-8') )
    
  def test_set_value_existing_file(self):
    'Add a second property to an existing property file.'
    content = '''\
[something]
fruit = kiwi
'''
    tmp = temp_file.make_temp_file(content = content)
    e = CFE(tmp)
    self.assertMultiLineEqual(content, file_util.read(tmp, codec = 'utf-8') )
    self.assertEqual( 'kiwi', e.get_value('something', 'fruit') )
    
  def test_bump_version(self):
    content = '''\
[something]
ver = 1.2.3
'''
    e = CFE(temp_file.make_temp_file(content = content))
    self.assertEqual( '1.2.3', e.get_value('something', 'ver') )
    e.bump_version('something', 'ver', 'revision')
    self.assertEqual( '1.2.4', e.get_value('something', 'ver') )
    e.bump_version('something', 'ver', 'major')
    self.assertEqual( '2.2.4', e.get_value('something', 'ver') )
    e.bump_version('something', 'ver', 'major', reset_lower = True)
    self.assertEqual( '3.0.0', e.get_value('something', 'ver') )
    e.bump_version('something', 'ver', 'minor')
    self.assertEqual( '3.1.0', e.get_value('something', 'ver') )
    
if __name__ == '__main__':
  unit_test.main()
