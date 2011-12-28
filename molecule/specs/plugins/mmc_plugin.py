# -*- coding: utf-8 -*-
#    Molecule Disc Image builder for Sabayon Linux
#    Copyright (C) 2012 Fabio Erculiani
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
import tempfile
import errno

from molecule.i18n import _
from molecule.output import blue, darkred
from molecule.specs.skel import GenericExecutionStep, GenericSpec
from molecule.specs.plugins.builtin_plugin import BuiltinHandlerMixin
import molecule.utils


class ImageHandler(GenericExecutionStep, BuiltinHandlerMixin):

    LOSETUP_EXEC = "/sbin/losetup"
    MB_IN_BYTES = 1024000

    def __init__(self, *args, **kwargs):
        GenericExecutionStep.__init__(self, *args, **kwargs)
        # init variables
        self.image_mb = 0
        self._tmp_image_file_fd = None
        self._tmp_image_file = None

    def setup(self):

        self.image_mb = self.metadata['image_mb']

        try:
            self._tmp_image_file_fd, self._tmp_image_file = \
                tempfile.mkstemp(prefix = "molecule",
                                 dir = self._config['tmp_dir'],
                                 suffix=".mmc_img")
        except (OSError, IOError,) as err:
            self._output.output("[%s|%s] %s: %s" % (
                    blue("ImageHandler"), darkred(self.spec_name),
                    _("setup hook failed"), _("cannot create temporary file"),
                )
            )
            return 1

        self.metadata['MmcImageHandler_image_file'] = self._tmp_image_file
        return 0

    def pre_run(self):
        self._output.output("[%s|%s] %s" % (
                blue("ImageHandler"), darkred(self.spec_name),
                _("executing pre_run"),
            )
        )

        # run pre image script
        exec_script = self.metadata.get('pre_image_script')
        if exec_script:
            env = os.environ.copy()
            self._output.output("[%s|%s] %s: %s" % (
                    blue("ImageHandler"), darkred(self.spec_name),
                    _("spawning"), " ".join(exec_script),
                )
            )
            rc = molecule.utils.exec_cmd(exec_script, env = env)
            if rc != 0:
                self._output.output("[%s|%s] %s: %s" % (
                        blue("ImageHandler"), darkred(self.spec_name),
                        _("pre image hook failed"), rc,
                    )
                )
                return rc

        return 0

    def run(self):
        self._output.output("[%s|%s] %s" % (
                blue("ImageHandler"), darkred(self.spec_name),
                _("run hook called"),
            )
        )

        # run pre image script
        oexec_script = self.metadata.get('image_generator_script')
        if oexec_script:
            exec_script = oexec_script + [
                self._tmp_image_file, str(self.metadata['image_mb']),
                self.metadata['source_boot_directory'],
                self.metadata['source_chroot']]

            env = os.environ.copy()
            env['PATHS_TO_REMOVE'] = ";".join(
                self.metadata.get('paths_to_remove', []))
            env['PATHS_TO_EMPTY'] = ";".join(
                self.metadata.get('paths_to_empty', []))
            env['RELEASE_STRING'] = self.metadata['release_string']
            env['RELEASE_VERSION'] = self.metadata['release_version']
            env['RELEASE_DESC'] = self.metadata['release_desc']
            env['RELEASE_FILE'] = self.metadata['release_file']

            self._output.output("[%s|%s] %s: %s" % (
                    blue("ImageHandler"), darkred(self.spec_name),
                    _("spawning"), " ".join(exec_script),
                )
            )
            rc = molecule.utils.exec_cmd(exec_script, env = env)
            if rc != 0:
                self._output.output("[%s|%s] %s: %s" % (
                        blue("ImageHandler"), darkred(self.spec_name),
                        _("image hook failed"), rc,
                    )
                )
                return rc

        return 0

    def post_run(self):
        """ Nothing to run """
        return 0

    def kill(self, success = True):

        # kill tmp files
        if self._tmp_image_file_fd is not None:
            try:
                os.close(self._tmp_image_file_fd)
            except IOError as err:
                self._output.output("[%s|%s] %s: %s" % (
                        blue("ImageHandler"), darkred(self.spec_name),
                        _("unable to close temp fd"), err,
                    )
                )
            self._tmp_image_file_fd = None

        if not success:
            env = os.environ.copy()
            self._run_error_script(None, None, None, env = env)
            if self._tmp_image_file is not None:
                os.remove(self._tmp_image_file)
                self._tmp_image_file = None

        return 0


