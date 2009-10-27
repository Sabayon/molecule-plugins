# Sabayon Linux 4 amd64 Molecule spec file
# squashfs, mkisofs needed

# Define an alternative execution strategy, in this case, the value must be
# "livecd"
# execution_strategy: livecd

# pre chroot command, example, for 32bit chroots on 64bit system, you always have to append "linux32"
# this is useful for inner_chroot_script
# prechroot:

# Release string
release_string: Sabayon Linux

# Release Version
release_version: 5.0

# Release Version string description
release_desc: amd64 K

# Release file (inside chroot)
release_file: /etc/sabayon-edition

# Source chroot directory, where files are pulled from
source_chroot: /sabayon/sources/amd64_kde-2009

# Destination chroot directory, where files are pushed to before creating the squashfs image
# NOTE: data will be stored inside an auto-generated subdir
destination_chroot: /sabayon

# Merge directory with destination chroot
# merge_destination_chroot:

# Extra mirror (r)sync parameters
# extra_rsync_parameters:

# Outer chroot script command, to be executed outside destination chroot before packing it
# - amd64-archscript.sh - setup kernel bins
# outer_chroot_script: /path/to/script/to/be/executed/outside

# Inner chroot script command, to be executed inside destination chroot before packing it
# - kmerge.sh - setup kernel bins
inner_chroot_script: /sabayon/scripts/inner_chroot_script.sh

# Outer chroot script command, to be executed outside destination chroot before
# before entering it (and AFTER inner_chroot_script)
# outer_chroot_script_after: /path/to/script/to/be/executed/outside/after

# Destination LiveCD root directory, where files are placed before getting mkisofs'ed
# NOTE: data will be stored inside an auto-generated subdir
destination_livecd_root: /sabayon

# Merge directory with destination LiveCD root
merge_livecd_root: /sabayon/boot/standard

# Extra mksquashfs parameters
# extra_mksquashfs_parameters:

# Extra mkisofs parameters, perhaps something to include/use your bootloader
extra_mkisofs_parameters: -b isolinux/isolinux.bin -c isolinux/boot.cat

# Pre-ISO building script. Hook to be able to copy kernel images in place, for example
pre_iso_script: /sabayon/scripts/cdroot.py

# Destination directory for the ISO image path
destination_iso_directory: /home/fabio

# Destination ISO image name, call whatever you want.iso, not mandatory
# destination_iso_image_name:

# Directories to remove completely (comma separated)
paths_to_remove:
    /var/lib/entropy/client/database/amd64/sabayonlinux.org,
    /boot/grub/grub.conf,
    /root/.subversion,
    /lib/udev-state/devices.tar.bz2,
    /var/log/scrollkeeper.log, /var/log/genkernel.log,
    /var/log/emerge.log, /usr/tmp/portage/*,
    /root/.bash_history,
    /usr/share/slocate/slocate.db,
    /root/test-results.txt,
    /root/test.sh,
    /usr/portage/distfiles/*,
    /usr/portage/packages/*,
    /root/.revdep*,
    /install-data/games/*,
    /var/lib/entropy/store/*,
    /var/log/entropy/*,
    /var/lib/entropy/caches/*,
    /var/lib/entropy/smartapps/amd64/*,
    /var/lib/entropy/smartapps/amd64/*,
    /var/lib/entropy/tmp/*,
    /var/lib/entropy/packages/*,
    /var/tmp/entropy/*,
    /*.txt,
    /usr/portage/a*,
    /usr/portage/b*,
    /usr/portage/c*,
    /usr/portage/d*,
    /usr/portage/e*,
    /usr/portage/f*,
    /usr/portage/g*,
    /usr/portage/h*,
    /usr/portage/i*,
    /usr/portage/j*,
    /usr/portage/k*,
    /usr/portage/licenses,
    /usr/portage/lxde*,
    /usr/portage/m*,
    /usr/portage/n*,
    /usr/portage/o*,
    /usr/portage/packages,
    /usr/portage/pe*,
    /usr/portage/q*,
    /usr/portage/r*,
    /usr/portage/s*,
    /usr/portage/t*,
    /usr/portage/u*,
    /usr/portage/v*,
    /usr/portage/w*,
    /usr/portage/x*,
    /usr/portage/y*,
    /usr/portage/z*,
    /etc/ssh/ssh_host_*,
    /entropy,
    /tmp/equoerror.txt,
    /var/cache/man,
    /var/lib/entropy/glsa/*

# Directories to empty (comma separated)
paths_to_empty:
    /home/sabayonuser/.thumbnails/,
    /var/tmp,
    /root/.ccache,
    /var/tmp/portage,
    /var/tmp/ccache,
    /var/tmp/portage-pkg,
    /var/tmp/binpkgs,
    /var/lib/entropy/portage,
    /var/lib/entropy/logs,
    /var/lib/entropy/packages/amd64/4,
    /var/cache/genkernel
