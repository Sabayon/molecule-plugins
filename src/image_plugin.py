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

import array
import os
import shutil
import tempfile
import gc
import errno

from molecule.i18n import _
from molecule.output import blue, darkred
from molecule.specs.skel import GenericExecutionStep, GenericSpec

import molecule.utils

from .builtin_plugin import BuiltinHandlerMixin
from .remaster_plugin import IsoUnpackHandler as RemasterIsoUnpackHandler, \
    ChrootHandler as RemasterChrootHandler


class ImageHandler(GenericExecutionStep, BuiltinHandlerMixin):

    LOSETUP_EXEC = "/sbin/losetup"
    MB_IN_BYTES = 1024000
    DEFAULT_IMAGE_FORMATTER = ["/sbin/mkfs.ext3"]
    DEFAULT_IMAGE_MOUNTER = ["/bin/mount", "-o", "loop,rw"]
    DEFAULT_IMAGE_UMOUNTER = ["/bin/umount"]

    def __init__(self, *args, **kwargs):
        GenericExecutionStep.__init__(self, *args, **kwargs)

        # init variables
        self.loop_device = None
        self._tmp_loop_device_fd = None
        self.tmp_loop_device_file = None
        self.image_mb = 0
        self.randomize = False
        self.image_mounted = False
        self.tmp_image_mount = None

    def setup(self):

        self.image_mb = self.metadata['image_mb']
        if self.metadata.get('image_randomize') == "yes":
            self.randomize = True

        sts, loop_device = molecule.utils.exec_cmd_get_status_output(
            [ImageHandler.LOSETUP_EXEC, "-f"])
        if sts != 0:
            # ouch
            self._output.output("[%s|%s] %s: %s" % (
                    blue("ImageHandler"), darkred(self.spec_name),
                    _("setup hook failed"), _("cannot setup loop device"),
                )
            )
            return sts
        try:
            self._tmp_loop_device_fd, self.tmp_loop_device_file = \
                tempfile.mkstemp(prefix = "molecule", dir = self._config['tmp_dir'])
        except (OSError, IOError,) as err:
            self._output.output("[%s|%s] %s: %s" % (
                    blue("ImageHandler"), darkred(self.spec_name),
                    _("setup hook failed"), _("cannot create temporary file"),
                )
            )
            return 1

        # bind loop device
        args = [ImageHandler.LOSETUP_EXEC, loop_device,
            self.tmp_loop_device_file]
        rc = molecule.utils.exec_cmd(args)
        if rc != 0:
            self._output.output("[%s|%s] %s: %s" % (
                    blue("ImageHandler"), darkred(self.spec_name),
                    _("setup hook failed"), _("cannot bind loop device"),
                )
            )
            return 1
        self.loop_device = loop_device

        self.tmp_image_mount = molecule.utils.mkdtemp()

        # setup metadata for next phases
        self.metadata['ImageHandler_loop_device_file'] = \
            self.tmp_loop_device_file
        self.metadata['ImageHandler_tmp_image_mount'] = self.tmp_image_mount
        self.metadata['ImageHandler_loop_device'] = self.loop_device
        self.metadata['ImageHandler_kill_loop_device'] = self._kill_loop_device

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
            env['TMP_IMAGE_PATH'] = self.tmp_loop_device_file
            env['LOOP_DEVICE'] = self.loop_device
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

    def _fill_image_file(self):
        """
        Fill image file (using _tmp_loop_device_fd) with either zeroes or
        random data of image_mb size.

        @raises IOError: if space is not enough
        @raises OSError: well, sorry
        """
        if self.randomize:
            self._output.output("[%s|%s] %s => %s" % (
                    blue("ImageHandler"), darkred(self.spec_name),
                    _("generating random base image file"),
                    self.tmp_loop_device_file,
                )
            )
        else:
            self._output.output("[%s|%s] %s => %s" % (
                    blue("ImageHandler"), darkred(self.spec_name),
                    _("generating zeroed base image file"),
                    self.tmp_loop_device_file,
                )
            )

        image_mb = self.image_mb
        loop_f = os.fdopen(self._tmp_loop_device_fd, "wb")
        self._tmp_loop_device_fd = None
        arr = None
        mb_bytes = ImageHandler.MB_IN_BYTES
        while image_mb > 0:
            image_mb -= 1
            if self.randomize:
                arr = array.array('c', os.urandom(mb_bytes))
            else:
                arr = array.array('c', chr(0)*mb_bytes)
            arr.tofile(loop_f)

        del arr
        gc.collect()
        # file self._tmp_loop_device_fd is closed here.
        # no more writes needed
        loop_f.flush()
        loop_f.close()

        # last but not least, tell the loop device that the file size changed
        args = [ImageHandler.LOSETUP_EXEC, "-c", self.loop_device]
        self._output.output("[%s|%s] %s: %s" % (
                blue("ImageHandler"), darkred(self.spec_name),
                _("spawning"), " ".join(args),
            )
        )
        rc = molecule.utils.exec_cmd(args)
        if rc != 0:
            self._output.output("[%s|%s] %s: %s" % (
                    blue("ImageHandler"), darkred(self.spec_name),
                    _("image file resize failed"), rc,
                )
            )
        return rc

    def run(self):
        self._output.output("[%s|%s] %s" % (
                blue("ImageHandler"), darkred(self.spec_name),
                _("run hook called"),
            )
        )

        # fill image file
        try:
            rc = self._fill_image_file()
            if rc != 0:
                return rc
        except (IOError, OSError) as err:
            self._output.output("[%s|%s] %s: %s" % (
                    blue("ImageHandler"), darkred(self.spec_name),
                    _("image file generation failed"), err,
                )
            )
            return 1

        # format image file
        image_formatter = self.metadata.get('image_formatter',
            ImageHandler.DEFAULT_IMAGE_FORMATTER)
        formatter_args = image_formatter + [self.loop_device]
        self._output.output("[%s|%s] %s: %s" % (
                blue("ImageHandler"), darkred(self.spec_name),
                _("spawning"), " ".join(formatter_args),
            )
        )
        rc = molecule.utils.exec_cmd(formatter_args)
        if rc != 0:
            self._output.output("[%s|%s] %s: %s" % (
                    blue("ImageHandler"), darkred(self.spec_name),
                    _("image formatter hook failed"), rc,
                )
            )
            return rc

        # mount image file
        mounter = self.metadata.get('image_mounter',
            ImageHandler.DEFAULT_IMAGE_MOUNTER)
        mount_args = mounter + [self.loop_device, self.tmp_image_mount]
        self._output.output("[%s|%s] %s: %s" % (
                blue("ImageHandler"), darkred(self.spec_name),
                _("spawning"), " ".join(mount_args),
            )
        )
        rc = molecule.utils.exec_cmd(mount_args)
        if rc != 0:
            self._output.output("[%s|%s] %s: %s" % (
                    blue("ImageHandler"), darkred(self.spec_name),
                    _("image mount failed"), rc,
                )
            )
            return rc
        self.image_mounted = True

        return 0

    def post_run(self):
        """ Nothing to do """
        return 0

    def _kill_loop_device(self, preserve_loop_device_file = False):

        kill_rc = 0
        if self.image_mounted:
            umounter = self.metadata.get('image_umounter',
                ImageHandler.DEFAULT_IMAGE_UMOUNTER)
            args = umounter + [self.tmp_image_mount]
            rc = molecule.utils.exec_cmd(args)
            if rc != 0:
                self._output.output("[%s|%s] %s: %s" % (
                        blue("ImageHandler"), darkred(self.spec_name),
                        _("unable to umount loop device"), self.loop_device,
                    )
                )
                kill_rc = rc
            else:
                self.image_mounted = False

        if self.tmp_image_mount is not None:
            try:
                os.rmdir(self.tmp_image_mount)
            except OSError:
                pass

        # kill loop device
        if self.loop_device is not None:
            rc = molecule.utils.exec_cmd([ImageHandler.LOSETUP_EXEC, "-d",
                self.loop_device])
            if rc != 0:
                self._output.output("[%s|%s] %s: %s" % (
                        blue("ImageHandler"), darkred(self.spec_name),
                        _("unable to kill loop device"), self.loop_device,
                    )
                )
                kill_rc = rc
            else:
                self.loop_device = None

        if (self.tmp_loop_device_file is not None) and \
            (not preserve_loop_device_file):
            try:
                os.remove(self.tmp_loop_device_file)
                self.tmp_loop_device_file = None
            except OSError as err:
                self._output.output("[%s|%s] %s: %s" % (
                        blue("ImageHandler"), darkred(self.spec_name),
                        _("unable to remove temp. loop device file"),
                        err,
                    )
                )
                kill_rc = 1

        return kill_rc

    def kill(self, success = True):

        # kill tmp files
        if self._tmp_loop_device_fd is not None:
            try:
                os.close(self._tmp_loop_device_fd)
            except IOError as err:
                self._output.output("[%s|%s] %s: %s" % (
                        blue("ImageHandler"), darkred(self.spec_name),
                        _("unable to close temp fd"), err,
                    )
                )
            self._tmp_loop_device_fd = None

        if not success:
            env = os.environ.copy()
            env["LOOP_DEVICE"] = self.loop_device
            self._run_error_script(None, None, None, env = env)
            self._kill_loop_device()

        return 0


