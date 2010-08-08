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
import tempfile
from molecule.compat import get_stringtype
from molecule.i18n import _
from molecule.output import red, brown, blue, green, purple, darkgreen, \
    darkred, bold, darkblue, readtext
import molecule.utils
from molecule.specs.skel import GenericExecutionStep, GenericSpec

class BuiltinHandlerMixin:
    """
    This class contains code in common between built-in handler classes.
    """
    def _run_error_script(self, source_chroot_dir, chroot_dir, cdroot_dir):
        error_script = self.metadata.get('error_script')
        if error_script:
            if source_chroot_dir:
                os.environ['SOURCE_CHROOT_DIR'] = source_chroot_dir
            if chroot_dir:
                os.environ['CHROOT_DIR'] = chroot_dir
            if cdroot_dir:
                os.environ['CDROOT_DIR'] = cdroot_dir
            self._output.output("[%s|%s] %s: %s" % (
                    blue("BuiltinHandler"), darkred(self.spec_name),
                    _("spawning"), error_script,
                )
            )
            molecule.utils.exec_cmd(error_script)
            for env_key in ("SOURCE_CHROOT_DIR", "CHROOT_DIR", "CDROOT_DIR",):
                try:
                    del os.environ[env_key]
                except KeyError:
                    continue

    def _exec_inner_script(self, exec_script, dest_chroot):

        source_exec = exec_script[0]
        with open(source_exec, "rb") as f_src:
            tmp_fd, tmp_exec = tempfile.mkstemp(dir = dest_chroot,
                prefix = "molecule_inner")
            f_dst = os.fdopen(tmp_fd, "wb")
            try:
                shutil.copyfileobj(f_src, f_dst)
            finally:
                f_dst.flush()
                f_dst.close()
            shutil.copystat(source_exec, tmp_exec)
            os.chmod(tmp_exec, 0o744)

        dest_exec = os.path.basename(tmp_exec)
        if not dest_exec.startswith("/"):
            dest_exec = "/%s" % (dest_exec,)

        rc = molecule.utils.exec_chroot_cmd([dest_exec] + exec_script[1:],
            dest_chroot, pre_chroot = self.metadata.get('prechroot', []))
        os.remove(tmp_exec)

        if rc != 0:
            self._output.output("[%s|%s] %s: %s" % (
                    blue("BuiltinHandler"), darkred(self.spec_name),
                    _("inner chroot hook failed"), rc,
                )
            )
        return rc

class MirrorHandler(GenericExecutionStep, BuiltinHandlerMixin):

    def __init__(self, *args, **kwargs):
        GenericExecutionStep.__init__(self, *args, **kwargs)

    def setup(self):
        # creating destination chroot dir
        self.source_dir = self.metadata['source_chroot']
        self.dest_dir = os.path.join(
            self.metadata['destination_chroot'], "chroot",
            os.path.basename(self.source_dir)
        )
        if not os.path.isdir(self.dest_dir):
            os.makedirs(self.dest_dir, 0o755)
        return 0

    def pre_run(self):
        self._output.output("[%s|%s] %s" % (
                blue("MirrorHandler"), darkred(self.spec_name),
                _("executing pre_run"),
            )
        )

        exec_script = self.metadata.get('inner_source_chroot_script')
        if exec_script:
            if os.path.isfile(exec_script[0]) and \
                os.access(exec_script[0], os.R_OK):
                rc = self._exec_inner_script(exec_script, self.source_dir)
                if rc != 0:
                    self._output.output("[%s|%s] %s: %s" % (
                            blue("MirrorHandler"), darkred(self.spec_name),
                            _("inner_source_chroot_script failed"), rc,
                        )
                    )
                    return rc


        self._output.output("[%s|%s] %s" % (
                blue("MirrorHandler"), darkred(self.spec_name),
                _("pre_run completed successfully"),
            )
        )

        return 0

    def post_run(self):
        self._output.output("[%s|%s] %s" % (
                blue("MirrorHandler"), darkred(self.spec_name),
                _("executing post_run"),
            )
        )
        return 0

    def kill(self, success = True):
        if not success:
            self._run_error_script(self.source_dir, self.dest_dir, None)
        self._output.output("[%s|%s] %s" % (
                blue("MirrorHandler"), darkred(self.spec_name),
                _("executing kill"),
            )
        )
        return 0

    def run(self):

        self._output.output("[%s|%s] %s" % (
                blue("MirrorHandler"), darkred(self.spec_name),
                _("mirroring running"),
            )
        )
        # running sync
        args = [self._config['mirror_syncer']]
        args.extend(self._config['mirror_syncer_builtin_args'])
        args.extend(self.metadata.get('extra_rsync_parameters', []))
        args.extend([self.source_dir+"/*", self.dest_dir])
        self._output.output("[%s|%s] %s: %s" % (
                blue("MirrorHandler"), darkred(self.spec_name),
                _("spawning"), args,
            )
        )
        rc = molecule.utils.exec_cmd(args)
        if rc != 0:
            self._output.output("[%s|%s] %s: %s" % (
                    blue("MirrorHandler"), darkred(self.spec_name),
                    _("mirroring failed"), rc,
                )
            )
            return rc

        self._output.output("[%s|%s] %s" % (
                blue("MirrorHandler"), darkred(self.spec_name),
                _("mirroring completed successfully"),
            )
        )
        return 0

