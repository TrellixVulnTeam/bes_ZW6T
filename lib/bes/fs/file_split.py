#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

from collections import namedtuple
import os.path as path
import math

from bes.archive.archiver import archiver
from ..system.check import check
from bes.common.time_util import time_util
from bes.system.check import check
from bes.system.log import logger

from .dir_util import dir_util
from .file_resolver import file_resolver
from .file_resolver_item_list import file_resolver_item_list
from .file_resolver_options import file_resolver_options
from .file_split_error import file_split_error
from .file_split_options import file_split_options
from .file_util import file_util
from .filename_util import filename_util
from .temp_file import temp_file

class file_split(object):
  'A class to find duplicate files'

  _log = logger('file_split')

  _UNSPLIT_EXTENSIONS = [ '01', '001', '0001', '00001' ]
  @classmethod
  def _match_unsplit_files(clazz, filename):
    return filename_util.has_any_extension(filename, clazz._UNSPLIT_EXTENSIONS)
  
  @classmethod
  def find_and_unsplit(clazz, files, options = None):
    check.check_string_seq(files)
    check.check_file_split_options(options, allow_none = True)

    info = clazz.find_and_unsplit_info(files, options = options)
    for item in info.items:
      item_target = item.target
      options.blurber.blurb_verbose(f'Unsplitting {item_target} - {len(item.files)} parts.')
      tmp = temp_file.make_temp_file(prefix = path.basename(item_target), dir = path.dirname(item_target))
      clazz.unsplit_files(tmp, item.files)
      if options.unzip:
        if archiver.is_valid(tmp):
          members = archiver.members(tmp)
          num_members = len(members)
          if num_members != 1:
            options.blurber.blurb(f'{item_target} archive should have exactly 1 member instead of {num_members}')
          else:
            archive_filename = members[0]
            archive_tmp_dir = temp_file.make_temp_dir(prefix = path.basename(archive_filename),
                                                      dir = path.dirname(item_target),
                                                      delete = False)
            archiver.extract_all(tmp, archive_tmp_dir)
            archive_tmp_file = path.join(archive_tmp_dir, archive_filename)
            assert path.exists(archive_tmp_file)
            file_util.rename(archive_tmp_file, tmp)
            file_util.remove(archive_tmp_dir)
            item_target = path.join(path.dirname(item_target), archive_filename)
            
      target = None
      if path.exists(item_target):
        if file_util.files_are_the_same(tmp, item_target):
          options.blurber.blurb(f'{item_target} already exists and is the same')
          file_util.remove(tmp)
        else:
          ts = time_util.timestamp(delimiter = '',
                                   milliseconds = False,
                                   when = options.existing_file_timestamp)
          target = clazz._make_timestamp_filename(item_target, ts)
          options.blurber.blurb(f'{item_target} already exists but is different.  Renaming to {target}')
      else:
        target = item_target
      if target:
        file_util.rename(tmp, target)
      file_util.remove(item.files)

  @classmethod
  def _make_timestamp_filename(clazz, filename, ts):
    dirname = path.dirname(filename)
    basename = path.basename(filename)
    basename_without_extension = filename_util.without_extension(basename)
    ext = filename_util.extension(basename)
    new_basename = filename_util.add_extension(f'{basename_without_extension}-{ts}', ext)
    return path.join(dirname, new_basename)
      
  _split_item = namedtuple('_split_item', 'target, files')
  _split_result = namedtuple('_find_duplicates_result', 'items, resolved_files')
  @classmethod
  def find_and_unsplit_info(clazz, files, options = None):
    check.check_string_seq(files)
    check.check_file_split_options(options, allow_none = True)

    options = options or file_split_options()
    resolver_options = file_resolver_options(recursive = options.recursive,
                                             match_basename = True,
                                             match_function = clazz._match_unsplit_files)
    resolved_files = file_resolver.resolve_files(files, options = resolver_options)
    items = []
    for f in resolved_files:
      item = clazz._unsplit_one_info(f.filename_abs, options)
      if item:
        items.append(item)
    return clazz._split_result(items, resolved_files)
      
  @classmethod
  def _unsplit_one_info(clazz, first_filename, options):
    files_group = clazz._files_group(first_filename, options.ignore_extensions)
    if len(files_group) == 1:
      return None
    if options.check_downloading_extension:
      dl_files = clazz._files_group_is_still_downloading(files_group, options.check_downloading_extension)
      if dl_files:
        for f in dl_files:
          options.blurber.blurb(f'Still downloading: {f}')
        return None
    if not clazz._files_group_is_complete(files_group):
      if options.ignore_incomplete:
        print('Ignoring incomplete group:\n  {}'.format('\n  '.join(files_group)))
        return None
      else:
        raise file_split_error('Incomplete group:\n  {}'.format('\n  '.join(files_group)))
    
    target_filename = filename_util.without_extension(first_filename)
    return clazz._split_item(target_filename, files_group)
    
  @classmethod
  def _files_group(clazz, first_filename, ignore_extensions):
    def _is_group_file(filename):
      return clazz._is_group_file(first_filename, filename, ignore_extensions)
    files = dir_util.list(path.dirname(first_filename),
                          function = _is_group_file)
    assert len(files) > 0
    assert files[0] == first_filename
    return files

  @classmethod
  def _is_group_file(clazz, first_filename, filename, ignore_extensions):
    first_basename = path.basename(first_filename)
    first_basename_without_extension = filename_util.without_extension(first_basename)
    first_ext = filename_util.extension(first_basename)
    first_ext_len = len(first_ext)

    if ignore_extensions and filename_util.has_any_extension(filename,
                                                             ignore_extensions,
                                                             ignore_case = True):
      filename = filename_util.without_extension(filename)
    
    basename = path.basename(filename)
    basename_without_extension = filename_util.without_extension(basename)
    ext = filename_util.extension(basename)
    if not ext:
      return False
    ext_len = len(ext)
    if basename_without_extension != first_basename_without_extension:
      return False
    if ext_len != first_ext_len:
      return False
    return ext.isdigit()

  @classmethod
  def _files_group_is_complete(clazz, files):
    last_ext = filename_util.extension(files[-1])
    last_index = int(last_ext)
    return len(files) == last_index

  @classmethod
  def _files_group_is_still_downloading(clazz, files, downloading_extension):
    result = []
    for filename in files:
      downloading_sentinel = filename_util.add_extension(filename, downloading_extension)
      if path.exists(downloading_sentinel):
        result.append(filename)
    return result
  
  @classmethod
  def split_file(clazz, filename, chunk_size, zfill_length = None, output_directory = None):
    check.check_string(filename)
    check.check_int(chunk_size)
    check.check_int(zfill_length, allow_none = True)
    
    file_size = file_util.size(filename)
    
    clazz._log.log_method_d()
    
    num_total = int(math.ceil(float(file_size) / float(chunk_size)))
    result_file_list = []
    zfill_length = zfill_length or len(str(num_total))
    output_directory = output_directory or path.dirname(filename)
    with open(filename, 'rb') as fin:
      index = 0
      while True:
        data = fin.read(chunk_size)
        if not data:
          break
        next_filename = clazz._make_split_filename(filename,
                                                   output_directory,
                                                   index + 1,
                                                   zfill_length)
        with open(next_filename, 'wb') as fout:
          fout.write(data)
          result_file_list.append(next_filename)
        index += 1
    return result_file_list

  @classmethod
  def _make_split_filename(clazz, filename, output_directory, index, zfill_length):
    basename = path.basename(filename)
    split_filename = path.join(output_directory, basename)
    extension = str(index).zfill(zfill_length)
    return filename_util.add_extension(split_filename, extension)
  
  @classmethod
  def unsplit_files(clazz, target_filename, files, buffer_size = 1024 * 1204):
    with open(target_filename, 'wb') as fout:
      for next_filename in files:
        with open(next_filename, 'rb') as fin:
          while True:
            data = fin.read(buffer_size)
            if not data:
              break
            fout.write(data)
  
