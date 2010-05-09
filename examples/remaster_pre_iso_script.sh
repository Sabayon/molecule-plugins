#!/bin/sh

# Setup Gaming Edition string in ISOLINUX stuff
sed -i 's/5.1/5.1 Gaming/g' "${CDROOT_DIR}/isolinux/isolinux.cfg"
sed -i 's/5.1/5.1 Gaming/g' "${CDROOT_DIR}/isolinux/isolinux.txt"