class ImageIsoUnpackHandler(RemasterIsoUnpackHandler):

    def setup(self):

        unpack_prefix = molecule.utils.mkdtemp(suffix = "chroot")

        self.metadata['chroot_tmp_dir'] = unpack_prefix
        self.metadata['chroot_unpack_path'] = \
            self.metadata['ImageHandler_tmp_image_mount']
        self.dest_root = os.path.join(unpack_prefix, "cdroot")

        # setup upcoming new chroot path
        self.chroot_dir = self.metadata['chroot_unpack_path']
        # explicitly set this to None
        self.metadata['cdroot_path'] = None

        return 0

    def run(self):

        self._output.output("[%s|%s] %s: %s => %s" % (
                blue("ImageIsoUnpackHandler"), darkred(self.spec_name),
                _("iso unpacker running"), self.tmp_squash_mount,
                self.metadata['chroot_unpack_path'],
            )
        )

        def dorm():
            if self.metadata['chroot_tmp_dir'] is not None:
                shutil.rmtree(self.metadata['chroot_tmp_dir'], True)

        # copy data into chroot, in our case, destination dir already
        # exists, so copy_dir() is a bit tricky
        try:
            rc = molecule.utils.copy_dir_existing_dest(self.tmp_squash_mount,
                self.metadata['chroot_unpack_path'])
        except:
            dorm()
            raise

        if rc != 0:
            dorm()

        return rc

    def kill(self, success = True):
        # ImageHandler sets this
        if not success:
            self.metadata['ImageHandler_kill_loop_device']()
        RemasterIsoUnpackHandler.kill(self, success = success)

        # we don't need the whole dir
        tmp_dir = self.metadata['chroot_tmp_dir']
        if os.path.isdir(tmp_dir):
            try:
                shutil.rmtree(tmp_dir, True)
            except (shutil.Error, OSError,):
                self._output.output("[%s|%s] %s: %s" % (
                        blue("ImageIsoUnpackHandler"), darkred(self.spec_name),
                        _("unable to remove temp. dir"), tmp_dir,
                    )
                )

        return 0


