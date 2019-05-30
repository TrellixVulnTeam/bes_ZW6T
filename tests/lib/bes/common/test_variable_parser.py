#!/usr/bin/env python
#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

import unittest
from bes.common.variable_parser import variable_parser as P, variable_token as V, variable_parser_error as VPE
from bes.common import point

class test_variable_parser(unittest.TestCase):

  def test_empty_string(self):
    self.assertEqual( [], self._parse('') )

  def test_dollar_just_var_sign(self):
    self.assertEqual( [ V('foo', '$foo', None, point(1, 1), point(4, 1)) ], self._parse('$foo') )

  def test_no_variables(self):
    self.assertEqual( [], self._parse('this is foo') )
    
  def test_escaped_dollar_sign(self):
    self.assertEqual( [], self._parse('this is \$foo') )

  def test_no_bracket_start(self):
    self.assertEqual( [ V('foo', '$foo', None, point(1, 1), point(4, 1)) ], self._parse('$foo bar') )
    
  def test_no_bracket_doubles(self):
    self.assertEqual( [
      V('foo', '$foo', None, point(1, 1), point(4, 1)),
      V('bar', '$bar', None, point(5, 1), point(8, 1)),
    ], self._parse('$foo$bar') )
    
  def test_no_bracket_doubles_escaped_dollar(self):
    self.assertEqual( [ V('bar', '$bar', None, point(6, 1), point(9, 1)) ], self._parse('\$foo$bar') )
    self.assertEqual( [ V('foo', '$foo', None, point(1, 1), point(4, 1)) ], self._parse('$foo\$bar') )
    
  def test_no_bracket_end(self):
    self.assertEqual( [ V('bar', '$bar', None, point(5, 1), point(8, 1)) ], self._parse('foo $bar') )
    
  def test_bracket_start(self):
    self.assertEqual( [ V('foo', '${foo}', None, point(1, 1), point(6, 1)) ], self._parse('${foo} bar') )
    
  def test_bracket_end(self):
    self.assertEqual( [ V('bar', '${bar}', None, point(5, 1), point(10, 1)) ], self._parse('foo ${bar}') )
    
  def test_simple_no_bracket(self):
    self.assertEqual( [ V('foo', '$foo', None, point(1, 1), point(4, 1)) ], self._parse('$foo') )
    self.assertEqual( [ V('foo', '$foo', None, point(1, 1), point(4, 1)) ], self._parse('$foo ') )
    self.assertEqual( [ V('foo', '$foo', None, point(2, 1), point(5, 1)) ], self._parse(' $foo') )
    self.assertEqual( [ V('foo', '$foo', None, point(2, 1), point(5, 1)) ], self._parse(' $foo ') )
    self.assertEqual( [ V('foo', '$foo', None, point(2, 1), point(5, 1)) ], self._parse('x$foo:') )
  
  def test_simple_bracket(self):
    self.assertEqual( [ V('foo', '${foo}', None, point(1, 1), point(6, 1)) ], self._parse('${foo}') )
    self.assertEqual( [ V('foo', '${foo}', None, point(1, 1), point(6, 1)) ], self._parse('${foo}x') )
    self.assertEqual( [ V('foo', '${foo}', None, point(2, 1), point(7, 1)) ], self._parse('x${foo}') )
    self.assertEqual( [ V('foo', '${foo}', None, point(2, 1), point(7, 1)) ], self._parse('x${foo}x') )
    self.assertEqual( [ V('foo', '${foo}', None, point(1, 1), point(6, 1)) ], self._parse('${foo} ') )
    self.assertEqual( [ V('foo', '${foo}', None, point(2, 1), point(7, 1)) ], self._parse(' ${foo}') )
    self.assertEqual( [ V('foo', '${foo}', None, point(2, 1), point(7, 1)) ], self._parse(' ${foo} ') )
    
  def test_simple_parentesis(self):
    self.assertEqual( [ V('foo', '$(foo)', None, point(1, 1), point(6, 1)) ], self._parse('$(foo)') )
    self.assertEqual( [ V('foo', '$(foo)', None, point(1, 1), point(6, 1)) ], self._parse('$(foo)x') )
    self.assertEqual( [ V('foo', '$(foo)', None, point(2, 1), point(7, 1)) ], self._parse('x$(foo)') )
    self.assertEqual( [ V('foo', '$(foo)', None, point(2, 1), point(7, 1)) ], self._parse('x$(foo)x') )
    self.assertEqual( [ V('foo', '$(foo)', None, point(1, 1), point(6, 1)) ], self._parse('$(foo) ') )
    self.assertEqual( [ V('foo', '$(foo)', None, point(2, 1), point(7, 1)) ], self._parse(' $(foo)') )
    self.assertEqual( [ V('foo', '$(foo)', None, point(2, 1), point(7, 1)) ], self._parse(' $(foo) ') )

  def test_bracket_with_default(self):
    self.assertEqual( [ V('foo', '${foo:-42}', '42', point(1, 1), point(10, 1)) ], self._parse('${foo:-42}') )
    self.assertEqual( [ V('foo', '$(foo:-42)', '42', point(1, 1), point(10, 1)) ], self._parse('$(foo:-42)') )
    
  def test_bracket_with_default_only_dash(self):
    self.assertEqual( [ V('foo', '${foo-42}', '42', point(1, 1), point(9, 1)) ], self._parse('${foo-42}') )
    self.assertEqual( [ V('foo', '$(foo-42)', '42', point(1, 1), point(9, 1)) ], self._parse('$(foo-42)') )
    
  def test_error_default_body_variable(self):
    with self.assertRaises(VPE) as ctx:
      self._parse('${foo:-$bar}')
    self.assertTrue( 'variables not allowed in defaults' in ctx.exception.message )
    
  def test_error_default_body_missing_dash(self):
    with self.assertRaises(VPE) as ctx:
      self._parse('${foo:$bar}')
    self.assertTrue( 'expecting "-" instead of: $' in ctx.exception.message )

  def test_error_premature_end_of_string_dollar(self):
    with self.assertRaises(VPE) as ctx:
      self._parse('$')
    self.assertTrue( 'unexpected end of string' in ctx.exception.message )
      
  def test_error_eos_bracket(self):
    with self.assertRaises(VPE) as ctx:
      self._parse('${foo')
    self.assertTrue( 'unexpected end of string' in ctx.exception.message )
    
  def test_error_eos_parentesis(self):
    with self.assertRaises(VPE) as ctx:
      self._parse('${foo')
    self.assertTrue( 'unexpected end of string' in ctx.exception.message )

  def test_error_eos_bracket_default(self):
    with self.assertRaises(VPE) as ctx:
      self._parse('${foo:-goo')
    self.assertTrue( 'unexpected end of string' in ctx.exception.message )
    
  def test_error_eos_bracket_default_colon_dash(self):
    with self.assertRaises(VPE) as ctx:
      self._parse('${foo:-')
    self.assertTrue( 'unexpected end of string' in ctx.exception.message )
    
  def test_error_eos_bracket_default_dash(self):
    with self.assertRaises(VPE) as ctx:
      self._parse('${foo-')
    self.assertTrue( 'unexpected end of string' in ctx.exception.message )
    
  @classmethod
  def _parse(self, text):
    return [ v for v in P.parse(text) ]

if __name__ == "__main__":
  unittest.main()
