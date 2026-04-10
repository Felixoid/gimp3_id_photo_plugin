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

plug_in_proc = "plug-in-copy-to-box"

plug_in_proc2 = "plug-in-copy-to-30x40"
plug_in_proc3 = "plug-in-copy-to-35x45"
plug_in_proc4 = "plug-in-copy-to-36x47"
plug_in_proc5 = "plug-in-copy-to-40x40"
plug_in_proc6 = "plug-in-copy-to-60x40"
plug_in_proc7 = "plug-in-copy-to-60x45"
plug_in_proc8 = "plug-in-copy-to-50x50"
plug_in_proc9 = "plug-in-copy-to-50x40"
plug_in_proc10 = "plug-in-copy-to-90x120"
plug_in_proc11 = "plug-in-copy-to-48x33"
plug_in_proc12 = "plug-in-copy-to-25x35"
plug_in_proc13 = "plug-in-copy-to-21x30"
plug_in_proc14 = "plug-in-copy-to-43x55"

def mm_to_px(val):
  return int(val * 11.811)

def copier_run(procedure, run_mode, image, drawables, config, data):
  width = config.get_property('width')
  height = config.get_property('height')
  guides = config.get_property('guides')
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
    for i in range (len(str_values)):
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
    return [ plug_in_proc, plug_in_proc2, plug_in_proc3, plug_in_proc4,
            plug_in_proc5, plug_in_proc6, plug_in_proc7, plug_in_proc8,
            plug_in_proc9, plug_in_proc10, plug_in_proc11, plug_in_proc12,
            plug_in_proc13, plug_in_proc14
	    ]

  def do_create_procedure(self, name):
    procedure = None
    width = 0
    height = 0
    guides = ""
    procedure = Gimp.ImageProcedure.new(self, name,
                                          Gimp.PDBProcType.PLUGIN,
                                          copier_run, None)
    procedure.set_sensitivity_mask (Gimp.ProcedureSensitivityMask.DRAWABLE)
    procedure.set_documentation (_("Copy picture to new image with size {name}mm").format(name=name.split('-')[4]),
                                   None)
    procedure.set_attribution("Vladislav Lukianenko <majosue@student.42.fr>", "majosue", "2025")
    if name == plug_in_proc:
      procedure.add_int_argument     ("width", "width", None,
                                      1, 10000, 100, GObject.ParamFlags.READWRITE)
      procedure.add_int_argument     ("height", "height", None,
                                      1, 10000, 200, GObject.ParamFlags.READWRITE)
      return procedure
    elif name == plug_in_proc2:
      procedure.set_menu_label("3x4")
      width = 30
      height = 40
    elif name == plug_in_proc3:
      procedure.set_menu_label("3.5x4.5")
      width = 35
      height = 45
      guides = "20 60 36 102 400 308 436 355"
    elif name == plug_in_proc4:
      procedure.set_menu_label(_("3,6x4,7"))
      width = 36
      height = 47
      guides = "29 0 407 0 454"
    elif name == plug_in_proc5:
      procedure.set_menu_label("4x4")
      width = 40
      height = 40
    elif name == plug_in_proc6:
      procedure.set_menu_label("6x4")
      width = 40
      height = 60
    elif name == plug_in_proc7:
      procedure.set_menu_label("6x4,5")
      width = 45
      height = 60
    elif name == plug_in_proc8:
      procedure.set_menu_label("5x5")
      width = 50
      height = 50
      guides = "63 0 172 0 259 0 402"
    elif name == plug_in_proc9:
      procedure.set_menu_label("5x4")
      width = 40
      height = 50
    elif name == plug_in_proc10:
      procedure.set_menu_label("9x12")
      width = 90
      height = 120
    elif name == plug_in_proc11:
      procedure.set_menu_label(_("4,8x3,3"))
      width = 33
      height = 48
      guides = "36 59 59 106 367 283 426 330"
    elif name == plug_in_proc12:
      procedure.set_menu_label(_("2,1x3"))
      width = 21
      height = 30
    elif name == plug_in_proc13:
      procedure.set_menu_label("2,5x3,5")
      width = 25
      height = 35
    elif name == plug_in_proc14:
      procedure.set_menu_label(_("4,3x5,5"))
      width = 43
      height = 55

    procedure.add_int_argument     ("width", "width", None,
                                      1, 10000, mm_to_px(width), GObject.ParamFlags.READABLE)
    procedure.add_int_argument     ("height", "height", None,
                                      1, 10000, mm_to_px(height), GObject.ParamFlags.READABLE)
    procedure.add_string_argument ("guides", "guides", _("String with guides coordinates \"horizontal vertical horizontal vertical...\""),
                                   guides, GObject.ParamFlags.READABLE)
    procedure.add_menu_path (_("<Image>/i_d photo"))
    return procedure

Gimp.main(Copier.__gtype__, sys.argv)
