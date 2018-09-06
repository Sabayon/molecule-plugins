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

import molecule.utils

from .builtin_plugin import ChrootHandler as BuiltinChrootHandler
from .builtin_plugin import CdrootHandler as BuiltinCdrootHandler
from .builtin_plugin import IsoHandler as BuiltinIsoHandler
from .builtin_plugin import BuiltinHandlerMixin


class IsoUnpackHandler(GenericExecutionStep, BuiltinHandlerMixin):

    _iso_mounter = ["/bin/mount", "-o", "loop,ro", "-t", "iso9660"]
    _iso_umounter = ["/bin/umount"]

    _squash_mounter = ["/bin/mount", "-o", "loop,ro", "-t", "squashfs"]
    _squash_umounter = ["/bin/umount"]

    def __init__(self, *args, **kwargs):
        super(IsoUnpackHandler, self).__init__(*args, **kwargs)
        self._export_generic_info()

        self.tmp_mount = molecule.utils.mkdtemp()
        self.tmp_squash_mount = molecule.utils.mkdtemp()
        self.iso_mounted = False
        self.squash_mounted = False
        self.metadata['cdroot_path'] = None

        # if you want to subclass, override setup() and tweak these
        self.chroot_dir = None
        self.dest_root = None
        self.metadata['chroot_tmp_dir'] = None
        self.metadata['chroot_unpack_path'] = None
        self.metadata['cdroot_path'] = None

    def setup(self):

        # setup chroot unpack dir
        # can't use /tmp because it could be mounted with "special" options
        unpack_prefix = molecule.utils.mkdtemp(suffix="chroot")
        self.metadata['chroot_tmp_dir'] = unpack_prefix
        self.metadata['chroot_unpack_path'] = os.path.join(
            unpack_prefix,
            "root"
        )

        # setup upcoming new chroot path
        self.dest_root = os.path.join(unpack_prefix, "cdroot")
        self.chroot_dir = self.metadata['chroot_unpack_path']
        self.metadata['cdroot_path'] = self.dest_root

    def pre_run(self):
        self._output.output("[%s|%s] %s" % (
                blue("IsoUnpackHandler"), darkred(self.spec_name),
                _("executing pre_run"),
            )
        )

        # setup paths
        self.iso_image = self.metadata['source_iso']

        # mount
        mounter = self.metadata.get('iso_mounter', self._iso_mounter)
        mount_args = mounter + [self.iso_image, self.tmp_mount]
        self._output.output("[%s|%s] %s: %s" % (
                blue("IsoUnpackHandler"), darkred(self.spec_name),
                _("spawning"), " ".join(mount_args),
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
                                    self._squash_mounter)

        output_file = BuiltinCdrootHandler.chroot_compressor_output_file
        if "chroot_compressor_output_file" in self.metadata:
            output_file = self.metadata.get('chroot_compressor_output_file')

        squash_file = os.path.join(self.tmp_mount, output_file)
        mount_args = mounter + [squash_file, self.tmp_squash_mount]
        self._output.output("[%s|%s] %s: %s" % (
                blue("IsoUnpackHandler"), darkred(self.spec_name),
                _("spawning"), " ".join(mount_args),
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
            if self.metadata['chroot_tmp_dir'] is not None:
                shutil.rmtree(self.metadata['chroot_tmp_dir'], True)

        # create chroot path
        try:
            rc = molecule.utils.copy_dir(self.tmp_squash_mount,
                                         self.metadata['chroot_unpack_path'])
        except Exception:
            dorm()
            raise

        if rc != 0:
            dorm()

        return rc

    def post_run(self):
        self._output.output("[%s|%s] %s" % (
                blue("IsoUnpackHandler"), darkred(self.spec_name),
                _("executing post_run"),
            )
        )
        return 0

    def kill(self, success=True):
        self._output.output("[%s|%s] %s" % (
                blue("IsoUnpackHandler"), darkred(self.spec_name),
                _("executing kill"),
            )
        )

        if not success:
            self._run_error_script(None, self.chroot_dir, self.dest_root)

        rc = 0
        if self.squash_mounted:
            umounter = self.metadata.get('squash_umounter',
                                         self._squash_umounter)
            args = umounter + [self.tmp_squash_mount]
            rc = molecule.utils.exec_cmd(args)

        if rc == 0:
            try:
                os.rmdir(self.tmp_squash_mount)
            except OSError:
                self._output.output(
                    "[%s|%s] %s: %s" % (
                        blue("IsoUnpackHandler"), darkred(self.spec_name),
                        _("unable to remove temp. dir"), self.tmp_squash_mount,
                    )
                )

        rc = 0
        if self.iso_mounted:
            umounter = self.metadata.get('iso_umounter',
                                         self._iso_umounter)
            args = umounter + [self.tmp_mount]
            rc = molecule.utils.exec_cmd(args)

        if rc == 0:
            try:
                os.rmdir(self.tmp_mount)
            except OSError:
                # if not empty, skip
                self._output.output(
                    "[%s|%s] %s: %s" % (
                        blue("IsoUnpackHandler"), darkred(self.spec_name),
                        _("unable to remove temp. dir"), self.tmp_mount,
                    )
                )

        if not success:
            tmp_dir = self.metadata['chroot_tmp_dir']
            if tmp_dir is not None:
                try:
                    shutil.rmtree(tmp_dir, True)
                except (shutil.Error, OSError,):
                    self._output.output("[%s|%s] %s: %s" % (
                        blue("IsoUnpackHandler"), darkred(self.spec_name),
                        _("unable to remove temp. dir"), tmp_dir,
                    )
                                        )

        return 0


class ChrootHandler(BuiltinChrootHandler):

    _pkgs_adder = ["/usr/bin/equo", "install"]
    _pkgs_remover = ["/usr/bin/equo", "remove"]
    _pkgs_updater = ["/usr/bin/equo", "update"]

    def setup(self):
        # to make superclass working
        self.source_dir = self.metadata['chroot_unpack_path']
        self.dest_dir = self.source_dir
        return 0

    def kill(self, success=True):
        BuiltinChrootHandler.kill(self, success=success)
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
                update_cmd = self.metadata.get(
                    'repositories_update_cmd',
                    self._pkgs_updater)
                try:
                    rc = molecule.utils.exec_chroot_cmd(
                        update_cmd,
                        self.source_dir,
                        pre_chroot=self.metadata.get('prechroot', [])
                    )
                except Exception:
                    molecule.utils.kill_chroot_pids(self.source_dir,
                                                    sleep=True)
                    raise
                if rc != 0:
                    molecule.utils.kill_chroot_pids(self.source_dir,
                                                    sleep=True)
                    return rc

        rc = BuiltinChrootHandler.run(self)
        if rc != 0:
            return rc

        self._output.output(
            "[%s|%s] %s" % (
                blue("ChrootHandler"), darkred(self.spec_name),
                _("hooks running"),
            )
        )

        packages_to_add = self.metadata.get('packages_to_add', [])
        if packages_to_add:

            add_cmd = self.metadata.get(
                'custom_packages_add_cmd',
                self._pkgs_adder)
            args = add_cmd + packages_to_add
            try:
                rc = molecule.utils.exec_chroot_cmd(
                    args,
                    self.source_dir,
                    pre_chroot=self.metadata.get('prechroot', [])
                )
            except Exception:
                molecule.utils.kill_chroot_pids(self.source_dir,
                                                sleep=True)
                raise
            if rc != 0:
                molecule.utils.kill_chroot_pids(self.source_dir,
                                                sleep=True)
                return rc

        packages_to_remove = self.metadata.get('packages_to_remove', [])
        if packages_to_remove:
            rm_cmd = self.metadata.get(
                'custom_packages_remove_cmd',
                self._pkgs_remover)
            args = rm_cmd + packages_to_remove
            try:
                rc = molecule.utils.exec_chroot_cmd(
                    args,
                    self.source_dir,
                    pre_chroot=self.metadata.get('prechroot', [])
                )
            except Exception:
                molecule.utils.kill_chroot_pids(self.source_dir,
                                                sleep=True)
                raise
            if rc != 0:
                molecule.utils.kill_chroot_pids(self.source_dir,
                                                sleep=True)
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
        return 0

    def kill(self, success=True):
        BuiltinCdrootHandler.kill(self, success=success)
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
        dest_iso_filename = self.metadata.get(
            'destination_iso_image_name',
            "remaster_" + os.path.basename(self.metadata['source_iso'])
        )
        self.dest_iso = os.path.join(self.metadata['destination_iso_directory'],
                                     dest_iso_filename)
        self.iso_title = self.metadata.get('iso_title', 'Molecule remaster')
        self.source_chroot = self.metadata['chroot_unpack_path']
        self.chroot_dir = self.source_chroot
        return 0

    def kill(self, success=True):
        BuiltinIsoHandler.kill(self, success=success)
        try:
            shutil.rmtree(self.metadata['chroot_tmp_dir'], True)
        except (shutil.Error, OSError,):
            pass
        return 0


class RemasterSpec(GenericSpec):

    PLUGIN_API_VERSION = 1

    @staticmethod
    def execution_strategy():
        return "iso_remaster"

    def vital_parameters(self):
        return [
            "source_iso",
            "destination_iso_directory",
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
            'iso_title': {
                'verifier': lambda x: len(x) != 0,
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
            'extra_mksquashfs_parameters': {
                'verifier': lambda x: True,
                'parser': self._command_splitter,
            },
            'extra_mkisofs_parameters': {
                'verifier': lambda x: True,
                'parser': self._command_splitter,
            },
            'pre_iso_script': {
                'verifier': self._verify_executable_arguments,
                'parser': self._command_splitter,
            },
            'post_iso_script': {
                'verifier': self._verify_executable_arguments,
                'parser': self._command_splitter,
            },
            'destination_iso_directory': {
                'verifier': os.path.isdir,
                'parser': lambda x: x.strip(),
            },
            'destination_iso_image_name': {
                'verifier': lambda x: len(x) != 0,
                'parser': lambda x: x.strip(),
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
            'merge_livecd_root': {
                'verifier': os.path.isdir,
                'parser': lambda x: x.strip(),
            },
            'custom_packages_remove_cmd': {
                'verifier': lambda x: len(x) != 0,
                'parser': self._command_splitter,
            },
            'custom_packages_add_cmd': {
                'verifier': lambda x: len(x) != 0,
                'parser': self._command_splitter,
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
        return [IsoUnpackHandler, ChrootHandler, CdrootHandler, IsoHandler]
