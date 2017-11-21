#!/usr/bin/env python
#-*- coding:utf-8 -*-
#
import unittest
from bes.common import string_list

class test_string_list(unittest.TestCase):

  def test_remove_if(self):
    f = string_list.remove_if
    self.assertEqual( [ 'a', 'b', 'c' ], f( [ 'a', 'b', 'c' ], [] ) )
    self.assertEqual( [], f( [ 'a', 'b', 'c' ], [ 'a', 'b', 'c' ] ) )
    self.assertEqual( [ 'a' ], f( [ 'a', 'b', 'c' ], [ 'b', 'c' ] ) )

  def test_to_string(self):
    f = string_list.to_string
    self.assertEqual( 'a;b;c', f([ 'a', 'b', 'c' ]) )
    self.assertEqual( 'a b c', f([ 'a', 'b', 'c' ], delimiter = ' ') )
    self.assertEqual( '"a x" b c', f([ 'a x', 'b', 'c' ], delimiter = ' ', quote = True) )
    
if __name__ == "__main__":
  unittest.main()
