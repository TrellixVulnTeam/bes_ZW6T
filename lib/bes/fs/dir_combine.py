#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

from collections import namedtuple
import os.path as path

from bes.common.algorithm import algorithm
from bes.common.object_util import object_util
from bes.common.string_util import string_util
from bes.system.check import check
from bes.system.log import logger
from bes.fs.file_resolver import file_resolver
from bes.fs.file_resolver_options import file_resolver_options

from .dir_operation_item import dir_operation_item
from .dir_operation_item_list import dir_operation_item_list
from .dir_operation_util import dir_operation_util
from .dir_combine_options import dir_combine_options
from .dir_combine_type import dir_combine_type
from .file_attributes_metadata import file_attributes_metadata
from .file_check import file_check
from .file_find import file_find
from .file_path import file_path
from .file_util import file_util
from .filename_list import filename_list

class dir_combine(object):
  'A class to partition directories'

  _log = logger('dir_combine')

  @classmethod
  def combine(clazz, files, dst_dir, options = None):
    check.check_string_seq(files)
    check.check_dir_combine_options(options, allow_none = True)
    check.check_string(dst_dir)

    options = options or dir_combine_options()
    
    info = clazz.combine_info(files, dst_dir, options = options)
    dir_operation_util.move_files(info.items,
                                  options.dup_file_timestamp,
                                  options.dup_file_count)
    root_dirs = info.resolved_files.root_dirs()
    for next_possible_empty_root in root_dirs:
      file_find.remove_empty_dirs(next_possible_empty_root)
      
  _combine_info_result = namedtuple('_partition_items_info', 'items, resolved_files')
  @classmethod
  def combine_info(clazz, files, dst_dir, options = None):
    check.check_string_seq(files)
    check.check_dir_combine_options(options, allow_none = True)
    check.check_string(dst_dir)

    dst_dir_abs = path.abspath(dst_dir)
    options = options or dir_combine_options()

    resolved_files = clazz._resolve_files(files, options.recursive)
    basenames = resolved_files.basenames(sort = True)
    prefixes = filename_list.prefixes(basenames)
    buckets = clazz._make_prefix_buckets(prefixes, resolved_files.absolute_files(sort = True))
    items = dir_operation_item_list()
    for prefix, filenames in buckets.items():
      num_files = len(filenames)
      if num_files >= options.threshold:
        for src_filename in filenames:
          dst_filename = path.join(dst_dir_abs, prefix, path.basename(src_filename))
          item = dir_operation_item(src_filename, dst_filename)
          items.append(item)
    return clazz._combine_info_result(items, resolved_files)