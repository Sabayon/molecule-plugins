#!/bin/bash

# Use gdm by default
sed -i 's/DISPLAYMANAGER=".*"/DISPLAYMANAGER="gdm"/g' /etc/conf.d/xdm

# automatically start xdm
rc-update del xdm
rc-update add xdm boot
rc-update del hald
rc-update add hald default
rc-update del NetworkManager
rc-update add NetworkManager default

echo -5 | equo conf update

# remove stuff from Skel we don't have
rm /etc/skel/Desktop/WorldOfGooDemo-world-of-goo-demo.desktop
rm /etc/skel/Desktop/fusion-icon.desktop
rm /etc/skel/Desktop/xbmc.desktop

if [ "$1" = "lxde" ]; then
	# Fix ~/.dmrc to have it load LXDE
	echo "[Desktop]" > /etc/skel/.dmrc
	echo "Session=LXDE" >> /etc/skel/.dmrc
elif [ "$1" = "xfce" ]; then
	# Fix ~/.dmrc to have it load XFCE
	echo "[Desktop]" > /etc/skel/.dmrc
	echo "Session=xfce" >> /etc/skel/.dmrc
elif [ "$1" = "fluxbox" ]; then
	# Fix ~/.dmrc to have it load Fluxbox
	echo "[Desktop]" > /etc/skel/.dmrc
	echo "Session=fluxbox" >> /etc/skel/.dmrc
fi

# Update package list
equo query list installed -qv > /etc/sabayon-pkglist

# We installed feh and now use it to set a background!
echo "@feh --bg-scale /usr/share/backgrounds/sabayonlinux.png" >> /etc/xdg/lxsession/LXDE/autostart

rm /var/lib/entropy/client/database/*/sabayonlinux.org -rf
equo rescue vacuum

rm -rf /opt/anaconda*

# Setup basic GTK theme for root user
if [ ! -f "/root/.gtkrc-2.0" ]; then
	echo "include \"/usr/share/themes/Clearlooks/gtk-2.0/gtkrc\"" > /root/.gtkrc-2.0
fi

# Regenerate Fluxbox menu
if [ -x "/usr/bin/fluxbox-generate_menu" ]; then
	fluxbox-generate_menu -o /etc/skel/.fluxbox/menu
fi

layman -d sabayon
rm -rf /var/lib/layman/sabayon

exit 0
