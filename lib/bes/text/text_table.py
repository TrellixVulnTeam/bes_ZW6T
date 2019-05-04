#-*- coding:utf-8; mode:python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

from abc import abstractmethod, ABCMeta
from bes.system.compat import with_metaclass

from bes.common import check, object_util, table, size
from bes.compat import StringIO

from .text_box import text_box_unicode

class text_table_style_base(with_metaclass(ABCMeta, object)):
  
  @abstractmethod
  def spacing(self):
    pass
  
  @abstractmethod
  def box_style(self):
    pass
check.register_class(text_table_style_base, name = 'text_table_style')
  
class text_table_style_basic(text_table_style_base):

  def __init__(self, spacing = None, box_style = None):
    self._spacing = check.check_int(spacing if spacing is not None else 1)
    self._box_style = check.check_text_box(box_style or text_box_unicode())
    
  def spacing(self):
    return self._spacing
    
  def box_style(self):
    return self._box_style
    
class text_cell_renderer(object):

  JUST_LEFT = 'left'
  JUST_RIGHT = 'right'

  def __init__(self, just = None, width = None):
    self.just = just or self.JUST_LEFT
    self.width = width or 0

  def render(self, value, width = None, is_label = False):
    width = width or self.width or 0
    if value is not None:
      vs = self._value_to_string(value)
    else:
      vs = u''
    if self.just == self.JUST_LEFT:
      vs = vs.ljust(width)
    elif self.just == self.JUST_RIGHT:
      vs = vs.rjust(width)
    else:
      raise ValueError('Invalid just: %s' % (self.just))
    return vs

  def compute_width(self, value):
    return len(self.render(value, width = None))

  @classmethod
  def _value_to_string(self, value):
    if check.is_string(value):
      return value
    else:
      return str(value)
  
class text_table(object):
  'A table of strings.'

  def __init__(self, width = None, height = None, data = None,
               style = None, column_spacing = None, cell_renderer = None):
    self._labels = None
    self._table = table(width = width, height = height, data = data)
    self._style = check.check_text_table_style(style or text_table_style_basic())
    self._row_renderers = {}
    self._col_renderers = {}
    self._cell_renderers = {}
    self._default_cell_renderer = cell_renderer or text_cell_renderer()
    self._title = None
    
  def set_labels(self, labels):
    check.check_tuple(labels)
    self._table.check_width(len(labels))
    self._labels = labels[:]

  def set_title(self, title):
    check.check_string(title)
    self._title = title

  def set(self, x, y, s):
    check.check_string(s)
    self._table.set(x, y, s)
    
  def get(self, x, y):
    return self._table.get(x, y)

  def __str__(self):
    return self.to_string()

  def to_string(self, strip_rows = False):
    spacing = self._style.spacing()
    column_spacing = ' ' * spacing

    col_widths = self.column_widths()
    col_widths_with_spacing = [ (col + 2 * spacing) for col in col_widths ]
    num_cols = len(col_widths)

    box_style = self._style.box_style()
    
    v_char = box_style.v
    h_char = box_style.h
    tl_char = box_style.tl
    tr_char = box_style.tr
    
    total_cols_width = sum(col_widths_with_spacing)
    h_middle_width = total_cols_width + (num_cols - 1) * v_char.width
    h_width = tl_char.width + h_middle_width + tr_char.width

    buf = StringIO()
    
    if self._title:
      box_style.write_top(buf, h_width)
      buf.write('\n')
      box_style.write_centered_text(buf, h_width, self._title)
      buf.write('\n')
      if not self._labels:
        box_style.write_bottom(buf, h_width)
        buf.write('\n')
    
    if self._labels:
      box_style.write_middle(buf, h_width)
      buf.write('\n')
      buf.write(v_char.char)
      for x in range(0, self._table.width):
        buf.write(column_spacing)
        self._write_label(x, buf, col_widths)
        buf.write(column_spacing)
        buf.write(v_char.char)
      buf.write('\n')
      box_style.write_middle(buf, h_width)
      buf.write('\n')

    if not self._title or self._labels:
      box_style.write_top(buf, h_width)
      buf.write('\n')
      
    for y in range(0, self._table.height):
      row = self._table.row(y)
      assert len(row) == num_cols
      row_buf = StringIO()
      row_buf.write(v_char.char)
      for x in range(0, self._table.width):
        row_buf.write(column_spacing)
        self._write_cell(x, y, row_buf, col_widths)
        row_buf.write(column_spacing)
        row_buf.write(v_char.char)
      row_str = row_buf.getvalue()
      if strip_rows:
        row_str = row_str.strip()
      buf.write(row_str)
      buf.write('\n')
    box_style.write_bottom(buf, h_width)
    buf.write('\n')
    value = buf.getvalue()
    # remove the trailing new line
    return value[0:-1]

  def _write_cell(self, x, y, stream, col_widths):
    value = self._table.get(x, y)
    renderer = self.get_cell_renderer(x, y)
    assert renderer
    value_string = renderer.render(value, width = col_widths[x])
    #print('WRITING: %s - %s' % (value_string, type(value_string)))
    stream.write(value_string)
  
  def _write_label(self, x, stream, col_widths):
    value = self._labels[x]
    renderer = self.get_cell_renderer(x, 0)
    assert renderer
    value = renderer.render(value, width = col_widths[x], is_label = True)
    stream.write(value)
  
  def _column_width(self, x):
    self._table.check_x(x)
    max_col_width = self._max_column_width(x)
    if self._labels:
      max_col_width = max(max_col_width, len(self._labels[x]))
    return max_col_width
  
  def _max_column_width(self, x):
    self._table.check_x(x)
    max_width = 0
    for y in range(0, self._table.height):
      renderer = self.get_cell_renderer(x, y)
      value = self._table.get(x, y)
      max_width = max(max_width, renderer.compute_width(value))
    return max_width
  
  def sort_by_column(self, x):
    self._table.check_x(x)
    self._table.sort_by_column(x)

  def set_row(self, y, row):
    self._table.check_y(y)
    self._table.set_row(y, row)

  def set_row_renderer(self, y, renderer):
    self._table.check_y(y)
    self._row_renderers[y] = renderer

  def set_col_renderer(self, x, renderer):
    x = self._table.resolve_x(x)
    self._col_renderers[x] = renderer
    
  def set_cell_renderer(self, x, y, renderer):
    self._table.check_xy(x, y)
    self._cell_renderers[(x, y)] = renderer
    
  def get_cell_renderer(self, x, y):
    self._table.check_xy(x, y)
    return self._cell_renderers.get((x, y), None) or self._col_renderers.get(x, self._default_cell_renderer)

  def set_data(self, data):
    check.check_tuple_seq(data)
    self._table.set_data(data)

  def column_widths(self):
    return tuple([ self._column_width(x) for x in range(0, self._table.width) ])

  @property
  def default_cell_renderer(self):
    return self._default_cell_renderer
  
  @default_cell_renderer.setter
  def default_cell_renderer(self, renderer):
    if renderer:
      assert isinstance(renderer, text_cell_renderer)
    else:
      renderer = text_cell_renderer()
    self._default_cell_renderer = renderer
    #print('default renderer changed from %s to %s' % (self._default_cell_renderer, renderer))
