CC=gcc
LIBFLAGS= -lfifo -lm -pthread 
FIFOPATH=/home/jude/Projects/General-FIFO
LOGGERPATH=/home/jude/Projects/LiDAR-GUI/Threaded\ Logger
TCPPATH = /home/jude/Projects/LiDAR-GUI/TCP\ Handler

stamped_sine_server: 
	gcc $@.c tcp_handler.o logger.o -o $@.out -I$(LOGGERPATH) -L$(FIFOPATH) -I ./Threaded\ Logger $(LIBFLAGS)

clean_stamp:
	rm stamped_sine_server 

blah:
	gcc stamped_sine_server.c $(LOGGERPATH)/logger.c $(TCPPATH)/tcp_handler.c -o stamped_sine_server.out -I $(LOGGERPATH) -I .$(TCPPATH)  -L$(FIFOPATH) $(LIBFLAGS)