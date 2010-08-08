# Use abs path, otherwise daily builds automagic won't work
# For further documentation, see the file above:
%import /sabayon/molecules/spinbase-amazon-ami-image-template.common

# pre chroot command, example, for 32bit chroots on 64bit system, you always
# have to append "linux32" this is useful for inner_chroot_script
# prechroot:

# Path to source ISO file (MANDATORY)
source_iso: /sabayon/iso/Sabayon_Linux_SpinBase_DAILY_amd64.iso

release_version: 5.3
image_name: Sabayon_Linux_SpinBase_5.3_amd64_ami.img
