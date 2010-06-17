#!/bin/sh
PKGS_DIR="/sabayon/remaster/pkgs"
CHROOT_PKGS_DIR="${CHROOT_DIR}/var/lib/entropy/packages"

echo "Merging back packages"
cp "${CHROOT_PKGS_DIR}"/* "${PKGS_DIR}"/ -Ra
rm -rf "${CHROOT_PKGS_DIR}"{,-nonfree,-restricted}/*
