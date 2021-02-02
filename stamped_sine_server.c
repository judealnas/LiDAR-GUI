#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <unistd.h>
#include <errno.h>
#include <signal.h>
#include <string.h>
#include "logger.h"

#define PI 3.14159265

#include <sys/socket.h>
#include <sys/types.h>
#include <sys/time.h>

#include <netinet/in.h>

#define HEADERSIZE 10
#define PORT 49417
#define TIME_STR_SIZE 27 //YYYY-mm-DD-HH-MM-SS-uuuuuu\0

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
	char server_message[50] = "You have reached the server!";
	
	// create the listening server socket
	int server_socket = socket(AF_INET, SOCK_STREAM, 0);
	if (server_socket  < 0) 
	{
		perror("socket() call failed!");
		exit(1);
	}

	// define the server address
	struct sockaddr_in server_address;
	server_address.sin_family = AF_INET; //TCP
	server_address.sin_port = htons(PORT); //define port
	server_address.sin_addr.s_addr = INADDR_ANY; //accept connection at any address available

	// bind server socket to the address
	if (bind(server_socket, (struct sockaddr*) &server_address, sizeof(server_address)) < 0) 
	{
		perror("bind() call failed!");
		exit(1);
	}
	
	
	if (listen(server_socket, 5) < 0) 
	{
		perror("listen() failed!");
		exit(1);
	}
	
	while (1)  //loop to discard dead clients and wait for a reconnection 
	{
		printf("Waiting for client connection...\n");

		int client_socket;
		client_socket = accept(server_socket, NULL, NULL);
		if (client_socket < 0) 
		{
			perror("accept() failed");
			exit(1);
		}

		//configure TCP keepalive to detect dead client
		uint8_t val = 1;
		setsockopt(client_socket, SOL_SOCKET, SO_KEEPALIVE,&val, sizeof(val));
		
		printf("Connection established\n");
			
		char time_str[TIME_STR_SIZE];
		uint8_t loop_stop = 0;
		int i = 0;
		useconds_t delay =100000; //100 ms
		printf("Entering loop...\n");
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
			
			double x;
			x = sin(i*PI/180.0);

			size_t msg_size = HEADERSIZE + 1 + TIME_STR_SIZE; 
			char msg[msg_size];
			sprintf(msg,"%0*g_%s",HEADERSIZE, x, time_str);
			msg_size = strlen(msg);

			//send (msg_size - 1) bytes to omit string termination
			ssize_t send_status = send(client_socket, msg, msg_size, MSG_NOSIGNAL);
			if (send_status >= 0) 
			{
				if(send_status < msg_size) 
				{
					printf("Not all data sent\n");
				}
				else 
				{
					printf("Message sent: %s\n",msg);
				}
			}
			else if (errno == EPIPE) 
			{
				printf("sending on dead socket. Breaking from loop.\n");
				close(client_socket);
				break;
			}
			else 
			{
				perror("Error in send(): ");
				break;
			}

			size_t rec_size = 100;
			char received[rec_size];
			if (recv(client_socket,received, rec_size, MSG_DONTWAIT) > 0) {
				printf("Message received: %s", received);
			}

			i += 5;
			i = i % 360;

			usleep(delay);
		}	
	}
	
	close(server_socket);
	printf("Exitted");
	return 0;
}
