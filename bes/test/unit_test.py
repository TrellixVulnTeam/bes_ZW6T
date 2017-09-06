#!/usr/bin/env python
#-*- coding:utf-8 -*-

import inspect, os, os.path as path, re, unittest
from StringIO import StringIO
from bes.system import host

# FIXME: dont import bes stuff here 
FOO='''
platform
    __system = platform.system()
    if __system == 'Linux':
      return 'linux'
    elif __system == 'Darwin':
      return 'macos'
    else:
      raise RuntimeError('Unknown system: %s' % (__system))
'''

class unit_test(unittest.TestCase):
  'Helper for writing unit tests.'
  
  def data_path(self, filename, platform_specific = False): 
    assert filename
    return path.join(self.data_dir(platform_specific = platform_specific), filename)

  def platform_data_path(self, filename): 
    return self.data_path(filename, platform_specific = True)

  def data_dir(self, platform_specific = False): 
    parts = [ self.__class__._get_data_dir() ]
    if platform_specific:
      parts.append(host.SYSTEM)
    return path.join(*parts)

  def platform_data_dir(self): 
    return self.data_dir(platform_specific = True)

  def data(self, filename, platform_specific = False):
    data_path = self.data_path(filename, platform_specific = platform_specific)
    with open(data_path, 'r') as fin:
      return fin.read()

  def assert_string_equal_ws(self, s1, s2):
    self.maxDiff = None
    s1 = re.sub('\s+', ' ', s1)
    s2 = re.sub('\s+', ' ', s2)
    self.assertEqual( s1, s2 )

  def assert_string_equal_strip(self, s1, s2):
    self.maxDiff = None
    self.assertEqual( s1.strip(), s2.strip() )

  def assert_file_content_equal(self, expected, filename, strip = True):
    self.maxDiff = None
    with open(filename, 'r') as fin:
      content = fin.read()
      if strip:
        expected = expected.strip()
        content = content.strip()
    self.assertEqual( expected, content )
    
  @classmethod
  def _get_data_dir(clazz): 
    right = getattr(clazz, '__unit_test_data_dir__', None)
    if not right:
      raise RuntimeError('%s does not have a __unit_test_data_dir__ attribute.' % (clazz))
    left = path.dirname(inspect.getfile(clazz))
    return path.join(left, right)

  def assert_bit_string_equal(self, b1, b2, size):
    bs1 = bin(b1)[2:].zfill(size)
    bs2 = bin(b2)[2:].zfill(size)
    self.assertEqual( bs1, bs2)

  def assert_bytes_equal(self, expected, actual):
    expected = self.bytes_to_string(expected)
    actual = self.bytes_to_string(actual)
    msg = '\nexpected: %s\n  actual: %s\n' % (expected, actual)
    self.assertEqual( expected, actual, msg = msg)

  @classmethod
  def bytes_to_string(clazz, b):
    s = b.encode('hex')
    assert (len(s) % 2) == 0
    buf = StringIO()
    for i in range(0, len(s), 2):
      if i != 0:
        buf.write(' ')
      buf.write(s[i])
      buf.write(s[i + 1])
    return buf.getvalue()

  @classmethod
  def decode_hex(clazz, s):
    buf = StringIO()
    for c in s:
      if not c.isspace():
        buf.write(c)
    return buf.getvalue().decode('hex')
  
  @staticmethod
  def main(): 
    unittest.main()

  @classmethod
  def file_path(clazz, unit_test_filename, filename):
    'Return an absolute normalized path for a file relative to this unit test.'
    p = path.abspath(path.normpath(path.join(path.dirname(unit_test_filename), filename)))
    if not path.exists(p):
      raise RuntimeError('file not found: %s' % (p))
    if not os.access(p, os.X_OK):
      raise RuntimeError('file not executable: %s' % (p))
    return p
