# Sabayon Linux 5 x86 GNOME Molecule remaster spec file
# The aim of this spec file is to add arbitrary applications & misc stuff
# to an already built ISO image via scripting (providing hooks that call
# user-defined scripts).
# squashfs, mkisofs needed

# Define an alternative execution strategy, in this case, the value must be
# "iso_remaster"
execution_strategy: iso_remaster

# pre chroot command, example, for 32bit chroots on 64bit system, you always
# have to append "linux32" this is useful for inner_chroot_script
prechroot: linux32

# Path to source ISO file
source_iso: /sabayon/iso_images/Sabayon_5.0_G.iso

# Outer chroot script command, to be executed outside destination chroot before packing it
# - x86-archscript.sh - setup kernel bins
# outer_chroot_script: /path/to/script/to/be/executed/outside

# Inner chroot script command, to be executed inside destination chroot before packing it
# - kmerge.sh - setup kernel bins
# inner_chroot_script: /sabayon/scripts/inner_chroot_script.sh

# Extra mkisofs parameters, perhaps something to include/use your bootloader
extra_mkisofs_parameters: -b isolinux/isolinux.bin -c isolinux/boot.cat

# Pre-ISO building script. Hook to be able to copy kernel images in place, for example
# pre_iso_script: /sabayon/scripts/cdroot.py

# Destination directory for the ISO image path
destination_iso_directory: /home/fabio

# Destination ISO image name, call whatever you want.iso, not mandatory
# destination_iso_image_name:


