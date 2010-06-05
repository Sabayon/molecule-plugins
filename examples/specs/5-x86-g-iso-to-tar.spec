# Sabayon Linux 5 x86 GNOME Molecule ISO to compressed tar
# The aim of this spec file is make easily scriptable the creation of tar.*
# files generated off a Sabayon Linux ISO Live system environment.
# This, for example, enables users to easily create OpenVZ templates of any
# existing Sabayon Linux ISO image.
# squashfs needed

# Define an alternative execution strategy, in this case, the value must be
# "iso_to_tar"
execution_strategy: iso_to_tar

# pre chroot command, example, for 32bit chroots on 64bit system, you always
# have to append "linux32" this is useful for inner_chroot_script
prechroot: linux32

# Path to source ISO file (MANDATORY)
source_iso: /sabayon/iso_images/Sabayon_5.0_G.iso

# Error script command, executed when something went wrong and molecule has to terminate the execution
# environment variables exported:
# - CHROOT_DIR: path to chroot directory, if any
# - CDROOT_DIR: path to livecd root directory, if any
# - SOURCE_CHROOT_DIR: path from where chroot is copied for final handling
# error_script: /path/to/script/to/be/executed/outside/after

# Outer chroot script command, to be executed outside destination chroot before
# before entering it (and before inner_chroot_script)
# outer_chroot_script: /path/to/script/to/be/executed/outside

# Inner chroot script command, to be executed inside destination chroot before packing it
# - kmerge.sh - setup kernel bins
# inner_chroot_script: /sabayon/scripts/inner_chroot_script.sh

# Outer chroot script command, to be executed outside destination chroot before
# before entering it (and AFTER inner_chroot_script)
# outer_chroot_script_after: /path/to/script/to/be/executed/outside/after

# Pre-ISO building script. Hook called before making the iso image.
# environment variables exported:
# SOURCE_CHROOT_DIR: path pointing to source chroot directory
# CHROOT_DIR: path pointing to destination chroot directory (chroot being worked
#    on)
# CDROOT_DIR: path pointing to CD/DVD root directory (ISO filesystem root)
# pre_iso_script: /sabayon/scripts/cdroot.py

# Post-ISO building script. Hook called after having made the iso image and md5.
# environment variables exported:
# ISO_PATH: path to newly created ISO image file
# ISO_CHECKSUM_PATH: path to newly created ISO image checksum file
# post_iso_script: /sabayon/scripts/post_iso_script.sh

# Destination directory for the ISO image path (MANDATORY)
destination_tar_directory: /home/fabio

# Compression method (default is: gz). Supported compression methods: gz, bz2
# compression_method: gz

# Specify an alternative tar file name (tar file name will be automatically
# produced otherwise)
# tar_name:

# Alternative ISO file mount command (default is: mount -o loop -t iso9660)
# iso_mounter:

# Alternative ISO umounter command (default is: umount)
# iso_umounter:

# Alternative squashfs file mount command (default is: mount -o loop -t squashfs)
# squash_mounter:

# Alternative ISO squashfs umount command (default is: umount)
# squash_umounter:

# Merge directory with destination LiveCD root (before tarring everything up)
# merge_livecd_root: /put/more/files/onto/CD/root

# List of packages that would be removed from chrooted system (comma separated)
# packages_to_remove:

# Custom shell call to packages removal (default is: equo remove)
# custom_packages_remove_cmd:

# List of packages that would be added from chrooted system (comma separated)
# packages_to_add:

# Custom shell call to packages add (default is: equo install)
# custom_packages_add_cmd:

# Custom command for updating repositories (default is: equo update)
# repositories_update_cmd:

# Determine whether repositories update should be run (if packages_to_add is set)
# (default is: no), values are: yes, no.
# execute_repositories_update: no

# Directories to remove completely (comma separated)
# paths_to_remove:

# Directories to empty (comma separated)
# paths_to_empty:
