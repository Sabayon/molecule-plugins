# Use abs path, otherwise daily builds automagic won't work
%import /sabayon/molecules/lxde.common

# 32bit chroot
prechroot: linux32

# Release Version
release_version: 5.4

# Release Version string description
release_desc: x86 LXDE

# Path to source ISO file (MANDATORY)
source_iso: /sabayon/iso/Sabayon_Linux_SpinBase_DAILY_x86.iso

# Destination ISO image name, call whatever you want.iso, not mandatory
destination_iso_image_name: Sabayon_Linux_5.3_x86_LXDE.iso
