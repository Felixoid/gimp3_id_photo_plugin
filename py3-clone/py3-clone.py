#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
from gi.repository import GObject
from gi.repository import GLib
from gi.repository import Gtk
from gi.repository import Gio
from gi.repository import Gegl
from datetime import datetime
from pathlib import Path

from datetime import datetime
import sys
import os
from pathlib import Path

def N_(message): return message
def _(message): return GLib.dgettext(None, message)

plug_in_proc = "plug-in-clone"

plug_in_binary = "py3-clone"

SAVE_DIR = str(Path.home() / "Desktop" / "arch_photo")

FORMATS = {
  "unlimited": {"label": _("Unlimited"), "width": 0,   "height": 0},
  "10x15":     {"label": "10x15 cm",     "width": 100, "height": 150},
  "13x18":     {"label": "13x18 cm",     "width": 130, "height": 180},
  "15x20":     {"label": "15x20 cm",     "width": 150, "height": 200},
  "A6":        {"label": "A6",           "width": 105, "height": 148},
  "A5":        {"label": "A5",           "width": 148, "height": 210},
  "A4":        {"label": "A4",           "width": 210, "height": 297},
}

formats = Gimp.Choice.new()
for i, (nick, info) in enumerate(FORMATS.items()):
  formats.add(nick, i, info["label"], "")

CROSS_SIZE = 19
CROSS_COLOR = "black"
FONT_NAME = "DejaVu Serif Condensed"
FONT_SIZE = 20