class ChrootHandler(GenericExecutionStep, BuiltinHandlerMixin):

    def __init__(self, *args, **kwargs):
        GenericExecutionStep.__init__(self, *args, **kwargs)

    def setup(self):
        self.source_dir = self.metadata['source_chroot']
        self.dest_dir = os.path.join(
            self.metadata['destination_chroot'], "chroot",
            os.path.basename(self.source_dir)
        )
        return 0

    def pre_run(self):
        self._output.output("[%s|%s] %s" % (
                blue("ChrootHandler"), darkred(self.spec_name),
                _("executing pre_run"),
            )
        )

        # run outer chroot script
        exec_script = self.metadata.get('outer_chroot_script')
        if exec_script:
            os.environ['CHROOT_DIR'] = self.source_dir
            self._output.output("[%s|%s] %s: %s" % (
                    blue("ChrootHandler"), darkred(self.spec_name),
                    _("spawning"), exec_script,
                )
            )
            rc = molecule.utils.exec_cmd(exec_script)
            if rc != 0:
                self._output.output("[%s|%s] %s: %s" % (
                        blue("ChrootHandler"), darkred(self.spec_name),
                        _("outer chroot hook failed"), rc,
                    )
                )
                return rc

        return 0

    def post_run(self):
        self._output.output("[%s|%s] %s" % (
                blue("ChrootHandler"), darkred(self.spec_name),
                _("executing post_run"),
            )
        )

        # now remove paths to empty
        empty_paths = self.metadata.get('paths_to_empty', [])
        for mypath in empty_paths:
            mypath = self.dest_dir+mypath
            self._output.output("[%s|%s] %s: %s" % (
                    blue("ChrootHandler"), darkred(self.spec_name),
                    _("emptying dir"), mypath,
                )
            )
            if os.path.isdir(mypath):
                molecule.utils.empty_dir(mypath)

        # now remove paths to remove (...)
        remove_paths = self.metadata.get('paths_to_remove', [])

        # setup sandbox
        sb_dirs = [self.dest_dir]
        sb_env = {
            'SANDBOX_WRITE': ':'.join(sb_dirs),
        }
        myenv = os.environ.copy()
        myenv.update(sb_env)

        for mypath in remove_paths:
            mypath = self.dest_dir+mypath
            self._output.output("[%s|%s] %s: %s" % (
                    blue("ChrootHandler"), darkred(self.spec_name),
                    _("removing dir"), mypath,
                )
            )
            rc = molecule.utils.remove_path_sandbox(mypath, sb_env)
            if rc != 0:
                self._output.output("[%s|%s] %s: %s: %s" % (
                        blue("ChrootHandler"), darkred(self.spec_name),
                        _("removal failed for"), mypath, rc,
                    )
                )
                return rc

        # write release file
        release_file = self.metadata.get('release_file')
        if isinstance(release_file, get_stringtype()) and release_file:
            if release_file[0] == os.sep:
                release_file = release_file[len(os.sep):]
            release_file = os.path.join(self.dest_dir, release_file)
            if os.path.lexists(release_file) and not os.path.isfile(release_file):
                self._output.output("[%s|%s] %s: %s" % (
                        blue("ChrootHandler"), darkred(self.spec_name),
                        _("release file creation failed, not a file"),
                        release_file,
                    )
                )
                return 1
            release_string = self.metadata.get('release_string', '')
            release_version = self.metadata.get('release_version', '')
            release_desc = self.metadata.get('release_desc', '')
            file_string = "%s %s %s\n" % (release_string, release_version, release_desc,)
            try:
                f = open(release_file, "w")
                f.write(file_string)
                f.flush()
                f.close()
            except (IOError, OSError,) as e:
                self._output.output("[%s|%s] %s: %s: %s" % (
                        blue("ChrootHandler"), darkred(self.spec_name),
                        _("release file creation failed, system error"),
                        release_file, e,
                    )
                )
                return 1

        # run outer chroot script after
        exec_script = self.metadata.get('outer_chroot_script_after')
        if exec_script:
            os.environ['CHROOT_DIR'] = self.source_dir
            self._output.output("[%s|%s] %s: %s" % (
                    blue("ChrootHandler"), darkred(self.spec_name),
                    _("spawning"), exec_script,
                )
            )
            rc = molecule.utils.exec_cmd(exec_script)
            if rc != 0:
                self._output.output("[%s|%s] %s: %s" % (
                        blue("ChrootHandler"), darkred(self.spec_name),
                        _("outer chroot hook (after inner) failed"), rc,
                    )
                )
                return rc

        return 0

    def kill(self, success = True):
        if not success:
            self._run_error_script(self.source_dir, self.dest_dir, None)
        self._output.output("[%s|%s] %s" % (
                blue("ChrootHandler"),
                darkred(self.spec_name), _("executing kill"),
            )
        )
        return 0

    def run(self):

        self._output.output("[%s|%s] %s" % (
                blue("ChrootHandler"), darkred(self.spec_name),
                _("hooks running"),
            )
        )

        # run inner chroot script
        exec_script = self.metadata.get('inner_chroot_script')
        if exec_script:
            if os.path.isfile(exec_script[0]) and os.access(exec_script[0], os.R_OK):
                rc = self._exec_inner_script(exec_script, self.dest_dir)
                if rc != 0:
                    return rc


        self._output.output("[%s|%s] %s" % (
                blue("ChrootHandler"), darkred(self.spec_name),
                _("hooks completed succesfully"),
            )
        )
        return 0

