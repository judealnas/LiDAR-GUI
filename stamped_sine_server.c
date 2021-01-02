#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <unistd.h>
#include <errno.h>
#include <signal.h>
#include <pthread.h>

#define PI 3.14159265

#include <sys/socket.h>
#include <sys/types.h>
#include <sys/time.h>

#include <netinet/in.h>

#define HEADERSIZE 10
#define PORT 49417

int main() {
	char server_message[50] = "You have reached the server!";

	// create the server socket
	int server_socket = socket(AF_INET, SOCK_STREAM, 0);
	if (server_socket  < 0) {
		perror("socket() call failed!");
		exit(1);
	}

	// define the server address
	struct sockaddr_in server_address;
	server_address.sin_family = AF_INET; //TCP
	server_address.sin_port = htons(PORT); //define port
	server_address.sin_addr.s_addr = INADDR_ANY; //localhost

	// bind server socket to the address
	if (bind(server_socket, (struct sockaddr*) &server_address, sizeof(server_address)) < 0) {
		perror("bind() call failed!");
		exit(1);
	}
	
	
	if (listen(server_socket, 5) < 0) {
		perror("listen() failed!");
		exit(1);
	}
	
	while (1) { //loop to discard dead clients and wait for a reconnection
		printf("Waiting for client connection...\n");

		int client_socket;
		client_socket = accept(server_socket, NULL, NULL);
		if (client_socket < 0) {
			perror("accept() failed");
			exit(1);
		}

		//configure TCP keepalive to detect dead client
		uint8_t val = 1;
		setsockopt(client_socket, SOL_SOCKET, SO_KEEPALIVE,&val, sizeof(val));
		
		printf("Connection established\n");
		
		struct timeval *date;
		struct tm *timestamp;
		uint8_t loop_stop = 0;
		int i = 0;
		useconds_t delay = 500000; //500 ms
		printf("Entering loop...\n");
		while (!loop_stop)
		{
			double x;
			//char *payload;
			//payload = (double *) malloc(sizeof(char)*HEADERSIZE);
			char msg[10];
			char header[HEADERSIZE];
			//gettimeofday(date);
			//time_t *seconds = date->tv_sec;
			//long int usecs = date->tv_usec;
			//timestamp = gmtime(seconds); //get seconds from epoch
			//payload[0] = timestamp->tm_mon; 
			//payload[1] = timestamp->tm_mday;
			//payload[2] = timestamp->tm_hour;
			//payload[3] = timestamp->tm_min;
			//payload[4] = timestamp->tm_sec;
			//payload[5] = usecs;
			
			x = sin(i*PI/180.0);
			//payload[6] = x;
			sprintf(msg,"%-*f",HEADERSIZE, x);

			ssize_t send_status = send(client_socket, msg, sizeof(msg), MSG_NOSIGNAL);
			if (send_status >= 0) {
				if(send_status < HEADERSIZE) {
					printf("Not all data sent\n");
				}
				else {
					printf("Message sent\n");
				}
			}
			else if (errno == EPIPE) {
				printf("sending on dead socket. Breaking from loop.\n");
				close(client_socket);
				break;
			}
			else {
				perror("Error in send(): ");
				break;
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
