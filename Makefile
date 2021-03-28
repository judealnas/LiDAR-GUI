CC=gcc
LIBFLAGS= -llogger -lfifo -lm -lpthread -lzmq
FIFOPATH=/home/jude/Projects/General-FIFO
LOGGERPATH=/home/jude/Projects/LiDAR-GUI/Threaded\ Logger

stamped_sine_server: stamped_sine_server.c
	gcc stamped_sine_server.c -o stamped_sine_server -L$(LOGGERPATH) -L$(FIFOPATH) -I ./Threaded\ Logger $(LIBFLAGS)

stamped_sine_server.c:

tcp_handler.c:
	gcc tcp_handler.c -c tcp_handler.o
clean_stamp:
	rm stamped_sine_server 