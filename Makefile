CC=gcc
CFLAGS= -g -Wall -Wextra
LIBFLAGS= -lpigpio -lm -pthread 
DEPS=$(CURDIR)/Threaded-Logger/liblogger.a\
$(CURDIR)/Threaded-TCP/libtcphandler.a

CLEANDEPS=$(addsuffix .clean,$(DEPS))

%.out: $(DEPS)
	$(CC) $(CFLAGS) $(subst .out,.c,$@) $^ -o $@ $(addprefix -I,$(dir $(DEPS))) -I. $(LIBFLAGS)

$(DEPS):
	$(MAKE) -C $(@D) $(@F)

.PHONY: clean
clean: $(CLEANDEPS)
	rm -f *.o *.a
$(CLEANDEPS): %.clean:
	$(MAKE) -C $(*D) clean 
