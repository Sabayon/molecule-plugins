#!/bin/bash

# do not remove these
/usr/sbin/env-update
source /etc/profile

eselect opengl set xorg-x11 &> /dev/null

# automatically start xdm
rc-update del xdm default
rc-update del xdm boot
rc-update add xdm boot

# consolekit must be run at boot level
rc-update add consolekit boot

rc-update del hald boot
rc-update del hald
rc-update add hald boot

rc-update del NetworkManager default
rc-update del NetworkManager
rc-update add NetworkManager default

rc-update del music boot
rc-update add music default

rc-update del sabayon-mce default
rc-update add sabayon-mce boot

rc-update add nfsmount default

remove_desktop_files() {
	rm /etc/skel/Desktop/WorldOfGooDemo-world-of-goo-demo.desktop
	rm /etc/skel/Desktop/fusion-icon.desktop
	rm /etc/skel/Desktop/xbmc.desktop
}

setup_sabayon_mce() {
	# Sabayon Media Center user setup
	source /sbin/sabayon-functions.sh
	sabayon_setup_live_user "sabayonmce"
}

if [ "$1" = "lxde" ]; then
	# Fix ~/.dmrc to have it load LXDE
	echo "[Desktop]" > /etc/skel/.dmrc
	echo "Session=LXDE" >> /etc/skel/.dmrc
	remove_desktop_files
	sed -i 's/DISPLAYMANAGER=".*"/DISPLAYMANAGER="gdm"/g' /etc/conf.d/xdm
	# properly tweak lxde autostart tweak, adding --desktop option
	sed -i 's/pcmanfm -d/pcmanfm -d --desktop/g' /etc/xdg/lxsession/LXDE/autostart
elif [ "$1" = "xfce" ]; then
	# Fix ~/.dmrc to have it load XFCE
	echo "[Desktop]" > /etc/skel/.dmrc
	echo "Session=xfce" >> /etc/skel/.dmrc
	remove_desktop_files
	sed -i 's/DISPLAYMANAGER=".*"/DISPLAYMANAGER="gdm"/g' /etc/conf.d/xdm
elif [ "$1" = "fluxbox" ]; then
	# Fix ~/.dmrc to have it load Fluxbox
	echo "[Desktop]" > /etc/skel/.dmrc
	echo "Session=fluxbox" >> /etc/skel/.dmrc
	remove_desktop_files
	sed -i 's/DISPLAYMANAGER=".*"/DISPLAYMANAGER="gdm"/g' /etc/conf.d/xdm
elif [ "$1" = "gnome" ]; then
	# Fix ~/.dmrc to have it load GNOME
	echo "[Desktop]" > /etc/skel/.dmrc
	echo "Session=gnome" >> /etc/skel/.dmrc
	SHIP_NVIDIA_LEGACY="1"
	rc-update del system-tools-backends boot
	rc-update add system-tools-backends default
	sed -i 's/DISPLAYMANAGER=".*"/DISPLAYMANAGER="gdm"/g' /etc/conf.d/xdm
	setup_sabayon_mce
elif [ "$1" = "kde" ]; then
	# Fix ~/.dmrc to have it load KDE
	echo "[Desktop]" > /etc/skel/.dmrc
	echo "Session=KDE-4" >> /etc/skel/.dmrc
	SHIP_NVIDIA_LEGACY="1"
	sed -i 's/DISPLAYMANAGER=".*"/DISPLAYMANAGER="kdm"/g' /etc/conf.d/xdm
	setup_sabayon_mce
fi

if [ -n "${SHIP_NVIDIA_LEGACY}" ]; then
	# Prepare NVIDIA legacy drivers infrastructure

	if [ ! -d "/install-data/drivers" ]; then
        	mkdir -p /install-data/drivers
	fi
	myuname=$(uname -m)
	mydir="x86"
	if [ "$myuname" == "x86_64" ]; then
        	mydir="amd64"
	fi
	kernel_tag="#$(equo query installed -qv sys-kernel/linux-sabayon | sort | head -n 1 | cut -d"-" -f 4 | sed 's/ //g')-sabayon"

	rm -rf /var/lib/entropy/client/packages/packages*/${mydir}/*/x11-drivers*
	ACCEPT_LICENSE="NVIDIA" equo install --fetch --nodeps =x11-drivers/nvidia-drivers-173*$kernel_tag
	ACCEPT_LICENSE="NVIDIA" equo install --fetch --nodeps =x11-drivers/nvidia-drivers-96*$kernel_tag
	# not working with >=xorg-server-1.5
	# ACCEPT_LICENSE="NVIDIA" equo install --fetch --nodeps ~x11-drivers/nvidia-drivers-71.86.*$kernel_tag
	mv /var/lib/entropy/client/packages/packages-nonfree/${mydir}/*/x11-drivers\:nvidia-drivers*.tbz2 /install-data/drivers/

	# Add fusion icon to desktop
	if [ -f "/usr/share/applications/fusion-icon.desktop" ]; then
		cp /usr/share/applications/fusion-icon.desktop /etc/skel/Desktop/
	fi
fi

# if Sabayon GNOME, drop qt-gui bins
gnome_panel=$(qlist -ICve gnome-base/gnome-panel)
if [ -n "${gnome_panel}" ]; then
        find /usr/share/applications -name "*qt-gui*.desktop" | xargs rm
fi
# we don't want this on our ISO
rm -f /usr/share/applications/sandbox.desktop

# Remove wicd from autostart
rm -f /usr/share/autostart/wicd-tray.desktop /etc/xdg/autostart/wicd-tray.desktop

# EXPERIMENTAL, clean icon cache files
for file in `find /usr/share/icons -name "icon-theme.cache"`; do
        rm $file
done

# Update package list
equo query list installed -qv > /etc/sabayon-pkglist

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


echo -5 | equo conf update
mount -t proc proc /proc
/lib/rc/bin/rc-depend -u

echo "Vacuum cleaning client db"
rm /var/lib/entropy/client/database/*/sabayonlinux.org -rf
equo rescue vacuum

# Generate openrc cache
/etc/init.d/savecache start
/etc/init.d/savecache zap

ldconfig
ldconfig
umount /proc

equo deptest --pretend
emaint --fix world

exit 0
