#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

import string

from collections import namedtuple

from bes.system.check import check
from bes.compat.StringIO import StringIO

from .word_boundary import word_boundary as word_boundary_module

class text_search(object):
  'Class to deal with text search and replace'

  _span = namedtuple('_span', 'start, end')
  @classmethod
  def find_all(clazz, text, sub_string, word_boundary = False, boundary_chars = None):
    'Returns a list of of all the spans containing sub_string in text'
    check.check_string(text)
    check.check_string(sub_string)
    check.check_bool(word_boundary)
    check.check_set(boundary_chars, allow_none = True)

    return [ span for span in clazz.find_all_generator(text,
                                                       sub_string,
                                                       word_boundary = word_boundary,
                                                       boundary_chars = boundary_chars) ]

  @classmethod
  def find_all_generator(clazz, text, sub_string, word_boundary = False, boundary_chars = None):
    check.check_string(text)
    check.check_string(sub_string)
    check.check_bool(word_boundary)
    check.check_set(boundary_chars, allow_none = True)

    boundary_chars = boundary_chars or word_boundary_module.CHARS
    sub_string_length = len(sub_string)
    i = 0
    while True:
      i = text.find(sub_string, i)
      if i < 0:
        return
      start = i
      end = i + sub_string_length - 1
      i += sub_string_length
      if word_boundary:
        assert boundary_chars
        do_yield = word_boundary_module.word_has_boundary(text, start, end, boundary_chars = boundary_chars)
      else:
        do_yield = True
      if do_yield:
        yield clazz._span(start, end)
        
  @classmethod
  def replace_span(clazz, text, start, end, replacement):
    'Replace a span of text from start to end with replacement'
    check.check_string(text)
    check.check_int(start)
    check.check_int(end)
    check.check_string(replacement)

    length = len(text)
    
    if start < 0:
      raise ValueError('start should be greater than 0')
    if start >= length:
      raise ValueError(f'end should be less than the length of text - {length}')
    if end < start:
      raise ValueError(f'end({end}) should be greater than start({start})')
    if end >= length:
      raise ValueError(f'end({end}) should be less than the length of text - {length}')
    
    left = text[:start]
    right = text[end + 1:]
    return left + replacement + right

  @classmethod
  def replace_all(clazz, text, src_string, dst_string, word_boundary = False, boundary_chars = None):
    'Replace src_string with dst_string optionally respecting word boundaries.'
    check.check_string(text)
    check.check_string(src_string)
    check.check_string(dst_string)
    check.check_bool(word_boundary)
    check.check_set(boundary_chars, allow_none = True)

    spans = clazz.find_all(text,
                           src_string,
                           word_boundary = word_boundary,
                           boundary_chars = boundary_chars)
    for span in reversed(spans):
      text = clazz.replace_span(text, span.start, span.end, dst_string)
    return text

  @classmethod
  def replace_all_fast(clazz, text, src_string, dst_string, word_boundary = False, boundary_chars = None):
    'Replace src_string with dst_string optionally respecting word boundaries.'
    check.check_string(text)
    check.check_string(src_string)
    check.check_string(dst_string)
    check.check_bool(word_boundary)
    check.check_set(boundary_chars, allow_none = True)

    spans = clazz.find_all(text,
                           src_string,
                           word_boundary = word_boundary,
                           boundary_chars = boundary_chars)
    if not spans:
      return text
    last_start = 0
    buf = StringIO()
    last_span = None
    for span in spans:
      left = text[last_start : span.start]
      if left:
        buf.write(left)
      buf.write(dst_string)
      last_start = span.end + 1
      last_span = span
    if last_span:
      right = text[last_span.end + 1:]
      buf.write(right)
    return buf.getvalue()

  @classmethod
  def replace_punctuation(clazz, s, replacement):
    'Replace punctuation in s with replacement.'
    buf = StringIO()
    for c in s:
      if c in string.punctuation:
        if replacement:
          buf.write(replacement)
      else:
        buf.write(c)
    return buf.getvalue()

  @classmethod
  def replace_white_space(clazz, s, replacement):
    'Replace white space sequences in s with replacement.'
    buf = StringIO()
    STATE_CHAR = 1
    STATE_SPACE = 2

    state = STATE_CHAR
    for c in s:
      if state == STATE_CHAR:
        if c.isspace():
          buf.write(replacement)
          state = STATE_SPACE
        else:
          buf.write(c)
      elif state == STATE_SPACE:
        if not c.isspace():
          buf.write(c)
          state = STATE_CHAR
    return buf.getvalue()
  
