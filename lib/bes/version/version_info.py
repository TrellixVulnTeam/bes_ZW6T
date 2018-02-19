#!/usr/bin/env python
#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

from bes.common import check
from collections import namedtuple
from bes.compat import StringIO

class version_info(namedtuple('version_info', 'version,author_name,author_email,address,tag')):

  def __new__(clazz, version, author_name, author_email, address, tag):
    check.check_string(version)
    check.check_string(author_name)
    check.check_string(author_email)
    check.check_string(address)
    check.check_string(tag)
    return clazz.__bases__[0].__new__(clazz, version, author_name, author_email, address, tag)

  HEADER = '''\
#!/usr/bin/env python
#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

'''
  
  def __str__(self):
    buf = StringIO()
    buf.write(self.HEADER)
    buf.write('BES_VERSION = u\'%s\'\n' % (self.version))
    buf.write('BES_AUTHOR_NAME = u\'%s\'\n' % (self.author_name))
    buf.write('BES_AUTHOR_EMAIL = u\'%s\'\n' % (self.author_email))
    buf.write('BES_ADDRESS = u\'%s\'\n' % (self.address))
    buf.write('BES_TAG = u\'%s\'\n' % (self.tag))
    return buf.getvalue()

  @classmethod
  def read_file(clazz, filename):
    check.check_string(filename)
    with open(filename, 'r') as f:
      return clazz.read_string(f.read())

  @classmethod
  def read_string(clazz, s):
    ver = {}
    exec(s, {}, ver)
    return clazz(ver['BES_VERSION'], ver['BES_AUTHOR_NAME'], ver['BES_AUTHOR_EMAIL'], ver['BES_TAG'], ver['BES_ADDRESS'])

  def save_file(self, filename):
    check.check_string(filename)
    with open(filename, 'w') as f:
      f.write(str(self))
  
  def change(self, version = None, author_name = None, author_email = None, address = None, tag = None):
    if version is not None:
      check.check_string(version)
    else:
      version = self.version
    if author_name is not None:
      check.check_string(author_name)
    else:
      author_name = self.author_name
    if author_email is not None:
      check.check_string(author_email)
    else:
      author_email = self.author_email
    if address is not None:
      check.check_string(address)
    else:
      address = self.address
    if tag is not None:
      check.check_string(tag)
    else:
      tag = self.tag
    return self.__class__(version, author_name, author_email, address, tag)

check.register_class(version_info)

