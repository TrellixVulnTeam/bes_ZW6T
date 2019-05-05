#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

import re
#from datetime import datetime
from collections import namedtuple

from bes.text import text_line_parser
from bes.common import string_util, tuple_util

git_branch_status = namedtuple('git_branch_status', 'ahead, behind')

class git_branch(namedtuple('git_branch', 'name, where, active, ahead, behind, commit, comment')):

  def __new__(clazz, name, where, active, ahead, behind, commit, comment):
    return clazz.__bases__[0].__new__(clazz, name, where, active, ahead, behind, commit, comment)

  @classmethod
  def parse_branch(clazz, s, where):
    parts = string_util.split_by_white_space(s, strip = True)
    active = False
    if parts[0] == '*':
      active = True
      parts.pop(0)
    assert len(parts) > 2
    name = parts[0]
    commit = parts[1]
    comment = ' '.join(parts[2:])
    ahead, behind = clazz.parse_branch_status(comment)
    return git_branch(name, where, active, ahead, behind, commit, comment)

  @classmethod
  def parse_branch_status(clazz, s):
    lines = text_line_parser.parse_lines(s, strip_comments = False, strip_text = True, remove_empties = True)
    ahead = re.findall('.*\[ahead\s+(\d+).*', lines[0])
    if ahead:
      ahead = int(ahead[0])
    behind = re.findall('.*behind\s+(\d+)\].*', lines[0])
    if behind:
      behind = int(behind[0])
    return git_branch_status(ahead or 0, behind or 0)
  
  def clone(self, mutations = None):
    return tuple_util.clone(self, mutations = mutations)