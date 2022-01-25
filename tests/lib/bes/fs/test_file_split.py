#!/usr/bin/env python
#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

import math
import random
import string
from datetime import datetime
from datetime import timedelta

from bes.archive.temp_archive import temp_archive
from bes.fs.file_split import file_split
from bes.fs.file_split_options import file_split_options
from bes.fs.file_split import file_split
from bes.fs.file_util import file_util
from bes.fs.testing.temp_content import temp_content
from bes.testing.unit_test import unit_test

from _bes_unit_test_common.dir_operation_tester import dir_operation_tester

class test_file_split(unit_test):

  def test_unsplit(self):
    items = [
      temp_content('file', 'src/a/foo/kiwi.txt', 'this is kiwi', 0o0644),
      temp_content('file', 'src/a/parts/foo.txt.001', 'part001', 0o0644),
      temp_content('file', 'src/a/parts/foo.txt.002', 'part002', 0o0644),
      temp_content('file', 'src/a/parts/foo.txt.003', 'part003', 0o0644),
      temp_content('file', 'src/b/icons/lemon.jpg.01', 'part01', 0o0644),
      temp_content('file', 'src/b/icons/lemon.jpg.02', 'part02', 0o0644),
      temp_content('file', 'src/b/icons/lemon.jpg.03', 'part03', 0o0644),
    ]
    return
    t = self._unsplit_test(extra_content_items = items,
                           recursive = True)
    self.assertEqual( [
      'a',
      'a/foo',
      'a/foo/kiwi.txt',
      'a/parts',
      'a/parts/foo.txt',
      'b',
      'b/icons',
      'b/icons/lemon.jpg',
    ], t.src_files )

  def test_split_file_basic(self):
    NUM_ITEMS = 10
    CONTENT_SIZE = 1024 * 100
    items = []
    for i in range(0, NUM_ITEMS):
      arcname = 'item{}.txt'.format(i)
      item = temp_archive.item(arcname, content = self._make_content(CONTENT_SIZE))
      items.append(item)
    tmp_archive = temp_archive.make_temp_archive(items, 'zip')

    files = file_split.split_file(tmp_archive, int(math.floor(file_util.size(tmp_archive) / 1)))
    unsplit_tmp_archive = self.make_temp_file()
    file_split.unsplit_files(unsplit_tmp_archive, files)
    self.assertEqual( file_util.checksum('sha256', tmp_archive), file_util.checksum('sha256', unsplit_tmp_archive) )
    file_util.remove(files)
    
    files = file_split.split_file(tmp_archive, int(math.floor(file_util.size(tmp_archive) / 2)))
    unsplit_tmp_archive = self.make_temp_file()
    file_split.unsplit_files(unsplit_tmp_archive, files)
    self.assertEqual( file_util.checksum('sha256', tmp_archive), file_util.checksum('sha256', unsplit_tmp_archive) )
    file_util.remove(files)

    files = file_split.split_file(tmp_archive, int(math.floor(file_util.size(tmp_archive) / 3)))
    unsplit_tmp_archive = self.make_temp_file()
    file_split.unsplit_files(unsplit_tmp_archive, files)
    self.assertEqual( file_util.checksum('sha256', tmp_archive), file_util.checksum('sha256', unsplit_tmp_archive) )
    file_util.remove(files)
    
    files = file_split.split_file(tmp_archive, int(math.floor(file_util.size(tmp_archive) / 4)))
    unsplit_tmp_archive = self.make_temp_file()
    file_split.unsplit_files(unsplit_tmp_archive, files)
    self.assertEqual( file_util.checksum('sha256', tmp_archive), file_util.checksum('sha256', unsplit_tmp_archive) )
    file_util.remove(files)
    
    files = file_split.split_file(tmp_archive, int(math.floor(file_util.size(tmp_archive) / 5)))
    unsplit_tmp_archive = self.make_temp_file()
    file_split.unsplit_files(unsplit_tmp_archive, files)
    self.assertEqual( file_util.checksum('sha256', tmp_archive), file_util.checksum('sha256', unsplit_tmp_archive) )
    file_util.remove(files)
    
  @classmethod
  def _make_content(clazz, size):
    chars = [ c for c in string.ascii_letters ]
    v = []
    for i in range(0, size):
      i = random.randint(0, (len(chars) - 1))
      v.append(chars[i])
    return ''.join(v)
    
  def _unsplit_test(self,
                    extra_content_items = None,
                    recursive = False,
                    ):
    options = file_split_options(recursive = recursive)
    with dir_operation_tester(extra_content_items = extra_content_items) as test:
      test.result = file_split.unsplit_files([ test.src_dir ],
                                             options = options)
    return test
    
if __name__ == '__main__':
  unit_test.main()
