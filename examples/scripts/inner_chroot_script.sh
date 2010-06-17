#!/bin/bash

/usr/sbin/env-update
source /etc/profile

for arg in $*; do
    [[ "${arg}" = "spinbase" ]] && SPINBASE="1"
done

# Setup locale to en_US
echo LANG=\"en_US.UTF-8\" > /etc/env.d/02locale
echo LANGUAGE=\"en_US.UTF-8\" >> /etc/env.d/02locale
echo LC_ALL=\"en_US.UTF-8\" >> /etc/env.d/02locale

# remove SSH keys
rm -rf /etc/ssh/*_key*

# allow root logins to the livecd by default

# turn bashlogin shells to actual login shells
sed -i 's:exec -l /bin/bash:exec -l /bin/bash -l:' /bin/bashlogin

# setup sudoers
[ -e /etc/sudoers ] && sed -i '/NOPASSWD: ALL/ s/^# //' /etc/sudoers

# setup opengl in /etc (if configured)
[[ -z "${SPINBASE}" ]] && eselect opengl set xorg-x11

# touch /etc/asound.state
touch /etc/asound.state

update-pciids
update-usbids

if [ -z "${SPINBASE}" ]; then
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

	rm -rf /var/lib/entropy/packages*/${mydir}/5/x11-drivers*
	ACCEPT_LICENSE="NVIDIA" equo install --fetch --nodeps =x11-drivers/nvidia-drivers-173*$kernel_tag
	ACCEPT_LICENSE="NVIDIA" equo install --fetch --nodeps =x11-drivers/nvidia-drivers-96*$kernel_tag
	# testing xorg-server-1.5 support
	# ACCEPT_LICENSE="NVIDIA" equo install --fetch --nodeps ~x11-drivers/nvidia-drivers-71.86.*$kernel_tag
	mv /var/lib/entropy/packages-nonfree/${mydir}/*/x11-drivers\:nvidia-drivers*.tbz2 /install-data/drivers/

	# Add fusion icon to desktop
	if [ -f "/usr/share/applications/fusion-icon.desktop" ]; then
		cp /usr/share/applications/fusion-icon.desktop /etc/skel/Desktop/
	fi
fi

# EXPERIMENTAL, clean icon cache files
for file in `find /usr/share/icons -name "icon-theme.cache"`; do
	rm $file
done

echo -5 | etc-update
mount -t proc proc /proc
/lib/rc/bin/rc-depend -u

echo "Vacuum cleaning client db"
equo rescue vacuum

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
[[ -z "${SPINBASE}" ]] && cp /var/lib/entropy/client/database/*/sabayonlinux.org/standard/*/*/make.conf /etc/make.conf

# Update sabayon overlay
layman -s sabayon
if [ -z "${SPINBASE}" ]; then
	layman -d sabayon
	rm -rf /var/lib/layman/sabayon
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

# Reset users' password
echo "sabayonuser:" | chpasswd
echo "root:" | chpasswd

# protect /var/tmp
touch /var/tmp/.keep
touch /tmp/.keep
chmod 777 /var/tmp
chmod 777 /tmp

# Looks like screen directories are missing
if [ ! -d "/var/run/screen" ]; then
	mkdir /var/run/screen
	chmod 775 /var/run/screen
	chown root:utmp /var/run/screen
fi

# Revert to blocked entropy repo URL
sed -i 's/pkgbuild.sabayon.org/pkg.sabayon.org/g' /etc/entropy/repositories.conf

# Tweak user groups
usermod -a -G lpadmin sabayonuser

# Regenerate Fluxbox menu
if [ -x "/usr/bin/fluxbox-generate_menu" ]; then
        fluxbox-generate_menu -o /etc/skel/.fluxbox/menu
fi

equo query list installed -qv > /etc/sabayon-pkglist
exit 0
