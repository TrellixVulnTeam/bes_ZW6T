#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

import ast, os.path as path
from bes.common.algorithm import algorithm
from bes.fs.file_util import file_util
from bes.system.compat import compat
from .unit_test_description import unit_test_description

import unittest

class unit_test_inspect(object):

  @classmethod
  def inspect_file(clazz, filename, unit_test_class_names = None):
    old = []
    new = []
    try:
      old = clazz.inspect_file_old(filename, unit_test_class_names)
    except Exception as ex:
      print('WARNING: failed to inspect unit test %s: %s' % (path.relpath(filename), str(ex)))
      raise
      #return None
    try:
      new = clazz.inspect_file_new(filename, unit_test_class_names)
    except Exception as ex:
      #print('WARNING: failed to inspect unit test %s: %s' % (path.relpath(filename), str(ex)))
      #return None
      pass
    return sorted(algorithm.unique(old + new), key = lambda x: x.function)
    
  @classmethod
  def inspect_file_new(clazz, filename, unit_test_class_names):
    loader = unittest.TestLoader()
    where = path.dirname(filename)
    pattern = path.basename(filename)
    discovery = loader.discover(where, pattern = pattern)
    result = []
    for disc in discovery:
      for suite in disc:
        for test in suite:
          fixture = test.__class__.__name__
          test_functions = loader.getTestCaseNames(test)
          for function in test_functions:
            result.append(unit_test_description(filename, fixture, function))
    return sorted(algorithm.unique(result), key = lambda x: x.function)

  @classmethod
  def inspect_file_old(clazz, filename, unit_test_class_names):
    code = file_util.read(filename)
    tree = ast.parse(code, filename = filename)
    s = ast.dump(tree, annotate_fields = True, include_attributes = True)
    result = []
    for node in tree.body:
      if clazz._node_is_unit_test_class(node, unit_test_class_names):
        for statement in node.body:
          if isinstance(statement, ast.FunctionDef):
            if statement.name.startswith('test_'):
              result.append(unit_test_description(filename, node.name, statement.name))
    return sorted(result, key = lambda x: x.function)

  _DEFAULT_UNIT_TEST_CLASS_NAMES = ( 'unittest.TestCase', 'unit_test', 'program_unit_test' )
  @classmethod
  def _node_is_unit_test_class(clazz, node, unit_test_class_names):
    unit_test_class_names = unit_test_class_names or ()
    unit_test_class_names = unit_test_class_names + clazz._DEFAULT_UNIT_TEST_CLASS_NAMES
    if not isinstance(node, ast.ClassDef):
      return False
    for i, base in enumerate(node.bases):
      base_class_name = clazz._base_class_name(base)
      if base_class_name in unit_test_class_names:
        return True
      print('missed base_class_name={}'.format(base_class_name))
    return False
    
  @classmethod
  def _base_class_name(clazz, base):
    result = []
    for field in base._fields:
      value = getattr(base, field)
      if isinstance(value, ast.Name):
        result.append(value.id)
      elif compat.is_string(value):
        result.append(value)
    return '.'.join(result)
  
