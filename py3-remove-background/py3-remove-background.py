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

plug_in_proc = "plug-in-remove-background"

plug_in_binary = "py3-remove-background"

def run(procedure, run_mode, image, drawables, config, data):

  if run_mode == Gimp.RunMode.INTERACTIVE:
    GimpUi.init(plug_in_binary)
    dialog = GimpUi.ProcedureDialog.new(procedure, config, None)
    box = dialog.fill_box("box", ["increase", "feather"])
    box.set_orientation (Gtk.Orientation.VERTICAL)
    box.set_spacing(20)
    dialog.fill(["box"])
    if not dialog.run():
      dialog.destroy()
      return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, None)
    else:
      dialog.destroy()

  addon = config.get_property('increase')
  feather = config.get_property('feather')
  Gimp.Selection.grow(image, addon)
  Gimp.Selection.feather(image, feather)
  drawables[0].add_alpha()
  drawables[0].edit_clear()

  return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, None)

class Copier (Gimp.PlugIn):
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
    procedure.set_documentation (_("Increase the selection by a few pixels. Feather it and remove"),
                                   None)
    procedure.set_menu_label(_("remove background"))
    procedure.set_attribution("Vladislav Lukianenko <majosue@student.42.fr>", "majosue", "2025")

    procedure.add_int_argument     ("increase", _("Increase selection"), None,
                                      1, 10000, 2, GObject.ParamFlags.READWRITE)
    procedure.add_int_argument     ("feather", _("Feather selection"), None,
                                      1, 10000, 15, GObject.ParamFlags.READWRITE)
    procedure.add_menu_path (_("<Image>"))
    return procedure

Gimp.main(Copier.__gtype__, sys.argv)
