#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

from __future__ import absolute_import
from bes.system.compat import compat

if compat.IS_PYTHON2:
  map = map
else:
  from builtins import map

