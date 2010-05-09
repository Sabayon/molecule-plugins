#!/bin/bash

echo "REMASTER INNER CHROOT SCRIPT AFTER"

# touch /etc/asound.state
touch /etc/asound.state

rm -f "/usr/share/applications/vmware-user.desktop"
rm -f "/etc/skel/Desktop/WorldOfGooDemo-world-of-goo-demo.desktop"

echo -5 | etc-update
mount -t proc proc /proc

eselect opengl set xorg-x11

env-update
/lib/rc/bin/rc-depend -u
equo database vacuum

# Generate openrc cache
/etc/init.d/savecache start
/etc/init.d/savecache zap

equo deptest --pretend
emaint --fix world

ldconfig
umount /proc

# EXPERIMENTAL, clean icon cache files
for file in `find /usr/share/icons -name "icon-theme.cache"`; do
	rm $file
done
