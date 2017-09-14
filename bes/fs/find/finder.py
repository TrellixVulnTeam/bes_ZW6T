#!/usr/bin/env python
#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

import errno, os.path as path, os, stat

from bes.system import log
from bes.common import object_util
#from bes.fs import file_util, file_match

from .match_variables import match_variables
from .criteria import criteria

from collections import namedtuple

class finder(object):

  BLOCK = 0x01
  CHAR = 0x02
  DIR = 0x04
  FILE = 0x08
  LINK = 0x10
  FIFO = 0x20
  SOCKET = 0x40
  ANY = BLOCK | CHAR | DIR | FILE | LINK | FIFO | SOCKET
  
  def __init__(self, root_dir, criteria = None, relative = True):
    self.root_dir = path.normpath(root_dir)
    self.criteria = object_util.listify(criteria or [])
    
  def find(self):

    if not path.isdir(self.root_dir):
      raise RuntimeError('not a directory: %s' % (self.root_dir))

    file_criteria = [ c for c in self.criteria if c.targets_files() ]
    dir_criteria = [ c for c in self.criteria if c.targets_dirs() ]

    if False:
      import sys
      sys.stderr.write("file criteria: %s\n" % (file_criteria))
      sys.stderr.write(" dir criteria: %s\n" % (dir_criteria))
    
    root_dir_depth = self.root_dir.count(os.sep)

    for x in self._match_file(self.root_dir, dir_criteria, 0, '', self.root_dir):
      yield x
      
    for next_dir, dirs, files in os.walk(self.root_dir, topdown = True):
      next_dir_depth = next_dir.count(os.sep) - root_dir_depth

      if False:
        mv = match_variables(next_dir_depth, self.root_dir, path.basename(next_dir), next_dir)
        for c in dir_criteria:
          if c.matches(mv):
            yield next_dir

      for x in self._match_files(files, file_criteria, next_dir_depth, next_dir, self.root_dir):
        yield x

      for x in self._match_files(dirs, dir_criteria, next_dir_depth, next_dir, self.root_dir):
        yield x
        
      if False:
      #if True:
        print "       next_dir: %s" % (next_dir)
        print " root_dir_depth: %s" % (root_dir_depth)
        print "           dirs: %s" % (' '.join(dirs))
        print "          files: %s" % (' '.join(files))
        print " next_dir_depth: %s" % (next_dir_depth)
        print ""
#      yield clazz.walk_item(next_dir_depth, next_dir, dirs, files)
#      if max_depth is not None:
#        if next_dir_depth > max_depth:
#          del dirs[:]

  @classmethod
  def _match_file(clazz, filename, criteria, depth, next_dir, root_dir):
    filepath = path.join(next_dir, filename)
    mv = match_variables(depth, root_dir, filename, filepath)
    if not criteria:
      yield filepath
    for c in criteria:
      import sys
      sys.stderr.write("MATCHING %s with %s\n" % (filename, c))
      if c.matches(mv):
        yield filepath

  @classmethod
  def _match_files(clazz, files, criteria, depth, next_dir, root_dir):
    for filename in files:
      for x in clazz._match_file(filename, criteria, depth, next_dir, root_dir):
        yield x
