PREFIX = /usr
BINDIR = $(PREFIX)/bin
DESTDIR = 
LIBDIR = $(PREFIX)/lib
SYSCONFDIR = /etc

all:
	

clean:
	

install:
	mkdir -p $(DESTDIR)$(PREFIX)/share/molecule/examples/scripts
	install -m 644 scripts/*.{sh,py,bz2} $(DESTDIR)$(PREFIX)/share/molecule/examples/scripts/
	mkdir -p $(DESTDIR)$(PREFIX)/share/molecule/examples/specs/sabayon
	install -m 644 specs/*.spec $(DESTDIR)$(PREFIX)/share/molecule/examples/specs/
	install -m 644 specs/sabayon/* $(DESTDIR)$(PREFIX)/share/molecule/examples/specs/sabayon/
