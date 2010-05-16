PREFIX = /usr
BINDIR = $(PREFIX)/bin
DESTDIR = 
LIBDIR = $(PREFIX)/lib
SYSCONFDIR = /etc

all:
	

clean:
	

install:
	mkdir -p $(DESTDIR)$(PREFIX)/share/molecule/examples
	install -m 644 *.{sh,py,bz2} $(DESTDIR)$(PREFIX)/share/molecule/examples/
	mkdir -p $(DESTDIR)$(PREFIX)/share/molecule/examples/specs
	install -m 644 specs/*.spec $(DESTDIR)$(PREFIX)/share/molecule/examples/specs/