class CdrootHandler(GenericExecutionStep, BuiltinHandlerMixin):

    def __init__(self, *args, **kwargs):
        GenericExecutionStep.__init__(self, *args, **kwargs)

    def setup(self):
        self.source_chroot = os.path.join(
            self.metadata['destination_chroot'], "chroot",
            os.path.basename(self.metadata['source_chroot'])
        )
        self.dest_root = os.path.join(
            self.metadata['destination_livecd_root'], "livecd",
            os.path.basename(self.metadata['source_chroot'])
        )
        if os.path.isdir(self.dest_root):
            molecule.utils.empty_dir(self.dest_root)
        if not os.path.isdir(self.dest_root):
            os.makedirs(self.dest_root, 0o755)
        return 0

    def pre_run(self):
        self._output.output("[%s|%s] %s" % (
                blue("CdrootHandler"), darkred(self.spec_name),
                _("executing pre_run"),
            )
        )

        self._output.output("[%s|%s] %s" % (
                blue("CdrootHandler"), darkred(self.spec_name),
                _("preparing environment"),
            )
        )
        return 0

    def post_run(self):
        self._output.output("[%s|%s] %s" % (
                blue("CdrootHandler"), darkred(self.spec_name),
                _("executing post_run"),
            )
        )
        return 0

    def kill(self, success = True):
        if not success:
            self._run_error_script(None, self.source_chroot,
                self.dest_root)
        self._output.output("[%s|%s] %s" % (
                blue("CdrootHandler"), darkred(self.spec_name),
                _("executing kill"),
            )
        )
        return 0

    def run(self):

        self._output.output("[%s|%s] %s" % (
                blue("CdrootHandler"), darkred(self.spec_name),
                _("compressing chroot"),
            )
        )
        args = [self._config['chroot_compressor']]
        comp_output = self._config['chroot_compressor_output_file']
        if "chroot_compressor_output_file" in self.metadata:
            comp_output = self.metadata.get('chroot_compressor_output_file')
        comp_output = os.path.join(self.dest_root, comp_output)
        args.extend([self.source_chroot, comp_output])
        args.extend(self._config['chroot_compressor_builtin_args'])
        args.extend(self.metadata.get('extra_mksquashfs_parameters', []))
        self._output.output("[%s|%s] %s: %s" % (
                blue("CdrootHandler"), darkred(self.spec_name),
                _("spawning"), args,
            )
        )
        rc = molecule.utils.exec_cmd(args)
        if rc != 0:
            self._output.output("[%s|%s] %s: %s" % (
                    blue("CdrootHandler"), darkred(self.spec_name),
                    _("chroot compression failed"), rc,
                )
            )
            return rc
        self._output.output("[%s|%s] %s" % (
                blue("CdrootHandler"), darkred(self.spec_name),
                _("chroot compressed successfully"),
            )
        )

        # merge dir
        merge_dir = self.metadata.get('merge_livecd_root')
        if merge_dir:
            if os.path.isdir(merge_dir):
                self._output.output("[%s|%s] %s %s" % (
                    blue("CdrootHandler"), darkred(self.spec_name),
                    _("merging livecd root"), merge_dir,)
                )
                import stat
                content = os.listdir(merge_dir)
                for mypath in content:
                    mysource = os.path.join(merge_dir, mypath)
                    mydest = os.path.join(self.dest_root, mypath)
                    copystat = False

                    if os.path.islink(mysource):
                        tolink = os.readlink(mysource)
                        os.symlink(tolink, mydest)
                    elif os.path.isfile(mysource) or os.path.islink(mysource):
                        copystat = True
                        shutil.copy2(mysource, mydest)
                    elif os.path.isdir(mysource):
                        copystat = True
                        shutil.copytree(mysource, mydest)

                    if copystat:
                        user = os.stat(mysource)[stat.ST_UID]
                        group = os.stat(mysource)[stat.ST_GID]
                        os.chown(mydest, user, group)
                        shutil.copystat(mysource, mydest)

        return 0

