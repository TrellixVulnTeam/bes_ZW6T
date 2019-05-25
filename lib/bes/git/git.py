#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

import os, os.path as path, re
from datetime import datetime
from collections import namedtuple

from bes.text import text_line_parser
from bes.common import algorithm, object_util, string_util
from bes.system import execute, logger
from bes.fs import dir_util, file_ignore, file_util, tar_util, temp_file
from bes.fs.file_ignore import ignore_file_data
from bes.version.software_version import software_version

from .git_branch import git_branch, git_branch_status
from .git_branch_list import git_branch_list
from .git_status import git_status

class git(object):
  'A class to deal with git.'

  _LOG = logger('git')
  
  GIT_EXE = 'git'

  @classmethod
  def status(clazz, root, filenames, abspath = False, untracked_files = True):
    filenames = object_util.listify(filenames)
    flags = [ '--porcelain' ]
    if untracked_files:
      flags.append('--untracked-files=normal')
    else:
      flags.append('--untracked-files=no')
    args = [ 'status' ] + flags + filenames
    rv = clazz._call_git(root, args)
    result = git_status.parse(rv.stdout)
    if abspath:
      for r in result:
        r.filename = path.join(root, r.filename)
    return result

  @classmethod
  def branch_status(clazz, root):
    rv = clazz._call_git(root, [ 'status', '-b', '--porcelain' ])
    return git_branch.parse_branch_status(rv.stdout)

  @classmethod
  def remote_update(clazz, root):
    return clazz._call_git(root, [ 'remote', 'update' ])

  @classmethod
  def remote_origin_url(clazz, root):
    rv = clazz._call_git(root, [ 'remote', 'get-url', '--push', 'origin' ])
    return rv.stdout.strip()
    
  @classmethod
  def has_changes(clazz, root, untracked_files = False):
    return clazz.status(root, '.', untracked_files = untracked_files) != []

  @classmethod
  def add(clazz, root, filenames):
    filenames = object_util.listify(filenames)
    flags = []
    args = [ 'add' ] + flags + filenames
    return clazz._call_git(root, args)

  @classmethod
  def move(clazz, root, src, dst):
    args = [ 'mv', src, dst ]
    return clazz._call_git(root, args)

  @classmethod
  def init(clazz, root, *args):
    args = [ 'init', '.' ] + list(args or [])
    return clazz._call_git(root, args)

  @classmethod
  def is_repo(clazz, root):
    expected_files = [ 'HEAD', 'config', 'index', 'refs', 'objects' ]
    for f in expected_files:
      if not path.exists(path.join(root, '.git', f)):
        return False
    return True

  @classmethod
  def check_is_git_repo(clazz, d):
    if not clazz.is_repo(d):
      raise RuntimeError('Not a git repo: %s' % (d))
  
  @classmethod
  def _call_git(clazz, root, args, raise_error = True):
    cmd = [ clazz.GIT_EXE ] + args
    clazz._LOG.log_d('root=%s; cmd=%s' % (root, ' '.join(cmd)))
    save_raise_error = raise_error
    rv = execute.execute(cmd, cwd = root, raise_error = False)
    if rv.exit_code != 0 and save_raise_error:
      message = 'git command failed: %s in %s\n' % (' '.join(cmd), root)
      message += rv.stderr
      message += rv.stdout
      print(message)
      ex = RuntimeError(message)
      setattr(ex, 'execute_result', rv)
      raise ex
    return rv

  @classmethod
  def clone(clazz, address, dest_dir, enforce_empty_dir = True):
    address = clazz.resolve_address(address)
    if path.exists(dest_dir):
      if not path.isdir(dest_dir):
        raise RuntimeError('dest_dir %s is not a directory.' % (dest_dir))
      if enforce_empty_dir:
        if not dir_util.is_empty(dest_dir):
          raise RuntimeError('dest_dir %s is not empty.' % (dest_dir))
    else:
      file_util.mkdir(dest_dir)
    args = [ 'clone', address, dest_dir ]
    return clazz._call_git(os.getcwd(), args)

  @classmethod
  def pull(clazz, root):
    args = [ 'pull', '--verbose' ]
    return clazz._call_git(root, args)

  @classmethod
  def checkout(clazz, root, revision):
    args = [ 'checkout', revision ]
    return clazz._call_git(root, args)

  @classmethod
  def push(clazz, root, *args):
    args = [ 'push', '--verbose' ] + list(args or [])
    return clazz._call_git(root, args)

  @classmethod
  def diff(clazz, root):
    args = [ 'diff' ]
    return clazz._call_git(root, args)

  @classmethod
  def patch_apply(clazz, root, patch_file):
    args = [ 'apply', patch_file ]
    return clazz._call_git(root, args)

  @classmethod
  def patch_make(clazz, root, patch_file):
    args = [ 'diff', '--patch' ]
    rv = clazz._call_git(root, args)
    file_util.save(patch_file, content = rv.stdout)

  @classmethod
  def commit(clazz, root, message, filenames):
    filenames = object_util.listify(filenames)
    message_filename = temp_file.make_temp_file(content = message)
    args = [ 'commit', '-F', message_filename ] + filenames
    return clazz._call_git(root, args)

  @classmethod
  def clone_or_pull(clazz, address, dest_dir, enforce_empty_dir = True):
    if clazz.is_repo(dest_dir):
      if clazz.has_changes(dest_dir):
        raise RuntimeError('dest_dir %s has changes.' % (dest_dir))
      return clazz.pull(dest_dir)
    else:
      return clazz.clone(address, dest_dir, enforce_empty_dir = enforce_empty_dir)

  @classmethod
  def archive(clazz, address, revision, base_name, archive_filename, untracked = False):
    'git archive with additional support to include untracked files for local repos.'
    tmp_repo_dir = temp_file.make_temp_dir()
    if path.isdir(address):
      tar_util.copy_tree_with_tar(address, tmp_repo_dir, excludes = clazz.read_gitignore(address))
      if untracked:
        clazz._call_git(tmp_repo_dir, [ 'add', '-A' ])
        clazz._call_git(tmp_repo_dir, [ 'commit', '-m', 'add untracked files just for tmp repo' ])
    else:
      if untracked:
        raise RuntimeError('untracked can only be True for local repos.')
      clazz.clone(address, tmp_repo_dir)
    archive_filename = path.abspath(archive_filename)
    file_util.mkdir(path.dirname(archive_filename))
    flags = []
    args = [
      'archive',
      '--format=tgz',
      '--prefix=%s-%s/' % (base_name, revision),
      '-o',
      archive_filename,
      revision
    ]
    rv = clazz._call_git(tmp_repo_dir, args)
    return rv
  
  @classmethod
  def short_hash(clazz, root, long_hash):
    args = [ 'rev-parse', '--short', long_hash ]
    rv = clazz._call_git(root, args)
    return rv.stdout.strip()

  @classmethod
  def long_hash(clazz, root, short_hash):
    args = [ 'rev-parse', short_hash ]
    rv = clazz._call_git(root, args)
    return rv.stdout.strip()
  
  @classmethod
  def reset_to_revision(clazz, root, revision):
    args = [ 'reset', '--hard', revision ]
    return clazz._call_git(root, args)

  @classmethod
  def last_commit_hash(clazz, root, short_hash = False):
    args = [ 'log', '--format=%H', '-n', '1' ]
    rv = clazz._call_git(root, args)
    long_hash = rv.stdout.strip()
    if not short_hash:
      return long_hash
    return clazz.short_hash(root, long_hash)

  @classmethod
  def root(clazz, filename):
    'Return the repo root for the given filename or raise and exception if not under git control.'
    cmd = [ 'git', 'rev-parse', '--show-toplevel' ]
    if path.isdir(filename):
      cwd = filename
    else:
      cwd = path.dirname(filename)
    rv = execute.execute(cmd, cwd = cwd, raise_error = False)
    if rv.exit_code != 0:
      return None
    l = clazz._parse_lines(rv.stdout)
    assert len(l) == 1
    return l[0]
  
  @classmethod
  def is_tracked(clazz, root, filename):
    'Return True if the filename is tracked by a git repo.'
    args = [ 'ls-files', '--error-unmatch', filename ]
    return clazz._call_git(root, args, raise_error = False).exit_code == 0
  
  @classmethod
  def modified_files(clazz, root):
    items = clazz.status(root, '.')
    return [ item.filename for item in items if 'M' in item.action ]

  @classmethod
  def tag(clazz, root_dir, tag, allow_downgrade = False):
    greatest_tag = git.greatest_local_tag(root_dir)
    if greatest_tag and not allow_downgrade:
      if software_version.compare(greatest_tag, tag) >= 0:
        raise ValueError('new tag \"%s\" is older than \"%s\".  Use allow_downgrade to force it.' % (tag, greatest_tag))
    clazz._call_git(root_dir, [ 'tag', tag ])

  @classmethod
  def push_tag(clazz, root, tag):
    clazz._call_git(root, [ 'push', 'origin', tag ])

  @classmethod
  def delete_local_tag(clazz, root, tag):
    clazz._call_git(root, [ 'tag', '--delete', tag ])

  @classmethod
  def delete_remote_tag(clazz, root, tag):
    clazz._call_git(root, [ 'push', '--delete', 'origin', tag ])

  @classmethod
  def delete_tag(clazz, root, tag, where, dry_run):
    clazz.check_where(where)
    if where in [ 'local', 'both' ]:
      local_tags = git.list_local_tags(root)
      if tag in local_tags:
        if dry_run:
          print('would delete local tag \"{tag}\"'.format(tag = tag))
        else:
          clazz.delete_local_tag(root, tag)
    if where in [ 'remote', 'both' ]:
      remote_tags = git.list_remote_tags(root)
      if tag in remote_tags:
        if dry_run:
          print('would delete remote tag \"{tag}\"'.format(tag = tag))
        else:
          clazz.delete_remote_tag(root, tag)

  @classmethod
  def list_local_tags(clazz, root, lexical = False, reverse = False):
    if lexical:
      sort_arg = '--sort={reverse}refname'.format(reverse = '-' if reverse else '')
    else:
      sort_arg = '--sort={reverse}version:refname'.format(reverse = '-' if reverse else '')
    rv = clazz._call_git(root, [ 'tag', '-l', sort_arg ])
    return clazz._parse_lines(rv.stdout)
  
  @classmethod
  def greatest_local_tag(clazz, root):
    tags = clazz.list_local_tags(root)
    if not tags:
      return None
    return tags[-1]

  @classmethod
  def list_remote_tags(clazz, root, lexical = False, reverse = False):
    rv = clazz._call_git(root, [ 'ls-remote', '--tags' ])
    lines = clazz._parse_lines(rv.stdout)
    tags = [ clazz._parse_remote_tag_line(line) for line in lines ]
    if lexical:
      return sorted(tags, reverse = reverse)
    else:
      return software_version.sort_versions(tags, reverse = reverse)
    return tags

  @classmethod
  def greatest_remote_tag(clazz, root):
    tags = clazz.list_remote_tags(root)
    if not tags:
      return None
    return tags[-1]

  @classmethod
  def _parse_remote_tag_line(clazz, s):
    f = re.findall('^[0-9a-f]{40}\s+refs/tags/(.+)$', s)
    if f and len(f) == 1:
      return f[0]
    return None

  @classmethod
  def _parse_lines(clazz, s):
    return text_line_parser.parse_lines(s, strip_comments = False, strip_text = True, remove_empties = True)

  @classmethod
  def commit_timestamp(clazz, root, commit):
    rv = clazz._call_git(root, [ 'show', '-s', '--format=%ct', commit ])
    ts = float(rv.stdout.strip())
    return datetime.fromtimestamp(ts)

  @classmethod
  def commit_for_tag(clazz, root, tag, short_hash = False):
    args = [ 'rev-list', '-n', '1', tag ]
    rv = clazz._call_git(root, args)
    long_hash = rv.stdout.strip()
    if not short_hash:
      return long_hash
    return clazz.short_hash(root, long_hash)

  @classmethod
  def read_gitignore(clazz, root):
    'Return the contents of .gitignore with comments stripped.'
    p = path.join(root, '.gitignore')
    if not path.isfile(p):
      return None
    return ignore_file_data.read_file(p).patterns

  @classmethod
  def config_set_value(clazz, key, value):
    clazz._call_git('/tmp', [ 'config', '--global', key, value ], raise_error = False)
    
  @classmethod
  def config_unset_value(clazz, key):
    clazz._call_git('/tmp', [ 'config', '--global', '--unset', key ], raise_error = False)
    
  @classmethod
  def config_get_value(clazz, key):
    rv = clazz._call_git('/tmp', [ 'config', '--global', key ], raise_error = False)
    if rv.exit_code == 0:
      return string_util.unquote(rv.stdout.strip())
    else:
      return None
  
  @classmethod
  def config_set_identity(clazz, name, email):
    clazz._call_git('/tmp', [ 'config', '--global', 'user.name', '"%s"' % (name) ])
    clazz._call_git('/tmp', [ 'config', '--global', 'user.email', '"%s"' % (email) ])

  _identity = namedtuple('_identity', 'name, email')
  @classmethod
  def config_get_identity(clazz):
    return clazz._identity(clazz.config_get_value('user.name'),
                           clazz.config_get_value('user.email'))
    
  _bump_tag_result = namedtuple('_bump_tag_result', 'old_tag, new_tag')
  @classmethod
  def bump_tag(clazz, root_dir, component, push = True, dry_run = False, default_tag = None, reset_lower = False):
    old_tag = git.greatest_local_tag(root_dir)
    if old_tag:
      new_tag = software_version.bump_version(old_tag, component, reset_lower = reset_lower)
    else:
      new_tag = default_tag or '1.0.0'
    if not dry_run:
      git.tag(root_dir, new_tag)
      if push:
        git.push_tag(root_dir, new_tag)
    return clazz._bump_tag_result(old_tag, new_tag)
  
  @classmethod
  def where_is_valid(clazz, where):
    return where in [ 'local', 'remote', 'both' ]

  @classmethod
  def check_where(clazz, where):
    if not clazz.where_is_valid(where):
      raise ValueError('where should be local, remote or both instead of: {}'.format(where))
    return where

  @classmethod
  def determine_where(clazz, local, remote, default_value = 'both'):
    if local is None and remote is None:
      return default_value
    local = bool(local)
    remote = bool(remote)
    if local and remote:
      return 'both'
    elif local:
      return 'local'
    elif remote:
      return 'remote'
    assert False

  @classmethod
  def active_branch(clazz, root):
    return [ i for i in clazz.branch_list(root) if i.active ][0].name

  @classmethod
  def list_branches(clazz, root, where):
    clazz.check_where(where)
    if where == 'local':
      branches = clazz._list_local_branches(root)
    elif where == 'remote':
      branches = clazz._list_remote_branches(root)
    else:
      branches = clazz._list_both_branches(root)
    return git_branch_list(branches)

  @classmethod
  def _branch_list_determine_authors(clazz, root, branches):
    result = git_branch_list()
    for branch in branches:
      result.append(branch.clone({ 'author': git.author(root, branch.commit, brief = True) }))
    return result
  
  @classmethod
  def _list_remote_branches(clazz, root):
    rv = clazz._call_git(root, [ 'branch', '--verbose', '--list', '--no-color', '--remote' ])
    lines = clazz._parse_lines(rv.stdout)
    lines = [ line for line in lines if not ' -> ' in line ]
    lines = [ string_util.remove_head(line, 'origin/') for line in lines ]
    branches = git_branch_list([ git_branch.parse_branch(line, 'remote') for line in lines ])
    return clazz._branch_list_determine_authors(root, branches)

  @classmethod
  def _list_local_branches(clazz, root):
    rv = clazz._call_git(root, [ 'branch', '--verbose', '--list', '--no-color' ])
    lines = clazz._parse_lines(rv.stdout)
    branches = git_branch_list([ git_branch.parse_branch(line, 'local') for line in lines ])
    return clazz._branch_list_determine_authors(root, branches)

  @classmethod
  def _list_both_branches(clazz, root):
    local_branches = clazz._list_local_branches(root)
    remote_branches = clazz._list_remote_branches(root)
    branch_map = {}
    
    for branch in clazz._list_remote_branches(root):
      branch_map[branch.name] = [ branch ]
      
    for branch in clazz._list_local_branches(root):
      existing_branch = branch_map.get(branch.name, None)
      if existing_branch:
        assert len(existing_branch) == 1
        if existing_branch[0].compare(branch, remote_only = True) == 0:
          new_branch = existing_branch[0].clone(mutations = { 'where': 'both', 'active': branch.active, 'ahead': branch.ahead, 'behind': branch.behind })
          branch_map[branch.name] = [ new_branch ]
        else:
          branch_map[branch.name].append(branch)
      else:
        branch_map[branch.name] = [ branch ]
    result = git_branch_list()
    for _, branches in branch_map.items():
      result.extend(branches)
    result.sort()
    return clazz._branch_list_determine_authors(root, result)
  
  @classmethod
  def branch_create(clazz, root, branch_name, checkout = False, push = False):
    branches = clazz.list_branches(root, 'both')
    if branches.has_remote(branch_name):
      raise ValueError('branch already exists remotely: {}'.format(branch_name))
    if branches.has_local(branch_name):
      raise ValueError('branch already exists locally: {}'.format(branch_name))
    clazz._call_git(root, [ 'branch', branch_name ])
    if checkout:
      clazz.checkout(root, branch_name)
    if push:
      clazz.branch_push(root, branch_name)
    
  @classmethod
  def branch_push(clazz, root, branch_name):
    clazz._call_git(root, [ 'push', '--set-upstream', 'origin', branch_name ])

  @classmethod
  def fetch(clazz, root):
    clazz._call_git(root, [ 'fetch', '--all' ])

  @classmethod
  def author(clazz, root, commit, brief = False):
    rv = clazz._call_git(root, [ 'show', '--no-patch', '--pretty=%ae', commit ])
    author = rv.stdout.strip()
    if brief:
      i = author.find('@')
      if i > 0:
        author = author[0:i]
        i = author.find('.')
        if i > 0:
          author = author[0:i]
    return author
    
  @classmethod
  def resolve_address(clazz, address):
    'If address is a local dir, return its absolute path with ~ expanded.  Otherwise just return address.'
    resolved_address = path.expanduser(address)
    if path.isdir(resolved_address):
      return resolved_address
    return address
