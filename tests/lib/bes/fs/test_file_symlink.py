#!/usr/bin/env python
#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

import os, os.path as path, tempfile
from bes.testing.unit_test import unit_test
from bes.fs.file_symlink import file_symlink
from bes.fs.file_util import file_util

class test_file_symlink(unit_test):

  def test_is_broken_true(self):
    tmp = tempfile.NamedTemporaryFile()
    file_util.remove(tmp.name)
    os.symlink('/somethingnotthere', tmp.name)
    self.assertEqual( True, path.islink(tmp.name) )
    self.assertEqual( True, file_symlink.is_broken(tmp.name) )

  def test_is_broken_false(self):
    tmp1 = tempfile.NamedTemporaryFile()
    tmp2 = tempfile.NamedTemporaryFile()
    file_util.remove(tmp1.name)
    os.symlink(tmp2.name, tmp1.name)
    self.assertEqual( True, path.islink(tmp1.name) )
    self.assertEqual( False, file_symlink.is_broken(tmp1.name) )

if __name__ == "__main__":
  unit_test.main()