class IsoHandler(GenericExecutionStep, BuiltinHandlerMixin):

    MD5_EXT = ".md5"

    def __init__(self, *args, **kwargs):
        GenericExecutionStep.__init__(self, *args, **kwargs)

    def setup(self):
        # setup paths
        self.source_path = os.path.join(
            self.metadata['destination_livecd_root'], "livecd",
            os.path.basename(self.metadata['source_chroot'])
        )
        dest_iso_dir = self.metadata['destination_iso_directory']
        if not os.path.isdir(dest_iso_dir):
            os.makedirs(dest_iso_dir, 0o755)
        dest_iso_filename = self.metadata.get('destination_iso_image_name')
        release_string = self.metadata.get('release_string', '')
        release_version = self.metadata.get('release_version', '')
        release_desc = self.metadata.get('release_desc', '')
        if not dest_iso_filename:
            dest_iso_filename = "%s_%s_%s.iso" % (
                release_string.replace(' ', '_'),
                release_version.replace(' ', '_'),
                release_desc.replace(' ', '_'),
            )
        self.dest_iso = os.path.join(dest_iso_dir, dest_iso_filename)
        self.iso_title = "%s %s %s" % (release_string, release_version, release_desc,)
        self.source_chroot = self.metadata['source_chroot']
        self.chroot_dir = os.path.join(
            self.metadata['destination_chroot'], "chroot",
            os.path.basename(self.source_chroot)
        )
        return 0

    def pre_run(self):
        self._output.output("[%s|%s] %s" % (
                blue("IsoHandler"), darkred(self.spec_name),
                _("executing pre_run"),
            )
        )

        # run pre iso script
        exec_script = self.metadata.get('pre_iso_script')
        if exec_script:
            os.environ['SOURCE_CHROOT_DIR'] = self.source_chroot
            os.environ['CHROOT_DIR'] = self.chroot_dir
            os.environ['CDROOT_DIR'] = self.source_path
            os.environ['ISO_PATH'] = self.dest_iso
            os.environ['ISO_CHECKSUM_PATH'] = self.dest_iso + IsoHandler.MD5_EXT
            self._output.output("[%s|%s] %s: %s" % (
                    blue("IsoHandler"), darkred(self.spec_name),
                    _("spawning"), exec_script,
                )
            )
            rc = molecule.utils.exec_cmd(exec_script)
            if rc != 0:
                self._output.output("[%s|%s] %s: %s" % (
                        blue("IsoHandler"), darkred(self.spec_name),
                        _("pre iso hook failed"), rc,
                    )
                )
                return rc

        return 0

    def post_run(self):
        self._output.output("[%s|%s] %s" % (
                blue("IsoHandler"), darkred(self.spec_name),
                _("executing post_run"),
            )
        )

        # run post iso script
        exec_script = self.metadata.get('post_iso_script')
        if exec_script:
            os.environ['ISO_PATH'] = self.dest_iso
            os.environ['ISO_CHECKSUM_PATH'] = self.dest_iso + IsoHandler.MD5_EXT
            self._output.output("[%s|%s] %s: %s" % (
                    blue("IsoHandler"), darkred(self.spec_name),
                    _("spawning"), exec_script,
                )
            )
            rc = molecule.utils.exec_cmd(exec_script)
            if rc != 0:
                self._output.output("[%s|%s] %s: %s" % (
                        blue("IsoHandler"), darkred(self.spec_name),
                        _("post iso hook failed"), rc,
                    )
                )
                return rc

        return 0

    def kill(self, success = True):
        if not success:
            self._run_error_script(self.source_chroot, self.chroot_dir,
                self.source_path)
        self._output.output("[%s|%s] %s" % (
                blue("IsoHandler"), darkred(self.spec_name),
                _("executing kill"),
            )
        )
        return 0

    def run(self):

        self._output.output("[%s|%s] %s" % (
                blue("IsoHandler"), darkred(self.spec_name),
                _("building ISO image"),
            )
        )

        args = [self._config['iso_builder']]
        args.extend(self._config['iso_builder_builtin_args'])
        args.extend(self.metadata.get('extra_mkisofs_parameters', []))
        if self.iso_title.strip():
            args.extend(["-V", '"', self.iso_title[:30], '"'])
        args.extend(['-o', self.dest_iso, self.source_path])
        self._output.output("[%s|%s] %s: %s" % (
                blue("IsoHandler"), darkred(self.spec_name),
                _("spawning"), args,
            )
        )
        rc = molecule.utils.exec_cmd(args)
        if rc != 0:
            self._output.output("[%s|%s] %s: %s" % (
                    blue("IsoHandler"), darkred(self.spec_name),
                    _("ISO image build failed"), rc,
                )
            )
            return rc

        self._output.output("[%s|%s] %s: %s" % (
                blue("IsoHandler"), darkred(self.spec_name),
                _("built ISO image"), self.dest_iso,
            )
        )
        if os.path.isfile(self.dest_iso) and os.access(self.dest_iso, os.R_OK):
            self._output.output("[%s|%s] %s: %s" % (
                    blue("IsoHandler"), darkred(self.spec_name),
                    _("generating md5 for"), self.dest_iso,
                )
            )
            digest = molecule.utils.md5sum(self.dest_iso)
            md5file = self.dest_iso + IsoHandler.MD5_EXT
            with open(md5file, "w") as f:
                f.write("%s  %s\n" % (digest, os.path.basename(self.dest_iso),))
                f.flush()

        return 0

