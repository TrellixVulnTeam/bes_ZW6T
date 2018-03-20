#!/usr/bin/env python
#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

from bes.testing.unit_test import unit_test
from bes.text import comments

class test_comments(unit_test):

  def test_strip_line(self):
    self.assertEqual( 'foo ', comments.strip_line('foo #comment') )
    self.assertEqual( 'foo', comments.strip_line('foo#comment') )
    self.assertEqual( 'foo', comments.strip_line('foo #comment', strip_tail = True) )
    self.assertEqual( ' foo', comments.strip_line(' foo #comment', strip_tail = True) )
    self.assertEqual( 'foo ', comments.strip_line(' foo #comment', strip_head = True) )
    
  def test_strip_line_with_quoted_hash(self):
    self.assertEqual( 'ab "cd # ef"', comments.strip_line('ab "cd # ef"') )
    self.assertEqual( 'ab "cd # ef"', comments.strip_line('ab "cd # ef"#comment') )
    self.assertEqual( '', comments.strip_line('#ab "cd # ef"') )
    self.assertEqual( '"#"', comments.strip_line('"#"') )
    
  def test_strip_line_with_strip(self):
    self.assertEqual( 'foo', comments.strip_line('foo #comment', strip_tail = True) )

  def test_strip_strip_multi_line(self):
    text = '''
foo_# comment
# comment
bar
'''
    expected = '''
foo_

bar
'''
    self.assertEqual( expected, comments.strip_multi_line(text) )

  def test_strip_strip_multi_line_with_strip(self):
    text = '''
foo # comment
# comment
bar
'''
    expected = '''
foo

bar
'''
    self.assertEqual( expected, comments.strip_multi_line(text, strip_tail = True) )

  def test_strip_strip_multi_line_remove_empties(self):
    text = '''
foo_# comment
# comment
bar
'''
    expected = '''foo_
bar'''
    self.assertEqual( expected, comments.strip_multi_line(text, remove_empties = True) )
    
  def test_strip_strip_multi_line_with_strip_and_remove_empties(self):
    text = '''
foo # comment
# comment
bar
'''
    expected = '''foo
bar'''
    self.assertEqual( expected, comments.strip_multi_line(text, strip_tail = True, remove_empties = True) )
    
if __name__ == '__main__':
  unit_test.main()
