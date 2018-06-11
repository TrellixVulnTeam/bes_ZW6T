#!/usr/bin/env python
#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

import unittest
from bes.fs import temp_file
from bes.archive.archive_extension import archive_extension
from bes.archive.temp_archive import temp_archive
from bes.archive.archive_unix_tar import archive_unix_tar
from archive_base_common import archive_base_common
from bes.testing.unit_test.unit_test_skip import raise_skip

class test_archive_unix_tar(unittest.TestCase, archive_base_common):

  @classmethod
  def setUpClass(clazz):
    pass
    #raise_skip('broken')
  
  def __init__(self, methodName = 'runTest'):
    super(test_archive_unix_tar, self).__init__(methodName)
    self.default_archive_type = archive_extension.TAR

  def make_archive(self, filename):
    return archive_unix_tar(filename)

  def test_init(self):
    self.assertEqual( 'foo.tar', archive_unix_tar('foo.tar').filename )

  def test_is_valid(self):
    tmp_zip = temp_archive.make_temp_archive([ temp_archive.Item('foo.txt', content = 'foo.txt\n') ], archive_extension.ZIP)
    self.assertFalse( archive_unix_tar(tmp_zip.filename).is_valid() )

    tmp_tar = temp_archive.make_temp_archive([ temp_archive.Item('foo.txt', content = 'foo.txt\n') ], archive_extension.TAR)
    self.assertTrue( archive_unix_tar(tmp_tar.filename).is_valid() )

    tmp_tgz = temp_archive.make_temp_archive([ temp_archive.Item('foo.txt', content = 'foo.txt\n') ], archive_extension.TGZ)
    self.assertTrue( archive_unix_tar(tmp_tgz.filename).is_valid() )

    tmp_xz = temp_archive.make_temp_archive([ temp_archive.Item('foo.txt', content = 'foo.txt\n') ], archive_extension.XZ)
    self.assertTrue( archive_unix_tar(tmp_xz.filename).is_valid() )

    self.assertFalse( archive_unix_tar(temp_file.make_temp_file(content = 'junk\n')).is_valid() )

if __name__ == "__main__":
  unittest.main()