class LivecdSpec(GenericSpec):

    PLUGIN_API_VERSION = 0

    @staticmethod
    def execution_strategy():
        return "livecd"

    def vital_parameters(self):
        return [
            "release_string",
            "source_chroot",
            "destination_iso_directory",
            "destination_livecd_root",
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
            'source_chroot': {
                'cb': self.valid_dir,
                've': self.ve_string_stripper,
            },
            'destination_chroot': {
                'cb': self.valid_path_string,
                've': self.ve_string_stripper,
            },
            'extra_rsync_parameters': {
                'cb': self.always_valid,
                've': self.ve_string_splitter,
            },
            'merge_destination_chroot': {
                'cb': self.valid_dir,
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
            'inner_source_chroot_script': {
                'cb': self.valid_path_string_first_list_item,
                've': self.ve_string_splitter,
            },
            'inner_chroot_script': {
                'cb': self.valid_path_string_first_list_item,
                've': self.ve_string_splitter,
            },
            'outer_chroot_script_after': {
                'cb': self.valid_exec_first_list_item,
                've': self.ve_string_splitter,
            },
            'destination_livecd_root': {
                'cb': self.valid_path_string,
                've': self.ve_string_stripper,
            },
            'merge_livecd_root': {
                'cb': self.valid_dir,
                've': self.ve_string_stripper,
            },
            'extra_mksquashfs_parameters': {
                'cb': self.always_valid,
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
        return [MirrorHandler, ChrootHandler, CdrootHandler, IsoHandler]
