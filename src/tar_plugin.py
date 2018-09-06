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

from .builtin_plugin import BuiltinHandlerMixin
from .remaster_plugin import IsoUnpackHandler, ChrootHandler
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
        super(TarHandler, self).__init__(*args, **kwargs)
        self._export_generic_info()

    def _get_tar_comp_method(self):
        comp_method = self.metadata.get('compression_method', "gz")
        return TarHandler._TAR_COMP_METHODS[comp_method]

    def setup(self):
        # setup compression method, default is gz
        tar_name = self.metadata.get(
            'tar_name',
            os.path.basename(self.metadata['source_iso']) + ".tar." +
            self.metadata.get('compression_method', "gz")
        )
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
                    _("spawning"), " ".join(exec_script),
                )
            )
            rc = molecule.utils.exec_cmd(exec_script, env=env)
            if rc != 0:
                self._output.output(
                    "[%s|%s] %s: %s" % (
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
                    _("spawning"), " ".join(exec_script),
                )
            )
            rc = molecule.utils.exec_cmd(exec_script, env=env)
            if rc != 0:
                self._output.output("[%s|%s] %s: %s" % (
                        blue("TarHandler"), darkred(self.spec_name),
                        _("post tar hook failed"), rc,
                    )
                )
                return rc

        return 0

    def kill(self, success=True):
        if not success:
            self._run_error_script(None, self.chroot_path, None)
        try:
            shutil.rmtree(self.metadata['chroot_tmp_dir'], True)
        except (shutil.Error, OSError,):
            pass
        return 0


class IsoToTarSpec(GenericSpec):

    PLUGIN_API_VERSION = 1

    @staticmethod
    def execution_strategy():
        return "iso_to_tar"

    @staticmethod
    def supported_compression_method(comp_m):
        return comp_m in SUPPORTED_COMPRESSION_METHODS

    def vital_parameters(self):
        return [
            "source_iso",
            "destination_tar_directory",
        ]

    def parameters(self):
        return {
            'execution_strategy': {
                'verifier': lambda x: len(x) != 0,
                'parser': lambda x: x.strip(),
            },
            'prechroot': {
                'verifier': self._verify_command_arguments,
                'parser': self._command_splitter,
            },
            'release_string': {
                'verifier': lambda x: len(x) != 0,  # validation callback
                'parser': lambda x: x.strip(),  # value extractor
            },
            'release_version': {
                'verifier': lambda x: len(x) != 0,
                'parser': lambda x: x.strip(),
            },
            'release_desc': {
                'verifier': lambda x: len(x) != 0,
                'parser': lambda x: x.strip(),
            },
            'release_file': {
                'verifier': lambda x: len(x) != 0,
                'parser': lambda x: x.strip(),
            },
            'source_iso': {
                'verifier': lambda x: "\0" not in x,
                'parser': lambda x: x.strip(),
            },
            'tar_name': {
                'verifier': lambda x: len(x) != 0,
                'parser': lambda x: x.strip(),
            },
            'compression_method': {
                'verifier': self.supported_compression_method,
                'parser': lambda x: x.strip(),
            },
            'error_script': {
                'verifier': self._verify_executable_arguments,
                'parser': self._command_splitter,
            },
            'outer_chroot_script': {
                'verifier': self._verify_executable_arguments,
                'parser': self._command_splitter,
            },
            'inner_chroot_script': {
                'verifier': self._verify_executable_arguments,
                'parser': self._command_splitter,
            },
            'inner_chroot_script_after': {
                'verifier': self._verify_executable_arguments,
                'parser': self._command_splitter,
            },
            'outer_chroot_script_after': {
                'verifier': self._verify_executable_arguments,
                'parser': self._command_splitter,
            },
            'destination_tar_directory': {
                'verifier': os.path.isdir,
                'parser': lambda x: x.strip(),
            },
            'pre_tar_script': {
                'verifier': self._verify_executable_arguments,
                'parser': self._command_splitter,
            },
            'post_tar_script': {
                'verifier': self._verify_executable_arguments,
                'parser': self._command_splitter,
            },
            'iso_mounter': {
                'verifier': lambda x: len(x) != 0,
                'parser': self._command_splitter,
            },
            'iso_umounter': {
                'verifier': lambda x: len(x) != 0,
                'parser': self._command_splitter,
            },
            'squash_mounter': {
                'verifier': lambda x: len(x) != 0,
                'parser': self._command_splitter,
            },
            'squash_umounter': {
                'verifier': lambda x: len(x) != 0,
                'parser': self._command_splitter,
            },
            'custom_packages_remove_cmd': {
                'verifier': lambda x: len(x) != 0,
                'parser': lambda x: x.strip(),
            },
            'custom_packages_add_cmd': {
                'verifier': lambda x: len(x) != 0,
                'parser': lambda x: x.strip(),
            },
            'packages_to_remove': {
                'verifier': lambda x: len(x) != 0,
                'parser': self._comma_separate,
            },
            'packages_to_add': {
                'verifier': lambda x: len(x) != 0,
                'parser': self._comma_separate,
            },
            'repositories_update_cmd': {
                'verifier': lambda x: len(x) != 0,
                'parser': self._command_splitter,
            },
            'execute_repositories_update': {
                'verifier': lambda x: len(x) != 0,
                'parser': lambda x: x.strip(),
            },
            'paths_to_remove': {
                'verifier': lambda x: len(x) != 0,
                'parser': self._comma_separate_path,
            },
            'paths_to_empty': {
                'verifier': lambda x: len(x) != 0,
                'parser': self._comma_separate_path,
            },
        }

    def execution_steps(self):
        return [IsoUnpackHandler, ChrootHandler, TarHandler]
