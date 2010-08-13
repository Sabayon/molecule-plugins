# Use abs path, otherwise daily builds automagic won't work
%import chroot_to_iso.common

# Release Version
# Keep this here, otherwise daily builds automagic won't work
release_version: 5.3

prechroot: linux32

# Release Version string description
release_desc: x86 SpinBase

# Source chroot directory, where files are pulled from
source_chroot: specs/data/fake_chroot

# Destination ISO image name, call whatever you want.iso, not mandatory
# Keep this here and set, otherwise daily builds automagic won't work
destination_iso_image_name: Sabayon_Linux_5.3_x86_chroot_TEST.iso
