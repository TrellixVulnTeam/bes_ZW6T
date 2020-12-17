#!/usr/bin/env python
#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

import sys
import os.path as path
import multiprocessing

from bes.testing.unit_test import unit_test
from bes.fs.file_util import file_util
from bes.fs.temp_file import temp_file
from bes.system.env_override import env_override_temp_home_func
from bes.system.execute import execute
from bes.git.git import git
from bes.git.git_repo import git_repo
from bes.git.git_status import git_status
from bes.git.git_temp_repo import git_temp_repo
from bes.git.git_unit_test import git_temp_home_func

class test_git_temp_repo(unit_test):

#  def _make_repo(self, remote = True, content = None, prefix = None, commit_message = None):
#    return git_temp_repo(remote = remote, content = content, prefix = prefix,
#                         debug = self.DEBUG, commit_message = commit_message)

  @git_temp_home_func()
  def test_apply_config_text(self):
    config = '''\
file something.txt
  content: this is my content
           it can be multi line
           or not
  perm: 644

add commit1 commit1
  foo.txt: this is a multi line
           content
  subdir/bar.txt: this is subdir/bar.txt
  scripts/go.sh[perm=655]: \#!/bin/bash
                           echo hello
                           exit 0
  copy_of_something.txt: @something.txt
  message: first commit

tag rel/1.0.0 tag1
  from_commit: @commit1

tag rel/1.0.0 tag2
  from_commit: @commit1
  annotation: first release

branch b1 b1 
  from_commit: @commit1
  
branch b2 b2
  from_branch: b1

remove remove1
  filename: copy_of_something.txt
    '''

    r = git_temp_repo(remote = True)
    r.apply_config_text(config)
    
if __name__ == '__main__':
  unit_test.main()
