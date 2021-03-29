CC=gcc
CFLAGS= -O -g
OBJ= logger.o
LIBS = -lfifo -lpthread
INCLUDE = -I . 
FIFOATH = /home/jude/Projects/General-FIFO #point to directory containing libfifo.a
ARFLAGS= -rc

liblogger.a: logger.o 
	ar $(ARFLAGS) $@ $<
	
logger.o: logger.c logger.h
	gcc $(CFLAGS) -c logger.c $(INCLUDE) -L$(FIFOATH)

clean:
	rm -rf *.o *.a 