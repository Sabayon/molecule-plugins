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

import os
import shutil

from molecule.i18n import _
from molecule.output import blue, darkred
from molecule.specs.skel import GenericExecutionStep, GenericSpec
from molecule.specs.plugins.builtin_plugin import BuiltinHandlerMixin
from molecule.specs.plugins.remaster_plugin import IsoUnpackHandler, \
    ChrootHandler
import molecule.utils

SUPPORTED_COMPRESSION_METHODS = ["bz2", "gz"]

class TarHandler(GenericExecutionStep, BuiltinHandlerMixin):

    _TAR_EXEC = "/bin/tar"
    _TAR_COMP_METHODS = {
        "gz": "z",
        "bz2": "j",
    }
    MD5_EXT = ".md5"

    def __init__(self, *args, **kwargs):
        GenericExecutionStep.__init__(self, *args, **kwargs)

    def _get_tar_comp_method(self):
        comp_method = self.metadata.get('compression_method', "gz")
        return TarHandler._TAR_COMP_METHODS[comp_method]

    def setup(self):
        # setup compression method, default is gz
        tar_name = self.metadata.get('tar_name',
            os.path.basename(self.metadata['source_iso']) + ".tar." + \
            self.metadata.get('compression_method', "gz"))
        self.dest_path = os.path.join(
            self.metadata['destination_tar_directory'], tar_name)
        self.chroot_path = self.metadata['chroot_unpack_path']
        return 0

    def pre_run(self):
        self._output.output("[%s|%s] %s" % (
                blue("TarHandler"), darkred(self.spec_name),
                _("executing pre_run"),
            )
        )

        # run pre tar script
        exec_script = self.metadata.get('pre_tar_script')
        if exec_script:
            env = os.environ.copy()
            env['CHROOT_DIR'] = self.chroot_path
            env['TAR_PATH'] = self.dest_path
            env['TAR_CHECKSUM_PATH'] = self.dest_path + \
                TarHandler.MD5_EXT
            self._output.output("[%s|%s] %s: %s" % (
                    blue("TarHandler"), darkred(self.spec_name),
                    _("spawning"), exec_script,
                )
            )
            rc = molecule.utils.exec_cmd(exec_script, env = env)
            if rc != 0:
                self._output.output("[%s|%s] %s: %s" % (
                        blue("TarHandler"), darkred(self.spec_name),
                        _("pre tar hook failed"), rc,
                    )
                )
                return rc

        return 0

    def run(self):
        self._output.output("[%s|%s] %s => %s" % (
                blue("TarHandler"), darkred(self.spec_name),
                _("compressing chroot"),
                self.chroot_path,
            )
        )
        dest_path_dir = os.path.dirname(self.dest_path)
        if not os.path.isdir(dest_path_dir) and not \
            os.path.lexists(dest_path_dir):
            os.makedirs(dest_path_dir, 0o755)

        current_dir = os.getcwd()
        # change dir to chroot dir
        os.chdir(self.chroot_path)

        args = (TarHandler._TAR_EXEC, "cfp" + self._get_tar_comp_method(),
            self.dest_path, ".", "--atime-preserve", "--numeric-owner")
        rc = molecule.utils.exec_cmd(args)
        os.chdir(current_dir)
        if rc != 0:
            self._output.output("[%s|%s] %s: %s" % (
                    blue("TarHandler"), darkred(self.spec_name),
                    _("chroot compression failed"), rc,
                )
            )
            return rc
        self._output.output("[%s|%s] %s: %s" % (
                blue("TarHandler"), darkred(self.spec_name),
                _("generating md5 for"), self.dest_path,
            )
        )
        digest = molecule.utils.md5sum(self.dest_path)
        md5file = self.dest_path + TarHandler.MD5_EXT
        with open(md5file, "w") as f:
            f.write("%s  %s\n" % (digest, os.path.basename(self.dest_path),))
            f.flush()

        return 0

    def post_run(self):
        self._output.output("[%s|%s] %s" % (
                blue("TarHandler"), darkred(self.spec_name),
                _("executing post_run"),
            )
        )

        # run post tar script
        exec_script = self.metadata.get('post_tar_script')
        if exec_script:
            env = os.environ.copy()
            env['CHROOT_DIR'] = self.chroot_path
            env['TAR_PATH'] = self.dest_path
            env['TAR_CHECKSUM_PATH'] = self.dest_path + \
                TarHandler.MD5_EXT
            self._output.output("[%s|%s] %s: %s" % (
                    blue("TarHandler"), darkred(self.spec_name),
                    _("spawning"), exec_script,
                )
            )
            rc = molecule.utils.exec_cmd(exec_script, env = env)
            if rc != 0:
                self._output.output("[%s|%s] %s: %s" % (
                        blue("TarHandler"), darkred(self.spec_name),
                        _("post tar hook failed"), rc,
                    )
                )
                return rc

        return 0

    def kill(self, success = True):
        if not success:
            self._run_error_script(None, self.chroot_path, None)
            try:
                shutil.rmtree(self.metadata['chroot_tmp_dir'], True)
            except (shutil.Error, OSError,):
                pass
        return 0

