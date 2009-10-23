# -*- coding: utf-8 -*-
#    Molecule Disc Image builder for Sabayon Linux
#    Copyright (C) 2009 Fabio Erculiani
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

from molecule.i18n import _
from molecule.output import red, brown, blue, green, purple, darkgreen, \
    darkred, bold, darkblue, readtext
from molecule.specs.skel import GenericExecutionStep, GenericSpec

class IsoUnpackHandler(GenericExecutionStep):

    def __init__(self, *args, **kwargs):
        GenericExecutionStep.__init__(self, *args, **kwargs)

    def pre_run(self):
        self.Output.updateProgress("[%s|%s] %s" % (
                blue("IsoUnpackHandler"),darkred(self.spec_name),
                _("executing pre_run"),
            )
        )
        # FIXME: make it working
        return 0

    def post_run(self):
        self.Output.updateProgress("[%s|%s] %s" % (
                blue("IsoUnpackHandler"),darkred(self.spec_name),
                _("executing post_run"),
            )
        )
        return 0

    def kill(self):
        self.Output.updateProgress("[%s|%s] %s" % (
                blue("IsoUnpackHandler"),darkred(self.spec_name),
                _("executing kill"),
            )
        )
        return 0

    def run(self):

        self.Output.updateProgress("[%s|%s] %s" % (
                blue("IsoUnpackHandler"),darkred(self.spec_name),
                _("iso unpacker running"),
            )
        )
        return 0

from molecule.specs.plugins.builtin import ChrootHandler as BuiltinChrootHandler
class ChrootHandler(BuiltinChrootHandler):

    # INFO: Make external chroot, internal chroot hooks execution working

    def pre_run(self):
        self.Output.updateProgress("[%s|%s] %s" % (
                blue("ChrootHandler"),darkred(self.spec_name),
                _("executing pre_run"),
            )
        )
        return 0

    def post_run(self):
        self.Output.updateProgress("[%s|%s] %s" % (
                blue("ChrootHandler"),darkred(self.spec_name),
                _("executing post_run"),
            )
        )
        return 0

    def run(self):

        self.Output.updateProgress("[%s|%s] %s" % (
                blue("ChrootHandler"),darkred(self.spec_name),
                _("hooks running"),
            )
        )
        # FIXME: make parent method working
        return 0


from molecule.specs.plugins.builtin import CdrootHandler as BuiltinCdrootHandler
class CdrootHandler(BuiltinCdrootHandler):

    # INFO: create cdroot dir back, compress chroot

    def pre_run(self):
        self.Output.updateProgress("[%s|%s] %s" % (
                blue("CdrootHandler"),darkred(self.spec_name),
                _("executing pre_run"),
            )
        )
        # FIXME: make parent method working
        return 0

    def run(self):
        self.Output.updateProgress("[%s|%s] %s" % (
                blue("CdrootHandler"),darkred(self.spec_name),
                _("compressing chroot"),
            )
        )
        # FIXME: make parent method working
        return 0

from molecule.specs.plugins.builtin import IsoHandler as BuiltinIsoHandler
class IsoHandler(BuiltinIsoHandler):

    def pre_run(self):
        self.Output.updateProgress("[%s|%s] %s" % (
                blue("IsoHandler"),darkred(self.spec_name),
                _("executing pre_run"),
            )
        )
        # FIXME: make parent method working
        return 0

    def run(self):
        self.Output.updateProgress("[%s|%s] %s" % (
                blue("IsoHandler"),darkred(self.spec_name),
                _("building ISO image"),
            )
        )
        # FIXME: make parent method working
        return 0

class RemasterSpec(GenericSpec):

    @staticmethod
    def execution_strategy():
        return "iso_remaster"

    def vital_parameters(self):
        return [
            "source_iso",
            "destination_iso_directory",
        ]

    def parser_data_path(self):
        return {
            'prechroot': {
                'cb': self.valid_exec_first_list_item,
                've': self.ve_string_splitter,
            },
            'source_iso': {
                'cb': self.valid_path_string,
                've': self.ve_string_stripper,
            },
            'outer_chroot_script': {
                'cb': self.valid_exec,
                've': self.ve_string_stripper,
            },
            'inner_chroot_script': {
                'cb': self.valid_path_string,
                've': self.ve_string_stripper,
            },
            'extra_mkisofs_parameters': {
                'cb': self.always_valid,
                've': self.ve_string_splitter,
                'mod': self.ve_string_splitter,
            },
            'pre_iso_script': {
                'cb': self.valid_exec,
                've': self.ve_string_stripper,
            },
            'destination_iso_directory': {
                'cb': self.valid_dir,
                've': self.ve_string_stripper,
            },
            'destination_iso_image_name': {
                'cb': self.valid_ascii,
                've': self.ve_string_stripper,
            },
        }

    def get_execution_steps(self):
        return [IsoUnpackHandler, ChrootHandler, CdrootHandler, IsoHandler]
