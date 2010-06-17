# use abs path, otherwise daily iso build automagic won't work
%import /sabayon/molecules/corecdx.common

release_desc: x86 CoreCDX

# pre chroot command, example, for 32bit chroots on 64bit system, you always
# have to append "linux32" this is useful for inner_chroot_script
prechroot: linux32

# Path to source ISO file (MANDATORY)
source_iso: /sabayon/iso/Sabayon_Linux_SpinBase_DAILY_x86.iso

# Destination ISO image name, call whatever you want.iso, not mandatory
destination_iso_image_name: Sabayon_Linux_CoreCDX_5.3_x86.iso
