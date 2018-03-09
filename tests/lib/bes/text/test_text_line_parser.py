#!/usr/bin/env python
#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

from bes.testing.unit_test import unit_test
from bes.text import text_line_parser as LTP

class test_text_line_parser(unit_test):

  def test_empty(self):
    l = LTP('')
    self.assertEqual( 1, len(l) )

  def test___init__with_lines(self):
    l1 = LTP('apple\nkiwi\npear\nmelon')
    self.assertEqual( 4, len(l1) )
    l2 = LTP(l1)
    self.assertEqual( 4, len(l2) )
    self.assertEqual( ( 1, 'apple' ), l2[0] )
    self.assertEqual( ( 2, 'kiwi' ), l2[1] )
    self.assertEqual( ( 3, 'pear' ), l2[2] )
    self.assertEqual( ( 4, 'melon' ), l2[3] )
    
  def test_1_line(self):
    l = LTP('foo')
    self.assertEqual( 1, len(l) )
    self.assertEqual( 'foo', l[0].text )
    
  def test_1_line_with_newline(self):
    l = LTP('foo\n')
    self.assertEqual( 2, len(l) )
    self.assertEqual( 'foo', l[0].text )
    self.assertEqual( '', l[1].text )
    
  def test_1_empty_line(self):
    l = LTP('\n')
    self.assertEqual( 2, len(l) )
    self.assertEqual( '', l[0].text )
    self.assertEqual( '', l[1].text )
    
  def test_basic(self):
    l = LTP('foo bar\napple kiwi')
    self.assertEqual( 2, len(l) )
    self.assertEqual( 'foo bar', l[0].text )
    self.assertEqual( 'apple kiwi', l[1].text )
    
  def test___setitem__(self):
    l = LTP('foo bar\napple kiwi')
    with self.assertRaises(RuntimeError) as context:
      l[0] = 'foo'

  def test_add_line_numbers(self):
    l = LTP('foo\nbar\n')
    l.add_line_numbers()
    self.assertMultiLineEqual(
      '''1|foo
2|bar
3|
''',
      str(l) )

  def test_prepend(self):
    l = LTP('foo\nbar\n')
    l.prepend('ABC: ')
    self.assertMultiLineEqual(
      '''ABC: foo
ABC: bar
ABC: 
''',
      str(l) )

  def test_append(self):
    l = LTP('foo\nbar\n')
    l.append(':ABC')
    self.assertMultiLineEqual(
      '''foo:ABC
bar:ABC
:ABC
''',
      str(l) )

  def test_continuation(self):
    text = r'''foo bar
kiwi \
apple
pear \
orange
almond \
peanut \
walnut \
rum
coke'''
    l = LTP(text)
    l.merge_continuations()
    l.add_line_numbers()
    self.assertMultiLineEqual(
      ''' 1|foo bar
 2|kiwi apple
 3|
 4|pear orange
 5|
 6|almond peanut walnut rum
 7|
 8|
 9|
10|coke''',
      str(l) )

  def test_strip_comments(self):
    text = r'''foo bar # comment
kiwi # comment
apple
pear # comment
orange
almond # comment
peanut # comment
walnut # comment
rum
coke'''
    l = LTP(text)
    self.assertMultiLineEqual(
      '''foo bar
kiwi
apple
pear
orange
almond
peanut
walnut
rum
coke''',
      l.to_string(strip_comments = True) )

  def test_to_string_list(self):
    text = r'''foo bar # comment
kiwi # comment
apple
pear # comment
orange
almond # comment
peanut # comment
walnut # comment
rum
coke'''
    self.assertEqual( [
      'foo bar # comment',
      'kiwi # comment',
      'apple',
      'pear # comment',
      'orange',
      'almond # comment',
      'peanut # comment',
      'walnut # comment',
      'rum',
      'coke'
    ], LTP(text).to_string_list() )
    
  def test_to_string_list_strip_comments(self):
    text = r'''foo bar # comment
kiwi # comment
apple
pear # comment
orange
almond # comment
peanut # comment
walnut # comment
rum
coke'''
    self.assertEqual( [
      'foo bar',
      'kiwi',
      'apple',
      'pear',
      'orange',
      'almond',
      'peanut',
      'walnut',
      'rum',
      'coke'
    ], LTP(text).to_string_list(strip_comments = True) )

  def test_parse_lines(self):
    self.assertEqual( [ 'foo', 'bar' ], LTP.parse_lines('foo\nbar\n') )
    self.assertEqual( [ 'foo', 'bar' ], LTP.parse_lines('foo\nbar') )
    self.assertEqual( [ 'foo', 'bar' ], LTP.parse_lines('\nfoo\nbar') )
    self.assertEqual( [ 'foo', 'bar' ], LTP.parse_lines('\n foo\nbar') )
    self.assertEqual( [ 'foo', 'bar' ], LTP.parse_lines('\n foo\nbar ') )
    self.assertEqual( [ 'foo', 'bar' ], LTP.parse_lines('\n foo\nbar \n') )
    self.assertEqual( [], LTP.parse_lines('\n\n\n') )
    
  def test_match_first(self):
    text = '''
    Health ID: 8573008129436468
  Test Name                                              Results                               Reference Range               Lab
     CHLORIDE                                                                      101                   98-110 mmol/L
'''
    l = LTP(text)
    patterns = [
      '^\s*Test\s+Name\s\s+Result\s\s+Flag\s\s+Reference\s+Range\s\s+Lab\s*$',
      '^\s*Test\s+Name\s\s+Results\s\s+Reference\s+Range\s\s+Lab\s*$',
    ]
    self.assertEqual( 3, l.match_first(patterns).line_number )
    
  def test_remove_empties(self):
    text = '''
    foo

    bar


    baz


'''
    l = LTP(text)
    l.remove_empties()
    self.assertEqual( [ 'foo', 'bar', 'baz' ], l.to_string_list(strip_text = True) )

  def test_strip(self):
    text = '''
    apple
    kiwi
    orange
    '''
    l = LTP(text)
    l.strip()
    self.assertEqual( [ '', 'apple', 'kiwi', 'orange', '' ], l.to_string_list() )
    
  def test_cut_lines(self):
    text = '''
    apple
    kiwi
    orange
    apricot
    banana
    watermelon
    '''
    l = LTP(text)
    l.remove_empties()
    l.strip()
    self.assertEqual( [ 'kiwi', 'orange', 'apricot' ], l.cut_lines('^ap.*$', '^ba.*$').to_string_list() )
    self.assertEqual( [ 'banana', 'watermelon' ], l.cut_lines('^apr.*$', None).to_string_list() )
    self.assertEqual( [ 'apple', 'kiwi' ], l.cut_lines(None, '^or.*$').to_string_list() )
    
  def test_find_by_line_number(self):
    text = '''apple
    kiwi
    orange
    apricot
    banana
    watermelon'''
    l = LTP(text)
    l.strip()
    self.assertEqual( 0, l.find_by_line_number(1) )
    self.assertEqual( 3, l.find_by_line_number(4) )
    self.assertEqual( 5, l.find_by_line_number(6) )
    self.assertEqual( -1, l.find_by_line_number(666) )
    
  def test_remove_line_number(self):
    text = '''apple
    kiwi
    orange
    apricot
    banana
    watermelon'''
    l = LTP(text)
    l.strip()
    self.assertEqual( None, l.remove_line_number(666) )
    self.assertEqual( ( 1, 'apple' ), l.remove_line_number(1) )
    self.assertEqual( [ 'kiwi', 'orange', 'apricot', 'banana', 'watermelon' ], l.to_string_list() )
    self.assertEqual( ( 6, 'watermelon' ), l.remove_line_number(6) )
    self.assertEqual( [ 'kiwi', 'orange', 'apricot', 'banana' ], l.to_string_list() )
    self.assertEqual( ( 4, 'apricot' ), l.remove_line_number(4) )
    self.assertEqual( [ 'kiwi', 'orange', 'banana' ], l.to_string_list() )
    
  def test_remove_line_number(self):
    text = '''apple
    kiwi
    orange
    apricot
    banana
    watermelon'''
    l = LTP(text)
    l.strip()
    l.combine_lines(1, 2)
    self.assertEqual( [ 'apple kiwi', 'orange', 'apricot', 'banana', 'watermelon' ], l.to_string_list() )
    l.combine_lines(5, 6)
    self.assertEqual( [ 'apple kiwi', 'orange', 'apricot', 'banana watermelon' ], l.to_string_list() )
    l.combine_lines(3, 4)
    self.assertEqual( [ 'apple kiwi', 'orange apricot', 'banana watermelon' ], l.to_string_list() )
    l.combine_lines(1, 3)
    self.assertEqual( [ 'apple kiwi orange apricot', 'banana watermelon' ], l.to_string_list() )
    l.combine_lines(1, 5)
    self.assertEqual( [ 'apple kiwi orange apricot banana watermelon' ], l.to_string_list() )
    
  def test_match_all(self):
    text = '''apple
    kiwi
    orange
    apricot
    banana
    watermelon'''
    l = LTP(text)
    l.strip()
    self.assertEqual( [ ( 1, 'apple' ), ( 4, 'apricot' ) ], l.match_all('^a.*$') )
    self.assertEqual( [], l.match_all('^nothere.*$') )
    self.assertEqual( [ ( 1, 'apple' ) ], l.match_all('^app.*$') )

  def test_match_backwards(self):
    text = '''apple
    kiwi
    orange
    apricot
    banana
    watermelon'''
    l = LTP(text)
    l.strip()
    self.assertEqual( ( 2, 'kiwi' ), l.match_backwards(5, '^ki.*$') )
    
if __name__ == '__main__':
  unit_test.main()