class ImageChrootHandler(RemasterChrootHandler):

    def setup(self):
        # to make superclass working
        self.source_dir = self.metadata['chroot_unpack_path']
        self.dest_dir = self.source_dir
        return 0

    def kill(self, success = True):
        self._output.output("[%s|%s] %s" % (
                blue("ImageChrootHandler"),
                darkred(self.spec_name), _("executing kill"),
            )
        )
        if not success:
            env = os.environ.copy()
            loop_device = self.metadata.get('ImageHandler_loop_device')
            if loop_device is not None:
                env["LOOP_DEVICE"] = loop_device
            self._run_error_script(self.source_dir, self.dest_dir, None,
                env = env)
            self.metadata['ImageHandler_kill_loop_device']()
        return 0


class FinalImageHandler(GenericExecutionStep, BuiltinHandlerMixin):

    MD5_EXT = ".md5"
    IMAGE_EXT = ".img"

    def __init__(self, *args, **kwargs):
        GenericExecutionStep.__init__(self, *args, **kwargs)
        self._loop_device_killed = False
        self._loop_device_file_removed = False

    def setup(self):
        # ImageHandler sets this
        self.tmp_loop_device_file = \
            self.metadata['ImageHandler_loop_device_file']
        # umount all, but don't remove our loop device file
        kill_rc = self.metadata['ImageHandler_kill_loop_device'](
            preserve_loop_device_file = True)
        if kill_rc:
            self._loop_device_killed = True

        image_name = self.metadata.get('image_name',
            os.path.basename(self.metadata['source_iso']) + \
                FinalImageHandler.IMAGE_EXT)
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
            os.rename(self.tmp_loop_device_file, self.dest_path)
        except OSError as err:
            if err.errno != errno.EXDEV:
                raise
            # cannot move atomically, fallback to shutil.move
            try:
                shutil.move(self.tmp_loop_device_file, self.dest_path)
            except shutil.Error:
                raise
        self._loop_device_file_removed = True

        self._output.output("[%s|%s] %s: %s" % (
                blue("FinalImageHandler"), darkred(self.spec_name),
                _("built image"), self.dest_path,
            )
        )
        if os.path.isfile(self.dest_path) and os.access(self.dest_path, os.R_OK):
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
            if not (self._loop_device_file_removed and \
                self._loop_device_killed):
                self.metadata['ImageHandler_kill_loop_device']()
        """ Nothing to do """
        return 0

