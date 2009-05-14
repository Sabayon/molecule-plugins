#!/usr/bin/python
import os, shutil
source_chroot_dir = os.getenv('SOURCE_CHROOT_DIR')
chroot_dir = os.getenv('CHROOT_DIR')
cdroot_dir = os.getenv('CDROOT_DIR')
boot_dir = os.path.join(chroot_dir,"boot")
cdroot_boot_dir = os.path.join(cdroot_dir,"boot")

boot_kernel = [x for x in os.listdir(boot_dir) if x.startswith("kernel-")]
if boot_kernel:
    boot_kernel = os.path.join(boot_dir,sorted(boot_kernel)[0])
    shutil.copy2(boot_kernel,os.path.join(cdroot_boot_dir,"sabayon"))

boot_ramfs = [x for x in os.listdir(boot_dir) if x.startswith("initramfs-")]
if boot_ramfs:
    boot_ramfs = os.path.join(boot_dir,sorted(boot_ramfs)[0])
    shutil.copy2(boot_ramfs,os.path.join(cdroot_boot_dir,"sabayon.igz"))

