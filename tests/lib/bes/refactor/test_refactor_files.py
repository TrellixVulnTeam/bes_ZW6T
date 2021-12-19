#!/usr/bin/env python
#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

import os.path as path
from bes.testing.unit_test import unit_test
from bes.refactor.refactor_files import refactor_files
from bes.fs.testing.temp_content import temp_content

from _bes_unit_test_common.unit_test_media import unit_test_media
from _bes_unit_test_common.unit_test_media_files import unit_test_media_files

class test_refactor_files(unit_test, unit_test_media_files):

  @classmethod
  def _make_temp_content(clazz, items):
    return temp_content.write_items_to_temp_dir(items, delete = not clazz.DEBUG)

  def test_resolve_python_files(self):
    self.maxDiff = None
    tmp_dir = self._make_temp_content([
      temp_content('file', 'fruit/icons/kiwi.png', unit_test_media.PNG_SMALLEST_POSSIBLE, 0o0644),
      temp_content('file', 'fruit/icons/wrong_extension.py', unit_test_media.PNG_SMALLEST_POSSIBLE, 0o0644),
      temp_content('file', 'fruit/src/lemon.py', "class foo(object): pass", 0o0644),
      temp_content('file', 'fruit/bin/script', "#!/usr/bin/env python3\na=666\n", 0o0755),
    ])
    self.assert_filename_list_equal( [
      f'{tmp_dir}/fruit/bin/script',
      f'{tmp_dir}/fruit/src/lemon.py',
    ], refactor_files.resolve_python_files(tmp_dir) )
    
if __name__ == '__main__':
  unit_test.main()
