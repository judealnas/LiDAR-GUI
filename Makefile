CC=gcc
FIFOPATH=/home/jude/Projects/General-FIFO
LOGGERPATH=/home/jude/Projects/LiDAR-GUI/Threaded\ Logger

stamped_sine_server:
	gcc stamped_sine_server.c -o stamped_sine_server -L$(LOGGERPATH) -llogger -L$(FIFOPATH) -lfifo -I ./Threaded\ Logger -lm -lpthread