class IsoToImageSpec(GenericSpec):

    PLUGIN_API_VERSION = 0

    @staticmethod
    def execution_strategy():
        return "iso_to_image"

    def vital_parameters(self):
        return [
            "source_iso",
            "destination_image_directory",
            "image_mb",
        ]

    def parser_data_path(self):
        return {
            'execution_strategy': {
                'cb': self.ne_string,
                've': self.ve_string_stripper,
            },
            'prechroot': {
                'cb': self.valid_exec_first_list_item,
                've': self.ve_command_splitter,
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
            'image_name': {
                'cb': self.ne_string,
                've': self.ve_string_stripper,
            },
            'image_formatter': {
                'cb': self.ne_list,
                've': self.ve_command_splitter,
            },
            'image_mounter': {
                'cb': self.ne_list,
                've': self.ve_command_splitter,
            },
            'image_umounter': {
                'cb': self.ne_list,
                've': self.ve_command_splitter,
            },
            'image_mb': {
                'cb': self.valid_integer,
                've': self.ve_integer_converter,
            },
            'image_randomize': {
                'cb': self.valid_ascii,
                've': self.ve_string_stripper,
            },
            'error_script': {
                'cb': self.valid_exec_first_list_item,
                've': self.ve_command_splitter,
            },
            'outer_chroot_script': {
                'cb': self.valid_exec_first_list_item,
                've': self.ve_command_splitter,
            },
            'inner_chroot_script': {
                'cb': self.valid_path_string_first_list_item,
                've': self.ve_command_splitter,
            },
            'inner_chroot_script_after': {
                'cb': self.valid_path_string_first_list_item,
                've': self.ve_command_splitter,
            },
            'outer_chroot_script_after': {
                'cb': self.valid_exec_first_list_item,
                've': self.ve_command_splitter,
            },
            'destination_image_directory': {
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
            'iso_mounter': {
                'cb': self.ne_list,
                've': self.ve_command_splitter,
            },
            'iso_umounter': {
                'cb': self.ne_list,
                've': self.ve_command_splitter,
            },
            'squash_mounter': {
                'cb': self.ne_list,
                've': self.ve_command_splitter,
            },
            'squash_umounter': {
                'cb': self.ne_list,
                've': self.ve_command_splitter,
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
                've': self.ve_command_splitter,
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
        return [ImageHandler, ImageIsoUnpackHandler, ImageChrootHandler,
            FinalImageHandler]