class IsoToTarSpec(GenericSpec):

    PLUGIN_API_VERSION = 0

    @staticmethod
    def execution_strategy():
        return "iso_to_tar"

    def supported_compression_method(self, comp_m):
        return comp_m in SUPPORTED_COMPRESSION_METHODS

    def vital_parameters(self):
        return [
            "source_iso",
            "destination_tar_directory",
        ]

    def parser_data_path(self):
        return {
            'prechroot': {
                'cb': self.valid_exec_first_list_item,
                've': self.ve_string_splitter,
            },
            'release_string': {
                'cb': self.ne_string, # validation callback
                've': self.ve_string_stripper, # value extractor
            },
            'release_version': {
                'cb': self.ne_string,
                've': self.ve_string_stripper,
            },
            'release_desc': {
                'cb': self.ne_string,
                've': self.ve_string_stripper,
            },
            'release_file': {
                'cb': self.ne_string,
                've': self.ve_string_stripper,
            },
            'source_iso': {
                'cb': self.valid_path_string,
                've': self.ve_string_stripper,
            },
            'tar_name': {
                'cb': self.ne_string,
                've': self.ve_string_stripper,
            },
            'compression_method': {
                'cb': self.supported_compression_method,
                've': self.ve_string_stripper,
            },
            'error_script': {
                'cb': self.valid_exec_first_list_item,
                've': self.ve_string_splitter,
            },
            'outer_chroot_script': {
                'cb': self.valid_exec_first_list_item,
                've': self.ve_string_splitter,
            },
            'inner_chroot_script': {
                'cb': self.valid_path_string_first_list_item,
                've': self.ve_string_splitter,
            },
            'inner_chroot_script_after': {
                'cb': self.valid_path_string_first_list_item,
                've': self.ve_string_splitter,
            },
            'outer_chroot_script_after': {
                'cb': self.valid_exec_first_list_item,
                've': self.ve_string_splitter,
            },
            'destination_tar_directory': {
                'cb': self.valid_dir,
                've': self.ve_string_stripper,
            },
            'pre_tar_script': {
                'cb': self.valid_exec_first_list_item,
                've': self.ve_string_splitter,
            },
            'post_tar_script': {
                'cb': self.valid_exec_first_list_item,
                've': self.ve_string_splitter,
            },
            'iso_mounter': {
                'cb': self.ne_list,
                've': self.ve_string_splitter,
            },
            'iso_umounter': {
                'cb': self.ne_list,
                've': self.ve_string_splitter,
            },
            'squash_mounter': {
                'cb': self.ne_list,
                've': self.ve_string_splitter,
            },
            'squash_umounter': {
                'cb': self.ne_list,
                've': self.ve_string_splitter,
            },
            'custom_packages_remove_cmd': {
                'cb': self.valid_ascii,
                've': self.ve_string_stripper,
            },
            'custom_packages_add_cmd': {
                'cb': self.valid_ascii,
                've': self.ve_string_stripper,
            },
            'packages_to_remove': {
                'cb': self.ne_list,
                've': self.valid_comma_sep_list,
            },
            'packages_to_add': {
                'cb': self.ne_list,
                've': self.valid_comma_sep_list,
            },
            'repositories_update_cmd': {
                'cb': self.ne_list,
                've': self.ve_string_splitter,
            },
            'execute_repositories_update': {
                'cb': self.valid_ascii,
                've': self.ve_string_stripper,
            },
            'paths_to_remove': {
                'cb': self.ne_list,
                've': self.valid_path_list,
            },
            'paths_to_empty': {
                'cb': self.ne_list,
                've': self.valid_path_list,
            },
        }

    def get_execution_steps(self):
        return [IsoUnpackHandler, ChrootHandler, TarHandler]
