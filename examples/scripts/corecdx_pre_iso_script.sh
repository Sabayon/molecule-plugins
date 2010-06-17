#!/bin/bash
ver=${RELEASE_VERSION}
[[ -z "${ver}" ]] && ver=${CUR_DATE}
[[ -z "${ver}" ]] && ver="5.3"

sed -i "s/__VERSION__/${ver}/g" "${CDROOT_DIR}/isolinux/isolinux.cfg"
sed -i "s/gentoo=nox//g" "${CDROOT_DIR}/isolinux/isolinux.cfg"
sed -i "s/nox//g" "${CDROOT_DIR}/isolinux/isolinux.cfg"
sed -i "s/installer-text/installer-gui/g" "${CDROOT_DIR}/isolinux/isolinux.cfg"
sed -i "s/text-install/gui-install/g" "${CDROOT_DIR}/isolinux/isolinux.cfg"
# splashutils is stupid and gives black screen at the end of the boot if X is not there
# sed -i "s/splash=verbose/splash=silent/g" "${CDROOT_DIR}/isolinux/isolinux.cfg"
sed -i "s/CoreCD/CoreCDX/g" "${CDROOT_DIR}/isolinux/isolinux.cfg"

sabayon_pkgs_file="${CHROOT_DIR}/etc/sabayon-pkglist"
if [ -f "${sabayon_pkgs_file}" ]; then
        cp "${sabayon_pkgs_file}" "${CDROOT_DIR}/pkglist"
fi
