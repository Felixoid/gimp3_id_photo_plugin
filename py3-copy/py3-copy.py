#!/usr/bin/env python3
#coding: utf-8

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
from gi.repository import GObject
from gi.repository import GLib
from gi.repository import Gtk
from gi.repository import Gio
import sys

def N_(message): return message
def _(message): return GLib.dgettext(None, message)

plug_in_proc = "plug-in-copy-to-size"
plug_in_binary = "py3-copy"

def mm_to_px(val):
  return int(val * 11.811)

SIZES = {
  "custom":  {"label": _("Custom"),     "width": 0,  "height": 0,   "guides": ""},
  "21x30":   {"label": "2.1x3",         "width": 21, "height": 30,  "guides": ""},
  "25x35":   {"label": "2.5x3.5",       "width": 25, "height": 35,  "guides": ""},
  "30x40":   {"label": "3x4",           "width": 30, "height": 40,  "guides": ""},
  "35x45":   {"label": "3.5x4.5",       "width": 35, "height": 45,  "guides": "20 60 36 102 400 308 436 355"},
  "36x47":   {"label": "3.6x4.7",       "width": 36, "height": 47,  "guides": "29 0 407 0 454"},
  "40x40":   {"label": "4x4",           "width": 40, "height": 40,  "guides": ""},
  "43x55":   {"label": "4.3x5.5",       "width": 43, "height": 55,  "guides": ""},
  "48x33":   {"label": "4.8x3.3",       "width": 33, "height": 48,  "guides": "36 59 59 106 367 283 426 330"},
  "50x40":   {"label": "5x4",           "width": 40, "height": 50,  "guides": ""},
  "50x50":   {"label": "5x5",           "width": 50, "height": 50,  "guides": "63 0 172 0 259 0 402"},
  "60x40":   {"label": "6x4",           "width": 40, "height": 60,  "guides": ""},
  "60x45":   {"label": "6x4.5",         "width": 45, "height": 60,  "guides": ""},
  "90x120":  {"label": "9x12",          "width": 90, "height": 120, "guides": ""},
}

sizes_choice = Gimp.Choice.new()
for i, (nick, info) in enumerate(SIZES.items()):
  sizes_choice.add(nick, i, info["label"], "")

def update_custom_visibility(config, pspec, data):
  custom_box, dialog = data
  is_custom = config.get_property('size') == 'custom'
  custom_box.set_visible(is_custom)
  if not is_custom:
    dialog.resize(1, 1)

def copier_run(procedure, run_mode, image, drawables, config, data):
  if run_mode == Gimp.RunMode.INTERACTIVE:
    GimpUi.init(plug_in_binary)
    dialog = GimpUi.ProcedureDialog.new(procedure, config, _("Copy to size"))
    custom_box = dialog.fill_box("custom-box", ["custom_width", "custom_height", "guides"])
    config.connect("notify::size", update_custom_visibility, (custom_box, dialog))
    dialog.fill(["size", "custom-box"])
    custom_box.set_visible(config.get_property('size') == 'custom')
    if not dialog.run():
      dialog.destroy()
      return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, None)
    else:
      dialog.destroy()

  size_nick = config.get_property('size')
  info = SIZES[size_nick]

  if size_nick == "custom":
    width = config.get_property('custom_width')
    height = config.get_property('custom_height')
    guides = config.get_property('guides')
  else:
    width = mm_to_px(info["width"])
    height = mm_to_px(info["height"])
    guides = info["guides"]

  Gimp.edit_copy_visible(image)
  new_image = Gimp.Image.new(width, height, 0)
  new_layer = Gimp.Layer.new(new_image, None, width, height, 0, 100, 0)
  new_image.insert_layer(new_layer, None, 0)
  new_layer.fill(Gimp.FillType.WHITE)
  float_layer = Gimp.edit_paste(new_layer, False)
  Gimp.floating_sel_to_layer(float_layer[0])
  new_image.add_hguide(0)
  new_image.add_hguide(height)
  new_image.add_vguide(0)
  new_image.add_vguide(width)
  new_image.add_vguide(int(width / 2))
  if guides:
    str_values = guides.split()
    for i in range(len(str_values)):
      if i % 2:
        new_image.add_vguide(int(str_values[i]))
      else:
        new_image.add_hguide(int(str_values[i]))
  Gimp.Display.new(new_image)
  return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, None)

class Copier (Gimp.PlugIn):
  def do_set_i18n(self, procname):
    return True, 'ru', None
  def do_query_procedures(self):
    return [ plug_in_proc ]

  def do_create_procedure(self, name):
    procedure = Gimp.ImageProcedure.new(self, name,
                                        Gimp.PDBProcType.PLUGIN,
                                        copier_run, None)
    procedure.set_sensitivity_mask(Gimp.ProcedureSensitivityMask.DRAWABLE)
    procedure.set_documentation(_("Copy picture to new image with a chosen size"),
                                None)
    procedure.set_attribution("Vladislav Lukianenko <majosue@student.42.fr>", "majosue", "2025")
    procedure.set_menu_label(_("Convert to size..."))
    procedure.add_choice_argument("size", _("Photo size"), _("Photo size"),
                                 sizes_choice, "35x45", GObject.ParamFlags.READWRITE)
    procedure.add_int_argument("custom_width", _("Custom width (px)"), _("Width in pixels for custom size"),
                               1, 10000, 100, GObject.ParamFlags.READWRITE)
    procedure.add_int_argument("custom_height", _("Custom height (px)"), _("Height in pixels for custom size"),
                               1, 10000, 200, GObject.ParamFlags.READWRITE)
    procedure.add_string_argument("guides", _("Guides (custom size)"), _("Guides coordinates: \"horizontal vertical horizontal vertical...\""),
                                 "", GObject.ParamFlags.READWRITE)
    procedure.add_menu_path(_("<Image>/I_D Photo"))
    return procedure

Gimp.main(Copier.__gtype__, sys.argv)
