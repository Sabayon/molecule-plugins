# Use abs path, otherwise daily builds automagic won't work
%import /sabayon/molecules/core-openvz-template.common

# pre chroot command, example, for 32bit chroots on 64bit system, you always
# have to append "linux32" this is useful for inner_chroot_script
prechroot: linux32

# Path to source ISO file (MANDATORY)
source_iso: /sabayon/iso/Sabayon_Linux_CoreCD_DAILY_x86.iso

