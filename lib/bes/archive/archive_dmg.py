#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

import os, os.path as path, tarfile
from bes.fs import file_util, temp_file
from bes.system import execute

from .archive import archive
from .archive_extension import archive_extension
from .macos.dmg import dmg
from .archive_zip import archive_zip

class archive_dmg(archive):
  'A class to deal with dmg archives.  http://newosxbook.com/DMG.html.'

  def __init__(self, filename):
    super(archive_dmg, self).__init__(filename)

  def is_valid(self):
    return dmg.is_dmg_file(self.filename)

  def members(self):
    members = dmg.contents(self.filename)
    return self._normalize_members(members)

  def extract_members(self, members, dest_dir, base_dir = None,
                      strip_common_base = False, strip_head = None,
                      include = None, exclude = None):
    # Cheat by using a temporary zip file to do the actual work.  Super innefecient but
    # easy since theres no library to extract just some stuff from dmg files.
    tmp_dir = temp_file.make_temp_dir()
    dmg.extract(self.filename, tmp_dir)
    tmp_zip = temp_file.make_temp_file(suffix = '.zip')
    az = archive_zip(tmp_zip)
    az.create(tmp_dir)
    az.extract_members(members, dest_dir, base_dir = base_dir,
                       strip_common_base = strip_common_base, strip_head = strip_head,
                       include = include, exclude = exclude)
    file_util.remove(tmp_zip)
    file_util.remove(tmp_dir)

  def create(self, root_dir, base_dir = None,
             extra_items = None,
             include = None, exclude = None):
    self._pre_create()
    items = self._find(root_dir, base_dir, extra_items, include, exclude)
    tmp_dir = temp_file.make_temp_dir()
    for item in items:
      file_util.copy(item.filename, path.join(tmp_dir, item.arcname))
    cmd = 'hdiutil create -srcfolder %s -ov -format UDZO %s' % (tmp_dir, self.filename)
    execute.execute(cmd)
    file_util.remove(tmp_dir)