class FinalImageHandler(GenericExecutionStep, BuiltinHandlerMixin):

    MD5_EXT = ".md5"

    def __init__(self, *args, **kwargs):
        GenericExecutionStep.__init__(self, *args, **kwargs)
        self.dest_path = None
        self._tmp_image_file = None

    def setup(self):
        self._tmp_image_file = self.metadata['MmcImageHandler_image_file']

        image_name = self.metadata.get('image_name')
        self.dest_path = os.path.join(
            self.metadata['destination_image_directory'], image_name)

        dest_path_dir = os.path.dirname(self.dest_path)
        if (not os.path.lexists(dest_path_dir)) and \
            (not os.path.isdir(dest_path_dir)):
            os.makedirs(dest_path_dir, 0o755)

        return 0

    def pre_run(self):
        """ Nothing to do """
        return 0

    def run(self):
        self._output.output("[%s|%s] %s: %s %s" % (
                blue("FinalImageHandler"), darkred(self.spec_name),
                _("run hook called"), _("moving image file to destination"),
                self.dest_path,
            )
        )
        try:
            os.rename(self._tmp_image_file, self.dest_path)
        except OSError as err:
            if err.errno != errno.EXDEV:
                raise
            # cannot move atomically, fallback to shutil.move
            try:
                shutil.move(self._tmp_image_file, self.dest_path)
            except shutil.Error:
                raise

        self._output.output("[%s|%s] %s: %s" % (
                blue("FinalImageHandler"), darkred(self.spec_name),
                _("built image"), self.dest_path,
            )
        )
        if os.path.isfile(self.dest_path) and \
                os.access(self.dest_path, os.R_OK):
            self._output.output("[%s|%s] %s: %s" % (
                    blue("FinalImageHandler"), darkred(self.spec_name),
                    _("generating md5 for"), self.dest_path,
                )
            )
            digest = molecule.utils.md5sum(self.dest_path)
            md5file = self.dest_path + FinalImageHandler.MD5_EXT
            with open(md5file, "w") as f:
                f.write("%s  %s\n" % (digest,
                    os.path.basename(self.dest_path),))
                f.flush()

    def post_run(self):
        # run post tar script
        exec_script = self.metadata.get('post_image_script')
        if exec_script:
            env = os.environ.copy()
            env['IMAGE_PATH'] = self.dest_path
            env['IMAGE_CHECKSUM_PATH'] = self.dest_path + \
                FinalImageHandler.MD5_EXT
            self._output.output("[%s|%s] %s: %s" % (
                    blue("FinalImageHandler"), darkred(self.spec_name),
                    _("spawning"), " ".join(exec_script),
                )
            )
            rc = molecule.utils.exec_cmd(exec_script, env = env)
            if rc != 0:
                self._output.output("[%s|%s] %s: %s" % (
                        blue("FinalImageHandler"), darkred(self.spec_name),
                        _("post image hook failed"), rc,
                    )
                )
                return rc
        return 0

    def kill(self, success = True):
        if not success:
            if self._tmp_image_file is not None:
                if os.path.isfile(self._tmp_image_file):
                    os.remove(self._tmp_image_file)
        return 0

class ChrootToMmcImageSpec(GenericSpec):

    PLUGIN_API_VERSION = 0

    @staticmethod
    def execution_strategy():
        return "chroot_to_mmc"

    def vital_parameters(self):
        return [
            "release_string",
            "release_version",
            "release_desc",
            "release_file",
            "source_chroot",
            "source_boot_directory",
            "destination_image_directory",
            "image_generator_script",
            "image_mb",
        ]

    def parser_data_path(self):
        return {
            'execution_strategy': {
                'cb': self.ne_string,
                've': self.ve_string_stripper,
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
            'source_chroot': {
                'cb': self.valid_dir,
                've': self.ve_string_stripper,
            },
            'image_name': {
                'cb': self.ne_string,
                've': self.ve_string_stripper,
            },
            'image_mb': {
                'cb': self.valid_integer,
                've': self.ve_integer_converter,
            },
            'image_generator_script': {
                'cb': self.valid_exec_first_list_item,
                've': self.ve_command_splitter,
            },
            'error_script': {
                'cb': self.valid_exec_first_list_item,
                've': self.ve_command_splitter,
            },
            'destination_image_directory': {
                'cb': self.valid_dir,
                've': self.ve_string_stripper,
            },
            'source_boot_directory': {
                'cb': self.valid_dir,
                've': self.ve_string_stripper,
            },
            'pre_image_script': {
                'cb': self.valid_exec_first_list_item,
                've': self.ve_command_splitter,
            },
            'post_image_script': {
                'cb': self.valid_exec_first_list_item,
                've': self.ve_command_splitter,
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
        return [ImageHandler, FinalImageHandler]
