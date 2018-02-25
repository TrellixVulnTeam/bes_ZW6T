#!/usr/bin/env python
#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

import fnmatch, os.path as path
from collections import namedtuple
from bes.common import algorithm, check

class file_filter(object):
  file_and_tests = namedtuple('file_and_tests', 'filename,tests')

  @classmethod
  def caca_filter_files(clazz, files, test_map, patterns):
    if not patterns:
      return [ clazz.file_and_tests(filename, None) for filename in files ]
    result = []
    for filename in files:
      assert filename in test_map
      test_map_for_filename = test_map[filename]
      matching_tests = clazz._matching_tests(test_map_for_filename, patterns)
      if matching_tests:
        result.append(clazz.file_and_tests(filename, matching_tests))
    return result

  @classmethod
  def filter_files(clazz, finfos, test_map, patterns):
    if not patterns:
      return [ clazz.file_and_tests(finfo, None) for finfo in finfos ]
    result = []
    for finfo in finfos:
      assert finfo.filename in test_map
      test_map_for_finfo = test_map[finfo.filename]
      matching_tests = clazz._matching_tests(test_map_for_finfo, patterns)
      if matching_tests:
        result.append(clazz.file_and_tests(finfo, matching_tests))
    return result

  @classmethod
  def _matching_tests(clazz, test_map, patterns):
    result = []
    for test in test_map:
      for pattern in patterns:
        fixture_matches = True
        if pattern.fixture:
          fixture_matches = fnmatch.fnmatch(test.fixture.lower(), pattern.fixture.lower())
        function_matches = True
        if pattern.function:
          function_matches = fnmatch.fnmatch(test.function.lower(), pattern.function.lower())
        if fixture_matches and function_matches:
          result.append(test)
    return result

  @classmethod
  def ignore_files(clazz, filtered_files, ignore_patterns):
    return [ f for f in filtered_files if not clazz.filename_matches_any_pattern(f.filename, ignore_patterns) ]

  @classmethod
  def filenames(clazz, filtered_files):
    return sorted([ f.filename for f in filtered_files ])

  @classmethod
  def common_prefix(clazz, filtered_files):
    return path.commonprefix([f.filename for f in filtered_files]).rpartition(os.sep)[0]
  
  @classmethod
  def filename_matches_any_pattern(clazz, filename, patterns):
    for pattern in patterns:
      if fnmatch.fnmatch(filename, pattern):
        return True
    return False
  
  @classmethod
  def env_dirs(clazz, filtered_files):
    filenames = [ f.filename for f in filtered_files ]
    roots = [ clazz._test_file_get_root(f) for f in filenames ]
    roots = algorithm.unique(roots)
    roots = [ f for f in roots if f ]
    result = []
    for root in roots:
      env_dir = path.join(root, 'env')
      if path.isdir(env_dir):
        result.append(env_dir)
    return result
  
  @classmethod
  def _test_file_get_root(clazz, filename):
    if '/lib/' in filename:
      return filename.partition('/lib')[0]
    elif '/bin/' in filename:
      return filename.partition('/bin')[0]
    else:
      return None