class DecoratedImage:

  def __init__(self, v_text, h_text, image):
    self.__image = image.duplicate()
    self.__v_text = v_text
    self.__h_text = h_text
    self.__overlap = 0
    self.__cross_size = 0

  def save_image_to_archive(self, save_dir):
    self.__image.flatten()
    self.__image.crop(self.__image.get_width(),
                      self.__image.get_height(), 0, 0)
    now = datetime.now()
    name = now.strftime("%Y-%m-%d-%H-%M-%S")
    os.makedirs(save_dir, exist_ok=True)
    file_name = str(Path(save_dir) / f"{name}.jpg")
    file = Gio.File.new_for_path(file_name)
    self.__image.set_file(file)
    Gimp.file_save(Gimp.RunMode.NONINTERACTIVE,
                  self.__image, file, None)

  def add_marks(self):
    self.__cross_size = CROSS_SIZE
    offset = self.__cross_size // 2 + 1
    offset2 = offset - 1
    cross_layer = Gimp.Layer.new(self.__image, None, self.__cross_size, self.__cross_size,
                                Gimp.ImageType.RGBA_IMAGE, 100, 0)
    for i in range(self.__cross_size):
      cross_layer.set_pixel(i, self.__cross_size // 2, Gegl.Color.new(CROSS_COLOR))
      cross_layer.set_pixel(self.__cross_size // 2, i, Gegl.Color.new(CROSS_COLOR))
    self.__image.insert_layer(cross_layer, None, 0)
    cross_layer.set_offsets(-offset, -offset)
    cross_layer = cross_layer.copy()
    self.__image.insert_layer(cross_layer, None, 0)
    cross_layer.set_offsets(self.__image.get_width() - offset2, -offset)
    cross_layer = cross_layer.copy()
    self.__image.insert_layer(cross_layer, None, 0)
    cross_layer.set_offsets(self.__image.get_width() - offset2,
                            self.__image.get_height() - offset2)
    cross_layer = cross_layer.copy()
    self.__image.insert_layer(cross_layer, None, 0)
    cross_layer.set_offsets(-offset, self.__image.get_height() - offset2)
    self.__image.resize_to_layers()
    #self.__image.merge_visible_layers(Gimp.MergeType.CLIP_TO_IMAGE)
    self.__overlap = self.__cross_size

  def add_text(self, add_date=True):
    if add_date:
      now = datetime.now()
      self.__h_text = self.__h_text + " " + now.strftime("%d-%m-%Y")
    font = Gimp.Font.get_by_name(FONT_NAME)
    size = FONT_SIZE
    unit = Gimp.Unit.pixel()
    gap = size - (self.__cross_size // 2)
    width = self.__image.get_width() + gap
    height = self.__image.get_height() + gap
    self.__image.resize(width, height, 0, 0)
    h_text_layer = Gimp.TextLayer.new(self.__image, self.__h_text, font, size, unit)
    h_text_layer.set_offsets(self.__cross_size, height - size)
    v_text_layer = Gimp.TextLayer.new(self.__image, self.__v_text, font, size, unit)
    self.__image.insert_layer(v_text_layer, None, 0)
    v_text_layer = v_text_layer.transform_rotate(1.57, False, 0, 0)
    v_text_layer.set_offsets(width - size, self.__cross_size)
    self.__image.insert_layer(h_text_layer, None, 0)
    #self.__image.merge_visible_layers(Gimp.MergeType.CLIP_TO_IMAGE)
    self.__overlap = self.__cross_size // 2

  def get_overlap(self):
    return self.__overlap

  def get_image(self):
    return self.__image

  def display(self):
    return Gimp.Display.new(self.__image)

class Reproducer:
  def __init__(self, image, overlap, canv_width, canv_height, clear_guides=False):
    self.__original_image = image
    self.__image = None
    self.__overlap = overlap
    self.__clear_guides = clear_guides
    # Auto-orient canvas to fit more photos
    img_w = image.get_width() - overlap
    img_h = image.get_height() - overlap
    portrait_fit = (canv_width // img_w) * (canv_height // img_h)
    landscape_fit = (canv_height // img_w) * (canv_width // img_h)
    if landscape_fit > portrait_fit:
      self.__canv_width = canv_height
      self.__canv_height = canv_width
    else:
      self.__canv_width = canv_width
      self.__canv_height = canv_height

  def get_image(self):
    if not self.__image:
      self.__image = self.__original_image.duplicate()
      if self.__clear_guides:
        guide = self.__image.find_next_guide(0)
        while guide != 0:
          next_guide = self.__image.find_next_guide(guide)
          self.__image.delete_guide(guide)
          guide = next_guide
      self.__image.merge_visible_layers(Gimp.MergeType.CLIP_TO_IMAGE)
    return self.__image

  def can_fit_image(self):
    return self.__canv_width - self.__original_image.get_width() > 0 \
            and self.__canv_height - self.__original_image.get_height() > 0

  def reproduce_unlimited(self, col_nbr, row_nbr):
    image = self.get_image()
    width = image.get_width() - self.__overlap
    height = image.get_height() - self.__overlap
    Gimp.edit_copy_visible(image)
    layers = image.get_layers()
    selection = None
    if col_nbr > self.__canv_width // width:
      col_nbr = self.__canv_width // width
    if row_nbr > self.__canv_height // height:
      row_nbr = self.__canv_height // height
    p_nbr = col_nbr * row_nbr
    for i in range(1, p_nbr):
      selection = Gimp.edit_paste(layers[0], False)[0]
      selection.set_offsets(i % col_nbr * width,
                            i // col_nbr * height)
      Gimp.floating_sel_anchor(selection)
    image.resize_to_layers()
    return p_nbr

  def display(self):
    new_layer = self.__image.get_layers()[0].copy()
    self.__image.insert_layer(new_layer, None, -1)
    self.__image.get_layers()[1].resize_to_image_size()
    self.__image.get_layers()[1].fill(Gimp.FillType.WHITE)
    Gimp.Display.new(self.get_image())

  def reproduce(self, p_nbr, clip):
    image = self.get_image()
    width = image.get_width() - self.__overlap
    height = image.get_height() - self.__overlap
    col_nbr = self.__canv_width // width
    row_nbr = self.__canv_height // height
    if col_nbr and col_nbr * width + self.__overlap > self.__canv_width:
      col_nbr = col_nbr - 1
    if row_nbr and row_nbr * height + self.__overlap > self.__canv_height:
      row_nbr = row_nbr - 1
    max_p = col_nbr * row_nbr
    if max_p == 0:
     return max_p
    elif p_nbr > max_p:
      p_nbr = max_p
    Gimp.edit_copy_visible(image)
    layers = image.get_layers()
    selection = None
    for i in range(1, p_nbr):
      selection = Gimp.edit_paste(layers[0], False)[0]
      selection.set_offsets(i % col_nbr * width,
                            i // col_nbr * height)
      Gimp.floating_sel_anchor(selection)
    if clip:
      image.resize_to_layers()
    else:
      image.resize(self.__canv_width, self.__canv_height, 0, 0)
    return p_nbr

def mm_to_px(val):
  return int(val * 11.811)

def get_canv_size(format_nick):
  info = FORMATS[format_nick]
  if info["width"] == 0:
    return Gimp.MAX_IMAGE_SIZE, Gimp.MAX_IMAGE_SIZE
  return mm_to_px(info["width"]), mm_to_px(info["height"])

def update_clip_visibility(config, pspec, data):
  clip_widget, dialog = data
  is_format = config.get_property('format') != 'unlimited'
  clip_widget.set_visible(is_format)
  if not is_format:
    dialog.resize(1, 1)

def run(procedure, run_mode, image, drawables, config, data):
  if run_mode == Gimp.RunMode.INTERACTIVE:
    GimpUi.init(plug_in_binary)
    dialog = GimpUi.ProcedureDialog.new(procedure, config, _("Reproduce"))
    format = dialog.get_widget("format", GObject.TYPE_NONE)
    format.set_hexpand(False)
    clip_widget = dialog.get_widget("clip_result", GObject.TYPE_NONE)
    box = dialog.fill_box("options-box", ["add_marks", "add_text", "add_date", "clip_result", "clear_guides"])
    box.set_spacing(20)
    box.set_orientation(Gtk.Orientation.HORIZONTAL)
    dialog.fill_expander("expander", None, False, "options-box")
    box2 = dialog.fill_box("box", ["p_number", "rows_number"])
    box2.set_orientation(Gtk.Orientation.HORIZONTAL)
    config.connect("notify::format", update_clip_visibility, (clip_widget, dialog))
    dialog.fill(["h_text", "v_text", "box", "format", "expander", "save_dir"])
    clip_widget.set_visible(config.get_property('format') != 'unlimited')
    if not dialog.run():
      dialog.destroy()
      return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, None)
    else:
      dialog.destroy()

  p_nbr = config.get_property('p_number')
  r_nbr = config.get_property('rows_number')
  marks = config.get_property('add_marks')
  text = config.get_property('add_text')
  add_date = config.get_property('add_date')
  format_name = config.get_property('format')
  h_text = config.get_property('h_text')
  v_text = config.get_property('v_text')
  canv_width, canv_height = get_canv_size(format_name)
  clip = True
  if format_name != "unlimited":
    clip = config.get_property('clip_result')
  new_image = None
  new_canvas = None
  result = 0

  save_dir = config.get_property('save_dir')
  new_image = DecoratedImage(v_text, h_text, image)
  new_image.save_image_to_archive(save_dir)
  if marks:
    new_image.add_marks()
  if text:
    new_image.add_text(add_date)
  clear_guides = config.get_property('clear_guides')
  new_canvas = Reproducer(new_image.get_image(), new_image.get_overlap(),
                          canv_width, canv_height, clear_guides)
  if not new_canvas.can_fit_image():
      Gimp.message(_("The image is too big"))
      Gimp.PlugIn.quit()
  if not r_nbr:
    result = new_canvas.reproduce(p_nbr, clip)
    if result != p_nbr:
      Gimp.message(_("The number of copies has been reduced"))
  else:
    result = new_canvas.reproduce_unlimited(p_nbr, r_nbr)
    if result != p_nbr * r_nbr:
      Gimp.message(_("The number of copies has been reduced"))
  new_canvas.display()
  return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, None)

class Clone (Gimp.PlugIn):

  def do_set_i18n(self, procname):
    return True, 'ru', None

  def do_query_procedures(self):
    return [ plug_in_proc ]

  def do_create_procedure(self, name):
    procedure = None
    procedure = Gimp.ImageProcedure.new(self, name,
                                          Gimp.PDBProcType.PLUGIN,
                                          run, None)
    procedure.set_sensitivity_mask (Gimp.ProcedureSensitivityMask.DRAWABLE)
    procedure.set_documentation (_("Replicates an image within a given format"),
                                   None)
    procedure.set_attribution("Vladislav Lukianenko <majosue@student.42.fr>", "majosue", "2025")
    if name == plug_in_proc:
      procedure.set_menu_label(_("Prepare for printing..."))
      procedure.add_int_argument     ("p_number", _("Number of columns"), _("Number of copies / columns"),
                                      1, 10000, 8, GObject.ParamFlags.READWRITE)
      procedure.add_int_argument     ("rows_number", _("Number of rows"), _("Number of rows"),
                                      0, 10000, 0, GObject.ParamFlags.READWRITE)
      procedure.add_string_argument ("v_text", _("V. text"), _("Vertical text"),
                                   "Моментальное фото оцифровка видео", GObject.ParamFlags.READWRITE)
      procedure.add_string_argument ("h_text", _("H. text"), _("Horizontal text"),
                                   "Мира 37Б", GObject.ParamFlags.READWRITE)
      procedure.add_boolean_argument ("add_marks", _("Add cut marks"), _("Add cut marks"),
                                   True, GObject.ParamFlags.READWRITE)
      procedure.add_boolean_argument ("add_text", _("Add text"), _("Add text"),
                                   True, GObject.ParamFlags.READWRITE)
      procedure.add_boolean_argument ("add_date", _("Add date"), _("Add current date to text"),
                                   True, GObject.ParamFlags.READWRITE)
      procedure.add_boolean_argument ("clip_result", _("Clip to result"), _("Clip to result"),
                                   True, GObject.ParamFlags.READWRITE)
      procedure.add_boolean_argument ("clear_guides", _("Clear guides"), _("Remove guides from the output image"),
                                   True, GObject.ParamFlags.READWRITE)
      procedure.add_choice_argument ("format",  _("Paper format"), _("Paper format"),
                                   formats, "10x15", GObject.ParamFlags.READWRITE)
      procedure.add_string_argument ("save_dir", _("Archive directory"), _("Directory to save archived photos"),
                                   SAVE_DIR, GObject.ParamFlags.READWRITE)
    procedure.add_menu_path (_("<Image>/I_D Photo"))
    return procedure

Gimp.main(Clone.__gtype__, sys.argv)
