#!/bin/bash

/usr/sbin/env-update
source /etc/profile

# allow root logins to the livecd by default

# turn bashlogin shells to actual login shells
sed -i 's:exec -l /bin/bash:exec -l /bin/bash -l:' /bin/bashlogin

# setup sudoers
[ -e /etc/sudoers ] && sed -i '/NOPASSWD: ALL/ s/^# //' /etc/sudoers

# setup opengl in /etc (if configured)
eselect opengl set xorg-x11

# touch /etc/asound.state
touch /etc/asound.state

update-pciids
update-usbids

# Prepare NVIDIA legacy drivers infrastructure

if [ ! -d "/install-data/drivers" ]; then
        mkdir -p /install-data/drivers
fi
myuname=$(uname -m)
mydir="x86"
if [ "$myuname" == "x86_64" ]; then
        mydir="amd64"
fi

ACCEPT_LICENSE="NVIDIA" equo install --fetch --nodeps =x11-drivers/nvidia-drivers-173*
ACCEPT_LICENSE="NVIDIA" equo install --fetch --nodeps =x11-drivers/nvidia-drivers-96*
# dropped since no X 1.5 support yet
# ACCEPT_LICENSE="NVIDIA" equo install --fetch --nodeps ~x11-drivers/nvidia-drivers-71.86.07
mv /var/lib/entropy/packages/${mydir}/4/x11-drivers\:nvidia-drivers*.tbz2 /install-data/drivers/

echo -5 | etc-update
/lib/rc/bin/rc-depend -u
