#!/bin/bash
cp /sabayon/remaster/remaster_isolinux.cfg "${CDROOT_DIR}/isolinux/isolinux.cfg"
ver=${RELEASE_VERSION}
[[ -z "${ver}" ]] && ver=${CUR_DATE}
[[ -z "${ver}" ]] && ver="5.3"

sed -i "s/__VERSION__/${ver}/g" "${CDROOT_DIR}/isolinux/isolinux.cfg"
sed -i "s/__FLAVOUR__/${1}/g" "${CDROOT_DIR}/isolinux/isolinux.cfg"

sabayon_pkgs_file="${CHROOT_DIR}/etc/sabayon-pkglist"
if [ -f "${sabayon_pkgs_file}" ]; then
	cp "${sabayon_pkgs_file}" "${CDROOT_DIR}/pkglist"
fi

