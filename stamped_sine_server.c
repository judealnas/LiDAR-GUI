#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <unistd.h>
#include <errno.h>
#include <signal.h>
#include <string.h>
#include <czmq.h>
#include "Threaded Logger/logger.h"
#include "TCP Handler/tcp_handler.h"

#define PI 3.14159265

#include <sys/socket.h>
#include <sys/types.h>
#include <sys/time.h>

#include <netinet/in.h>

#define HEADERSIZE 10
#define PORT 49417
#define TIME_STR_SIZE 27 //YYYY-mm-DD-HH-MM-SS-uuuuuu\0

uint8_t loop_stop = false; //quick and dirty global stop flag for input monitoring thread

void* userInputThread()
{
	char c;
	do
	{
		printf("Enter \'q\' or \'Q\' to quit\n");
		scanf(" %c ", &c);
	} while (c != 'q' && c != 'Q');

	loop_stop = true;
	return NULL;
}

size_t getTimeString(char* str_result, size_t str_size, char delim) 
{	/**
	Returns the current time (UTC) as a string of format
	YYYY-mm-dd-HH-MM-SS-UUUUUU where mm is the month number and UUUUUU are the microseconds of the epoch time
	**/

	struct timeval curr_time_tv;
	char time_str[str_size];
	char out_str[str_size];
	
	//get current time; tv provides sec and usec; tm used for strftime
	gettimeofday(&curr_time_tv, NULL); //get current time in timeval
	struct tm *curr_time_tm = gmtime(&(curr_time_tv.tv_sec)); //use sec of timeval to get struct tm

	//use tm to get timestamp string
	strftime(time_str, str_size, "%Y-%m-%d-%H-%M-%S",curr_time_tm);
	size_t true_size = snprintf(str_result, str_size, "%s-%06ld",time_str, curr_time_tv.tv_usec); //add microseconds fixed to 6-character width left-padded with zeroes
    
	//str_size is characters to write INCLUDING null terminator; if true_size == str_size, then resulting string was truncated; 
	//max of (str_size - 1) can be written
	if (true_size == str_size) true_size = str_size - 1; 
    
	//replace default '-' delimiter if needed
    if (delim != '-') 
	{
        char* ptr_found; //pointer to found substring
        while (1) 
		{
            ptr_found = strstr(str_result,"-"); //find substring
            if (ptr_found == NULL) 
			{
                break; //if NULL, then no occurences of "-" so done
            }
            else 
			{
                *ptr_found = delim; //otw replace found '-' with desired delimiter
            }
        }    
    }
    
    return true_size;
}

int main() 
{
	//print ZMQ version
	int major;
	int minor;
	int patch;


	/******** logging thread ********/
	logger_t* logger = loggerCreate(30);
	pthread_t logger_tid;
	pthread_create(&logger_tid, NULL, &loggerMain, logger);
	/*********************************/

	char server_message[50] = "You have reached the server!";

	/******* Creating TCP Handler Thread *******/
	// define the server address
	struct sockaddr_in server_address;
	server_address.sin_family = AF_INET; //TCP
	server_address.sin_port = htons(PORT); //define port
	server_address.sin_addr.s_addr = INADDR_ANY; //accept connection at any address available

	pthread_t tcp_handler_tid;
	tcp_handler_t* tcp_handler = tcpHandlerInit(server_address, 50);
	pthread_create(&tcp_handler_tid, NULL, &tcpHandlerMain, tcp_handler);
	/********************************************/

	/********* User input monitoring thread *******/
	// pthread_t ui_tid;
	// pthread_create(&ui_tid, NULL, &userInputThread, NULL);
	/**********************************************/

	while (tcp_handler->tcp_state != CONNECTED); //wait for tcp handler to make connection
	
	while (!loop_stop)  //loop to discard dead clients and wait for a reconnection 
	{			
		char time_str[TIME_STR_SIZE];
		int i = 0;
		useconds_t delay =10000; //1000 ms
		//printf("Entering loop...\n");
		while (!loop_stop)
		{
			//getTimeString(time_str, TIME_STR_SIZE, '_');
			
			//Transmitting epoch time instead
			struct timeval curr_time_tv; 
			gettimeofday(&curr_time_tv,NULL);
			sprintf
			(
				time_str,"%lu.%06lu", curr_time_tv.tv_sec, curr_time_tv.tv_usec
			);
			// printf("Got time string\n");

			double x;
			x = sin(i*PI/180.0);
			// printf("calculated sine\n");
			
			size_t msg_size = HEADERSIZE + 2 + TIME_STR_SIZE; 
			char msg[msg_size];
			snprintf(msg,msg_size,"%0*g_%s",HEADERSIZE, x, time_str);
			size_t true_msg_size = strlen(msg);
			// printf("built msg string\n");

			//standard socket send
			// printf("From stamped_sine_server: tcp_state = %d\n", tcp_handler->tcp_state);
			if (tcp_handler->tcp_state == CONNECTED)
			{
				printf("Sending write message to TCP Handler...\n");
				tcpHandlerWrite(tcp_handler, msg, true_msg_size, 0, false);
				printf("Sent write message to TCP Handler...\n");
			}
			else if (tcp_handler->tcp_state == ERROR)
			{
				// perror("4hgajdfs");
			}

			
			/* ssize_t send_status = send(client_socket, msg, true_msg_size, MSG_NOSIGNAL);
			if (send_status >= 0) 
			{
				if(send_status < true_msg_size) 
				{
					printf("Not all data sent\n");
				}
				else 
				{
					//printf("Message sent: %s\n",msg);
				}
			}
			else if (errno == EPIPE) 
			{
				printf("sending on dead socket. Breaking from loop.\n");
				break;
			}
			else 
			{
				perror("Error in send(): ");
				break;
			} */
			//printf("sent\n");

			if (tcp_handler->client_socket >= 0) //if handler has a valid client connection
			{
				size_t rec_size = 100;
				char received[rec_size];
				if (recv(tcp_handler->client_socket,received, rec_size, MSG_DONTWAIT) > 0) 
				{
					printf("Message received: %s\n", received);
					loggerSendLogMsg(logger,received,sizeof(received),"./server_logs.txt",0,false);
					printf("After log?\n");
					if (strcmp(received, "CLOSE") == 0) 
					{
						printf("Stop Command Received\n");
						loop_stop = true;
						break;
					}
				}
			}
			//printf("rec\n"); 

			i += 5;
			i = i % 360;

			usleep(delay);
		} // end while (!loop_stop)
	} // end while (1)

	/******* Closing logger thread *******/
	printf("Sending Logger Close\n");
	loggerSendCloseMsg(logger,0,true);
	printf("Waiting for Logger Close\n");
	pthread_join(logger_tid,NULL);
	printf("Destroying logger\n");
	loggerDestroy(logger);

	/******* Closing TCP thread *******/
	printf("Sending Logger Close\n");
	tcpHandlerClose(tcp_handler, 0, true);
	printf("Waiting for Logger Close\n");
	pthread_join(tcp_handler_tid,NULL);
	printf("Destroying logger\n");
	tcpHandlerDestroy(tcp_handler);

	/******* Closing UI thread *******/
	// pthread_join(ui_tid, NULL);
	
	printf("Exitted\n");
	return 0;
}
