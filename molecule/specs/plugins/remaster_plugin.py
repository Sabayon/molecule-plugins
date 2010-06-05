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
import tempfile
import shutil

from molecule.i18n import _
from molecule.output import red, brown, blue, green, purple, darkgreen, \
    darkred, bold, darkblue, readtext
from molecule.specs.skel import GenericExecutionStep, GenericSpec
from molecule.specs.plugins.builtin_plugin import ChrootHandler as \
    BuiltinChrootHandler
from molecule.specs.plugins.builtin_plugin import CdrootHandler as \
    BuiltinCdrootHandler
from molecule.specs.plugins.builtin_plugin import IsoHandler as \
    BuiltinIsoHandler
from molecule.specs.plugins.builtin_plugin import BuiltinHandlerMixin
import molecule.utils

class IsoUnpackHandler(GenericExecutionStep, BuiltinHandlerMixin):

    def __init__(self, *args, **kwargs):
        GenericExecutionStep.__init__(self, *args, **kwargs)
        self.tmp_mount = tempfile.mkdtemp(prefix = "molecule", dir = "/var/tmp")
        self.tmp_squash_mount = tempfile.mkdtemp(prefix = "molecule",
            dir = "/var/tmp")
        self.iso_mounted = False
        self.squash_mounted = False

        # setup chroot unpack dir
        # can't use /tmp because it could be mounted with "special" options
        unpack_prefix = tempfile.mkdtemp(prefix = "molecule", dir = "/var/tmp",
            suffix = "chroot")
        self.metadata['chroot_tmp_dir'] = unpack_prefix
        self.metadata['chroot_unpack_path'] = os.path.join(unpack_prefix,
            "root")

        # setup upcoming new chroot path
        self.dest_root = os.path.join(unpack_prefix, "cdroot")
        self.chroot_dir = self.metadata['chroot_unpack_path']
        self.metadata['cdroot_path'] = self.dest_root

    def pre_run(self):
        self._output.output("[%s|%s] %s" % (
                blue("IsoUnpackHandler"),darkred(self.spec_name),
                _("executing pre_run"),
            )
        )

        # setup paths
        self.iso_image = self.metadata['source_iso']

        # mount
        mounter = self.metadata.get('iso_mounter', self._config['iso_mounter'])
        mount_args = mounter + [self.iso_image, self.tmp_mount]
        self._output.output("[%s|%s] %s: %s" % (
                blue("IsoUnpackHandler"), darkred(self.spec_name),
                _("spawning"), mount_args,
            )
        )
        rc = molecule.utils.exec_cmd(mount_args)
        if rc != 0:
            self._output.output("[%s|%s] %s: %s" % (
                    blue("IsoUnpackHandler"), darkred(self.spec_name),
                    _("iso mount failed"), rc,
                )
            )
            return rc

        # copy iso content over, including squashfs yeah, it will be
        # replaced later on
        # this is mandatory and used to make iso recreation easier
        rc = molecule.utils.copy_dir(self.tmp_mount, self.dest_root)
        if rc != 0:
            return rc

        self.iso_mounted = True

        # mount squash
        mounter = self.metadata.get('squash_mounter',
            self._config['squash_mounter'])
        squash_file = os.path.join(self.tmp_mount,
            self._config['chroot_compressor_output_file'])
        mount_args = mounter + [squash_file, self.tmp_squash_mount]
        self._output.output("[%s|%s] %s: %s" % (
                blue("IsoUnpackHandler"), darkred(self.spec_name),
                _("spawning"), mount_args,
            )
        )
        rc = molecule.utils.exec_cmd(mount_args)
        if rc != 0:
            self._output.output("[%s|%s] %s: %s" % (
                    blue("IsoUnpackHandler"), darkred(self.spec_name),
                    _("squash mount failed"), rc,
                )
            )
            return rc
        self.squash_mounted = True

        return 0

    def run(self):

        self._output.output("[%s|%s] %s: %s => %s" % (
                blue("IsoUnpackHandler"), darkred(self.spec_name),
                _("iso unpacker running"), self.tmp_squash_mount,
                self.metadata['chroot_unpack_path'],
            )
        )

        def dorm():
            shutil.rmtree(self.metadata['chroot_tmp_dir'], True)

        # create chroot path
        try:
            rc = molecule.utils.copy_dir(self.tmp_squash_mount,
                self.metadata['chroot_unpack_path'])
        except:
            dorm()
            raise

        if rc != 0:
            dorm()

        return rc

    def post_run(self):
        self._output.output("[%s|%s] %s" % (
                blue("IsoUnpackHandler"),darkred(self.spec_name),
                _("executing post_run"),
            )
        )
        return 0

    def kill(self, success = True):
        self._output.output("[%s|%s] %s" % (
                blue("IsoUnpackHandler"),darkred(self.spec_name),
                _("executing kill"),
            )
        )

        if not success:
            self._run_error_script(None, self.chroot_dir, self.dest_root)

        rc = 0
        if self.squash_mounted:
            umounter = self.metadata.get('squash_umounter',
                self._config['squash_umounter'])
            args = umounter + [self.tmp_squash_mount]
            rc = molecule.utils.exec_cmd(args)

        if rc == 0:
            try:
                os.rmdir(self.tmp_squash_mount)
            except OSError:
                pass

        rc = 0
        if self.iso_mounted:
            umounter = self.metadata.get('iso_umounter',
                self._config['iso_umounter'])
            args = umounter + [self.tmp_mount]
            rc = molecule.utils.exec_cmd(args)

        if rc == 0:
            try:
                os.rmdir(self.tmp_mount)
            except OSError:
                # if not empty, skip
                pass

        if not success:
            try:
                shutil.rmtree(self.metadata['chroot_tmp_dir'], True)
            except (shutil.Error, OSError,):
                pass

        return 0


