# Molecule example .spec file

# Define an alternative execution strategy, in this case, the value must be
# "livecd"
# execution_strategy: livecd

# pre chroot command, example, for 32bit chroots on 64bit system, you always have to append "linux32"
# prechroot: linux32

# Release string
# release_string: Sabayon Linux

# Release Version
# release_version: 4

# Release Version string description
# release_desc: Lite MCE

# Release file (inside chroot)
# release_file: /etc/sabayon-edition

# Source chroot directory, where files are pulled from
# source_chroot: /var/tmp/catalyst/tmp/stage1-amd64-2006.0

# Destination chroot directory, where files are pushed to before creating the squashfs image
# NOTE: data will be stored inside an auto-generated subdir
# destination_chroot: /var/tmp/catalyst/tmp/stage1-amd64-2006.0/default/livecd-stage2-amd64-2006.0

# Merge directory with destination chroot
# merge_destination_chroot: /path/to/your/chroot/overlay

# Extra mirror (r)sync parameters
# extra_rsync_parameters:

# Error script command, executed when something went wrong and molecule has to terminate the execution
# environment variables exported:
# - CHROOT_DIR: path to chroot directory, if any
# - CDROOT_DIR: path to livecd root directory, if any
# - SOURCE_CHROOT_DIR: path from where chroot is copied for final handling
# error_script: /path/to/script/to/be/executed/outside/after

# Outer chroot script command, to be executed outside destination chroot before packing it
# outer_chroot_script: /path/to/script/to/be/executed/outside

# Inner chroot script command, to be executed inside destination chroot before packing it
# inner_chroot_script: /path/to/script/to/be/executed/inside

# Destination LiveCD root directory, where files are placed before getting mkisofs'ed
# NOTE: data will be stored inside an auto-generated subdir
# destination_livecd_root: /path/to/dest/livecd

# Merge directory with destination LiveCD root
# merge_livecd_root: /path/to/your/configured/bootloader dir

# Extra mksquashfs parameters
# extra_mksquashfs_parameters:

# Extra mkisofs parameters, perhaps something to include/use your bootloader
# extra_mkisofs_parameters:

# Pre-ISO building script. Hook to be able to copy kernel images in place, for example
# pre_iso_script: 

# Destination directory for the ISO image path
# destination_iso_directory:

# Destination ISO image name, call whatever you want.iso, not mandatory
# destination_iso_image_name:

# Directories to remove completely (comma separated)
# paths_to_remove: /path/to/a, /path/to/b

# Directories to empty (comma separated)
# paths_to_empty: /path/to/a, /path/to/b
