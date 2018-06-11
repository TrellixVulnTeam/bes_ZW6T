#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

import os, os.path as path
from abc import abstractmethod, ABCMeta
from bes.system.compat import with_metaclass
from collections import namedtuple

from bes.common import algorithm
from bes.fs import file_find, file_path, file_util, tar_util, temp_file
from bes.match import matcher_multiple_filename, matcher_always_false, matcher_always_true, matcher_util

class archive(with_metaclass(ABCMeta, object)):
  'An archive interface.'

  Item = namedtuple('Item', [ 'filename', 'arcname' ])

  def __init__(self, filename):
    self.filename = filename

  @abstractmethod
  def is_valid(self):
    pass

  @abstractmethod
  def members(self):
    pass

  @abstractmethod
  def has_member(self, arcname):
    pass

  @abstractmethod
  def extract_members(self, members, dest_dir, base_dir = None,
                      strip_common_base = False, strip_head = None,
                      include = None, exclude = None):
    pass

  @abstractmethod
  def create(self, root_dir, base_dir = None,
             extra_items = None,
             include = None, exclude = None):
    pass

  def extract(self, dest_dir, base_dir = None,
              strip_common_base = False, strip_head = None,
              include = None, exclude = None):
    return self.extract_members(self.members(),
                                dest_dir,
                                base_dir = base_dir,
                                strip_common_base = strip_common_base,
                                strip_head = strip_head,
                                include = include, exclude = exclude)

  def extract_member_to_string(self, member):
    tmp_dir = temp_file.make_temp_dir()
    tmp_member = path.join(tmp_dir, member)
    self.extract_members([ member ], tmp_dir)
    if not path.exists(tmp_member):
      raise RuntimeError('Failed to extract member: %s' % (member))
    if not path.isfile(tmp_member):
      raise RuntimeError('Member is not a file: %s' % (member))
    result = file_util.read(tmp_member)
    file_util.remove(tmp_dir)
    return result

  # FIXME: cut-n-paste with above
  def extract_member_to_file(self, member, filename):
    tmp_dir = temp_file.make_temp_dir()
    tmp_member = path.join(tmp_dir, member)
    self.extract_members([ member ], tmp_dir)
    if not path.exists(tmp_member):
      raise RuntimeError('Failed to extract member: %s' % (member))
    if not path.isfile(tmp_member):
      raise RuntimeError('Member is not a file: %s' % (member))
    file_util.rename(tmp_member, filename)

  def common_base(self):
    'Return a common base dir for the archive or None if no common base exists.'
    return self._common_base_for_members(self.members())

  @classmethod
  def _normalize_members(clazz, members):
    'Return a sorted and unique list of members.'
    return sorted(algorithm.unique(members))

  # Some archives have some dumb members that are immaterial to common base
  COMMON_BASE_MEMBERS_EXCLUDE = [ '.' ]

  @classmethod
  def _common_base_for_members(clazz, members):
    'Return a common base dir for the given members or None if no common base exists.'
    members = [ m for m in members if m not in clazz.COMMON_BASE_MEMBERS_EXCLUDE ]
    return file_path.common_ancestor(members)

  @classmethod
  def _find(clazz, root_dir, base_dir, extra_items, include, exclude):
    files = file_find.find(root_dir, relative = True, file_type = file_find.FILE | file_find.LINK)
    items = []

    if include:
      include_matcher = matcher_multiple_filename(include)
    else:
      include_matcher = matcher_always_true()

    if exclude:
      exclude_matcher = matcher_multiple_filename(exclude)
    else:
      exclude_matcher = matcher_always_false()

    for f in files:
      filename = path.join(root_dir, f)
      if base_dir:
        arcname = path.join(base_dir, f)
      else:
        arcname = f

      should_include = include_matcher.match(f)
      should_exclude = exclude_matcher.match(f)

      if should_include and not should_exclude:
        items.append(clazz.Item(filename, arcname))

    return items + (extra_items or [])

  @classmethod
  def _determine_dest_dir(clazz, dest_dir, base_dir):
    if base_dir:
      dest_dir = path.join(dest_dir, base_dir)
    else:
      dest_dir = dest_dir
    file_util.mkdir(dest_dir)
    return dest_dir

  def _handle_extract_strip_common_base(self, members, strip_common_base, strip_head, dest_dir):
    if strip_common_base:
      common_base = self._common_base_for_members(members)
      if common_base:
        from_dir = path.join(dest_dir, common_base)
        tar_util.copy_tree_with_tar(from_dir, dest_dir)
        file_util.remove(from_dir)
    if strip_head:
      from_dir = path.join(dest_dir, strip_head)
      if path.isdir(from_dir):
        tar_util.copy_tree_with_tar(from_dir, dest_dir)
        file_util.remove(from_dir)
      
  def _pre_create(self):
    'Setup some stuff before create() is called.'
    d = path.dirname(self.filename)
    if d:
      file_util.mkdir(d)

  @classmethod
  def _filter_for_extract(clazz, members, include, exclude):
    return matcher_util.match_filenames(members, include, exclude)
