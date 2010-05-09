#!/bin/sh
PKGS_DIR="/sabayon/remaster/pkgs"
CHROOT_PKGS_DIR="${CHROOT_DIR}/var/lib/entropy/packages"

[[ ! -d "${PKGS_DIR}" ]] && mkdir -p "${PKGS_DIR}"
[[ ! -d "${CHROOT_PKGS_DIR}" ]] && mkdir -p "${CHROOT_PKGS_DIR}"

echo "Mounting packages over"
mount --bind "${PKGS_DIR}" "${CHROOT_PKGS_DIR}" || exit 1
mount --bind "/dev" "${CHROOT_DIR}/dev"
