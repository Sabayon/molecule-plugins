# -*- coding: utf-8 -*-
import os
import sys
sys.path.insert(0,'.')
sys.path.insert(0,'..')
import unittest

from molecule.settings import SpecParser
from molecule.compat import get_stringtype

class ParsersTest(unittest.TestCase):

    def setUp(self):
        sys.stdout.write("%s called\n" % (self,))
        sys.stdout.flush()

    def tearDown(self):
        """
        tearDown is run after each test
        """
        sys.stdout.write("%s ran\n" % (self,))
        sys.stdout.flush()

    def test_iso_remaster(self):

        from src.remaster_plugin import RemasterSpec

        expected_data = {
            'execution_strategy': "iso_remaster",
            'paths_to_remove': ['/this/and/that', '/that/and/this'],
            'post_iso_script': ['/sabayon/scripts/post_iso_script.sh'],
            'iso_title': 'Sabayon KDE',
            'extra_mkisofs_parameters': ['-b', 'isolinux/isolinux.bin', '-c',
                'isolinux/boot.cat'],
            'release_version': '5.3',
            'source_iso': 'specs/data/Sabayon_Linux_SpinBase_DAILY_x86.iso',
            '__plugin__': None,
            'destination_iso_image_name': 'Sabayon_Linux_5.3_x86_TEST.iso',
            'release_desc': 'x86 TEST',
            'packages_to_remove': ['app-foo/foo', 'app-foo2/foo2'],
            'pre_iso_script': ['/sabayon/scripts/generic_pre_iso_script.sh',
                'KDE'],
            'custom_packages_add_cmd': ['equo', 'install', '--ask'],
            'packages_to_add': ['app-admin/packagekit-base',
                'app-admin/packagekit-qt4', 'app-admin/sulfur'],
            'release_file': '/etc/sabayon-edition',
            'outer_chroot_script': ['/sabayon/scripts/remaster_pre.sh'],
            'execute_repositories_update': 'yes',
            'inner_chroot_script_after': [
                '/sabayon/scripts/remaster_generic_inner_chroot_script_after.sh',
                'kde'],
            'release_string': 'Sabayon Linux',
            'paths_to_empty': ['/empty/this', '/empty/that'],
            'destination_iso_directory': 'specs/out/',
            'repositories_update_cmd': ['equo', 'update', '--debug'],
            'outer_chroot_script_after': ['/sabayon/scripts/remaster_post.sh']
        }

        parse_obj = SpecParser("specs/iso_remaster.spec")
        extracted_data = parse_obj.parse()

        self.assert_(isinstance(extracted_data['__plugin__'], RemasterSpec))
        extracted_data['__plugin__'] = None
        self.assertEqual(expected_data, extracted_data)

    def test_chroot_to_iso(self):

        from src.builtin_plugin import LivecdSpec

        expected_data = {
            'execution_strategy': "livecd",
            'destination_iso_image_name': 'Sabayon_Linux_5.3_x86_chroot_TEST.iso',
            'post_iso_script': ['specs/data/post_iso_script.sh'],
            'extra_mkisofs_parameters': ['-b', 'isolinux/isolinux.bin', '-c',
                'isolinux/boot.cat'],
            'prechroot': ['linux32'],
            'pre_iso_script': ['specs/data/pre_iso_script.sh'],
            'paths_to_remove': [
                '/var/lib/entropy/client/database/*/sabayonlinux.org',
                '/boot/grub/grub.conf',
                '/root/.subversion',
                '/lib/udev-state/devices.tar.bz2',
                '/var/log/scrollkeeper.log',
                '/var/log/genkernel.log',
                '/var/log/emerge.log',
                '/usr/tmp/portage/*',
                '/root/.bash_history',
                '/usr/share/slocate/slocate.db',
                '/root/test-results.txt',
                '/root/test.sh',
                '/usr/portage/distfiles/*',
                '/usr/portage/packages/*',
                '/root/.revdep*',
                '/install-data/games/*',
                '/var/lib/entropy/store/*',
                '/var/log/entropy/*',
                '/var/lib/entropy/caches/*',
                '/var/lib/entropy/smartapps/*/*',
                '/var/lib/entropy/smartapps/*/*',
                '/var/lib/entropy/tmp/*',
                '/var/lib/entropy/packages*/*',
                '/var/tmp/entropy/*',
                '/*.txt', '/usr/portage/a*',
                '/usr/portage/b*', '/usr/portage/c*',
                '/usr/portage/d*', '/usr/portage/e*', '/usr/portage/f*',
                '/usr/portage/g*', '/usr/portage/h*', '/usr/portage/i*',
                '/usr/portage/j*', '/usr/portage/k*', '/usr/portage/licenses',
                '/usr/portage/lxde*', '/usr/portage/m*', '/usr/portage/n*',
                '/usr/portage/o*', '/usr/portage/packages',
                '/usr/portage/pe*', '/usr/portage/q*',
                '/usr/portage/r*', '/usr/portage/s*',
                '/usr/portage/t*', '/usr/portage/u*', '/usr/portage/v*',
                '/usr/portage/w*', '/usr/portage/x*', '/usr/portage/y*',
                '/usr/portage/z*', '/etc/ssh/ssh_host_*', '/entropy',
                '/tmp/equoerror.txt', '/var/cache/man',
                '/var/lib/entropy/glsa/*', '/root/local', '/var/tmp/*',
                '/boot/grub/device.map'],
            'release_version': '5.3', 'source_chroot': 'specs/data/fake_chroot',
            'destination_chroot': 'specs/out/fake_dest_chroot',
            '__plugin__': None,
            'destination_livecd_root': 'specs/out/fake_livecd_root',
            'release_desc': 'x86 SpinBase',
            'inner_chroot_script': ['/sabayon/scripts/inner_chroot_script.sh',
                'spinbase'],
            'extra_rsync_parameters': ['--one-file-system', '--exclude',
                '/proc/*', '--exclude', '/dev/pts/*'],
            'release_file': '/etc/sabayon-edition',
            'merge_livecd_root': 'specs/out/fake_merge_livecd_root',
            'release_string': 'Sabayon Linux',
            'paths_to_empty': ['/home/sabayonuser/.thumbnails/',
                '/root/.ccache', '/var/tmp/portage', '/var/tmp/ccache',
                '/var/tmp/portage-pkg', '/var/tmp/binpkgs',
                '/var/lib/entropy/portage', '/var/lib/entropy/logs',
                '/var/cache/genkernel'],
            'destination_iso_directory': 'specs/out'
        }

        parse_obj = SpecParser("specs/chroot_to_iso.spec")
        extracted_data = parse_obj.parse()

        self.assert_(isinstance(extracted_data['__plugin__'], LivecdSpec))
        extracted_data['__plugin__'] = None
        self.assertEqual(expected_data, extracted_data)

    def test_iso_to_tar(self):

        from src.tar_plugin import IsoToTarSpec

        expected_data = {
            'execution_strategy': "iso_to_tar",
            'iso_mounter': ['mount', '-t', 'iso9660', '-o', 'loop,ro'],
            'custom_packages_add_cmd': 'equo install --debug',
            'post_tar_script': ['specs/data/post_tar_script.sh'],
            'paths_to_remove': ['remove/this', 'and/that'],
            'release_version': '5.3',
            'custom_packages_remove_cmd': 'equo remove --debug',
            'source_iso': 'specs/data/Sabayon_Linux_SpinBase_DAILY_x86.iso',
            '__plugin__': None,
            'prechroot': ['linux32'],
            'packages_to_remove': ['app-remove/this', 'app-remove/that'],
            'inner_chroot_script': ['specs/data/inner_chroot_script.sh'],
            'pre_tar_script': ['specs/data/pre_tar_script.sh'],
            'packages_to_add': ['add-this/pkg', 'add-that/pkg'],
            'iso_umounter': ['umount', '-l'],
            'error_script': ['specs/data/error_script.sh'],
            'destination_tar_directory': 'specs/out/',
            'outer_chroot_script': ['specs/data/outer_chroot_script.sh'],
            'execute_repositories_update': 'yes', 'compression_method': 'bz2',
            'inner_chroot_script_after': ['specs/data/inner_chroot_script_after.sh'],
            'paths_to_empty': ['remove/that', 'and/this'],
            'squash_mounter': ['mount', '-t', 'squashfs', '-o', 'loop,ro'],
            'squash_umounter': ['umount', '-l'],
            'tar_name': 'Sabayon_Linux_SpinBase_5.3_x86_openvz.tar.bz2',
            'repositories_update_cmd': ['equo', 'update', '--debug'],
            'outer_chroot_script_after': [
                'specs/data/outer_chroot_script_after.sh']
        }

        parse_obj = SpecParser("specs/iso_to_tar.spec")
        extracted_data = parse_obj.parse()

        self.assert_(isinstance(extracted_data['__plugin__'], IsoToTarSpec))
        extracted_data['__plugin__'] = None
        self.assertEqual(expected_data, extracted_data)

    def test_iso_to_image(self):

        from src.image_plugin import IsoToImageSpec

        expected_data = {
            'execution_strategy': "iso_to_image",
            'destination_image_directory': '/',
            'outer_chroot_script_after': [
                '/path/to/script/to/be/executed/outside/after'],
            'iso_mounter': ['mount', '-t', 'iso9660', '-o', 'loop'],
            'prechroot': ['linux32'],
            'image_name': 'image_name_w00t Sabayon_Linux_SpinBase_5.3_x86_ami.img',
            'paths_to_remove': ['/remove/this', '/and/that'],
            'release_version': '5.3',
            'custom_packages_remove_cmd': 'equo remove --debug',
            'source_iso': 'specs/data/Sabayon_Linux_SpinBase_DAILY_x86.iso',
            'image_mb': 5000,
            'image_randomize': 'yes',
            'image_formatter': ['mkfs.ext2'],
            'packages_to_remove': ['app-remove/this', 'app-remove/that'],
            'inner_chroot_script': ['/sabayon/scripts/openvz_inner_chroot_script.sh'],
            'custom_packages_add_cmd': 'equo install --debug',
            'packages_to_add': ['app-add/this', 'app-add/that'],
            'iso_umounter': ['umount', '-l'],
            'error_script': ['/path/to/script/to/be/executed/outside/after'],
            'image_mounter': ['mount', '-o', 'rw,loop'],
            'post_image_script': ['/sabayon/scripts/post_image_script.sh'],
            'outer_chroot_script': ['/path/to/script/to/be/executed/outside'],
            'execute_repositories_update': 'yes',
            'inner_chroot_script_after': [
                '/sabayon/scripts/image_generic_inner_chroot_script_after.sh'],
            'paths_to_empty': ['/empty/this', 'and/that'],
            'squash_mounter': ['mount', '-t', 'squashfs', '-o', 'loop'],
            'pre_image_script': ['/sabayon/scripts/pre_image_script.sh'],
            'repositories_update_cmd': ['equo', 'update', '--debug'],
            '__plugin__': None, 'image_umounter': ['umount', '-l']
        }

        parse_obj = SpecParser("specs/iso_to_image.spec")
        extracted_data = parse_obj.parse()

        self.assert_(isinstance(extracted_data['__plugin__'], IsoToImageSpec))
        extracted_data['__plugin__'] = None
        self.assertEqual(expected_data, extracted_data)

if __name__ == '__main__':
    unittest.main()
    raise SystemExit(0)