class ChrootHandler(BuiltinChrootHandler):

    def setup(self):
        # to make superclass working
        self.source_dir = self.metadata['chroot_unpack_path']
        self.dest_dir = self.source_dir

    def kill(self, success = True):
        BuiltinChrootHandler.kill(self, success = success)
        if not success:
            try:
                shutil.rmtree(self.metadata['chroot_tmp_dir'], True)
            except (shutil.Error, OSError,):
                pass
        return 0

    def run(self):

        packages_to_add = self.metadata.get('packages_to_add', [])
        if packages_to_add:

            # update repos first?
            do_update = self.metadata.get('execute_repositories_update', 'no')
            if do_update == 'yes':
                update_cmd = self.metadata.get('repositories_update_cmd',
                    self._config['pkgs_updater'])
                rc = molecule.utils.exec_chroot_cmd(update_cmd,
                    self.source_dir,
                    self.metadata.get('prechroot',[]))
                if rc != 0:
                    return rc

        rc = BuiltinChrootHandler.run(self)
        if rc != 0:
            return rc

        self._output.output("[%s|%s] %s" % (
                blue("ChrootHandler"),darkred(self.spec_name),
                _("hooks running"),
            )
        )

        packages_to_add = self.metadata.get('packages_to_add', [])
        if packages_to_add:

            add_cmd = self.metadata.get('custom_packages_add_cmd',
                self._config['pkgs_adder'])
            args = add_cmd + packages_to_add
            rc = molecule.utils.exec_chroot_cmd(args,
                self.source_dir,
                self.metadata.get('prechroot',[]))
            if rc != 0:
                return rc

        packages_to_remove = self.metadata.get('packages_to_remove', [])
        if packages_to_remove:
            rm_cmd = self.metadata.get('custom_packages_remove_cmd',
                self._config['pkgs_remover'])
            args = rm_cmd + packages_to_remove
            rc = molecule.utils.exec_chroot_cmd(args,
                self.source_dir,
                self.metadata.get('prechroot',[]))
            if rc != 0:
                return rc

        # run inner chroot script after pkgs handling
        exec_script = self.metadata.get('inner_chroot_script_after')
        if exec_script:
            if os.path.isfile(exec_script[0]) and \
                os.access(exec_script[0], os.R_OK):
                rc = self._exec_inner_script(exec_script, self.source_dir)
                if rc != 0:
                    return rc

        return 0


class CdrootHandler(BuiltinCdrootHandler):

    def setup(self):
        self.dest_root = self.metadata['cdroot_path']
        self.source_chroot = self.metadata['chroot_unpack_path']

    def kill(self, success = True):
        BuiltinCdrootHandler.kill(self, success = success)
        if not success:
            try:
                shutil.rmtree(self.metadata['chroot_tmp_dir'], True)
            except (shutil.Error, OSError,):
                pass
        return 0

class IsoHandler(BuiltinIsoHandler):

    def setup(self):
        # cdroot dir
        self.source_path = self.metadata['cdroot_path']
        dest_iso_filename = self.metadata.get('destination_iso_image_name',
            "remaster_" + os.path.basename(self.metadata['source_iso']))
        self.dest_iso = os.path.join(self.metadata['destination_iso_directory'],
            dest_iso_filename)
        self.iso_title = self.metadata.get('iso_title', 'Molecule remaster')
        self.source_chroot = self.metadata['chroot_unpack_path']
        self.chroot_dir = self.source_chroot

    def kill(self, success = True):
        BuiltinIsoHandler.kill(self, success = success)
        try:
            shutil.rmtree(self.metadata['chroot_tmp_dir'], True)
        except (shutil.Error, OSError,):
            pass
        return 0


class RemasterSpec(GenericSpec):

    PLUGIN_API_VERSION = 0

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
            'iso_title': {
                'cb': self.ne_string,
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
            'extra_mkisofs_parameters': {
                'cb': self.always_valid,
                've': self.ve_string_splitter,
            },
            'pre_iso_script': {
                'cb': self.valid_exec_first_list_item,
                've': self.ve_string_splitter,
            },
            'post_iso_script': {
                'cb': self.valid_exec_first_list_item,
                've': self.ve_string_splitter,
            },
            'destination_iso_directory': {
                'cb': self.valid_dir,
                've': self.ve_string_stripper,
            },
            'destination_iso_image_name': {
                'cb': self.valid_ascii,
                've': self.ve_string_stripper,
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
            'merge_livecd_root': {
                'cb': self.valid_dir,
                've': self.ve_string_stripper,
            },
            'custom_packages_remove_cmd': {
                'cb': self.ne_list,
                've': self.ve_string_splitter,
            },
            'custom_packages_add_cmd': {
                'cb': self.ne_list,
                've': self.ve_string_splitter,
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
        return [IsoUnpackHandler, ChrootHandler, CdrootHandler, IsoHandler]
