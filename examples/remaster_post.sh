#!/bin/sh
PKGS_DIR="/sabayon/remaster/pkgs"
CHROOT_PKGS_DIR="${CHROOT_DIR}/var/lib/entropy/packages"

echo "Umounting packages over"
umount "${CHROOT_DIR}/dev"
umount "${CHROOT_PKGS_DIR}" || exit 1
