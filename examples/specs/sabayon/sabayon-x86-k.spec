# Use abs path, otherwise daily builds automagic won't work
%import /sabayon/molecules/gnome+kde.common

# pre chroot command, example, for 32bit chroots on 64bit system, you always have to append "linux32"
# this is useful for inner_chroot_script
prechroot: linux32

# Release Version
# Keep this here, otherwise daily iso images build won't work
release_version: 5.3

# Release Version string description
release_desc: x86 K

# Source chroot directory, where files are pulled from
source_chroot: /sabayon/sources/x86_kde-2009

# Destination ISO image name, call whatever you want.iso, not mandatory
# Keep this here, of course
destination_iso_image_name: Sabayon_Linux_5.3_x86_K.iso
