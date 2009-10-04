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

rm -rf /var/lib/entropy/packages/${mydir}/5/x11-drivers*
ACCEPT_LICENSE="NVIDIA" equo install --fetch --nodeps =x11-drivers/nvidia-drivers-173*
ACCEPT_LICENSE="NVIDIA" equo install --fetch --nodeps =x11-drivers/nvidia-drivers-96*
# dropped since no X 1.5 support yet
# ACCEPT_LICENSE="NVIDIA" equo install --fetch --nodeps ~x11-drivers/nvidia-drivers-71.86.07
mv /var/lib/entropy/packages/${mydir}/*/x11-drivers\:nvidia-drivers*.tbz2 /install-data/drivers/

# Add fusion icon to desktop
if [ -f "/usr/share/applications/fusion-icon.desktop" ]; then
	cp /usr/share/applications/fusion-icon.desktop /etc/skel/Desktop/
fi

# EXPERIMENTAL, clean icon cache files
for file in `find /usr/share/icons -name "icon-theme.cache"`; do
	rm $file
done

echo -5 | etc-update
mount -t proc proc /proc
/lib/rc/bin/rc-depend -u

echo "Vacuum cleaning client db"
equo database vacuum

# Generate openrc cache
/etc/init.d/savecache start
/etc/init.d/savecache zap

ldconfig
ldconfig
umount /proc

equo deptest --pretend
emaint --fix world

# remove anaconda .git
rm /opt/anaconda/.git -rf
rm /opt/anaconda/usr/share/anaconda/po/*.po -rf


# copy Portage config from sabayonlinux.org entropy repo to system
cp /var/lib/entropy/client/database/*/sabayonlinux.org/standard/*/*/package.mask /etc/portage/package.mask
cp /var/lib/entropy/client/database/*/sabayonlinux.org/standard/*/*/package.unmask /etc/portage/package.unmask
cp /var/lib/entropy/client/database/*/sabayonlinux.org/standard/*/*/package.use /etc/portage/package.use
cp /var/lib/entropy/client/database/*/sabayonlinux.org/standard/*/*/make.conf /etc/make.conf

# Update sabayon overlay
layman -s sabayon

# Optimize sabayon overlay
cd /usr/local/portage/layman/sabayon && git gc --aggressive \
	&& git repack -a -d -f --depth=250 --window=250 \
	&& git repack -ad && git prune

# if Sabayon GNOME, drop qt-gui bins
gnome_panel=$(qlist -ICve gnome-base/gnome-panel)
if [ -n "${gnome_panel}" ]; then
	find /usr/share/applications -name "*qt-gui*.desktop" | xargs rm
fi
# we don't want this on our ISO
rm -f /usr/share/applications/sandbox.desktop

# Remove wicd from autostart
rm -f /usr/share/autostart/wicd-tray.desktop /etc/xdg/autostart/wicd-tray.desktop
