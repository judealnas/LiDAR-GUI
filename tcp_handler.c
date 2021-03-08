#include "fifo.h"
#include <sys/socket.h>
#include <sys/types.h>
#include <string.h>

#include <netinet/in.h>
#include <netinet/tcp.h>

typedef struct TcpHandler {
    struct sockaddr_in server_address;  //address to place socket that listens for client connections
    pthread_mutex_t write_lock;        //mutex to signaling socket is ready for writing
    fifo_buffer_t* write_buffer;         //fifo buffer holding data to write
} tcp_handler_t;


tcp_handler_t* tcpHandlerInit(struct sockaddr_in server_address)
{   
    /*  Assumes [server_address] is already configured with the desired port, settings, etc.
        Instantiates the tcpHandler structure for access from main thread and handling thread */

    tcp_handler_t* tcpHandler = (tcp_handler_t*) malloc(sizeof(tcp_handler_t));
    tcpHandler->server_address = server_address;
    pthread_mutex_init(&tcpHandler->write_lock,NULL);
    pthread_mutex_lock(&tcpHandler->write_lock);   //immediately lock mutex; socket not read for write
    
    return tcpHandler;
}

int tcpHandlerMain(tcp_handler_t* tcpHandler)
 {
    int server_socket = socket(AF_INET, SOCK_STREAM, 0);
	if (server_socket  < 0) 
	{
		//If any error occurs with socket, stop tcpHandler.
        //TODO: stopping tcpHandler
            //1) permanent blocking
            //2) exit thread (must let parent know somehow)
	}

    // bind server socket to the address
	if (bind(server_socket, (struct sockaddr*) &tcpHandler->server_address, sizeof(tcpHandler->server_address)) < 0) 
	{
		perror("bind() call failed!");
		exit(1);
	}


    //listen for at most 1 connection
    if (listen(server_socket, 1) < 0) 
	{
		perror("listen() failed!");
		exit(1);
	}
    
    while (1) 
    {
        //wait for an incoming connection; create new client socket upon connection
        int client_socket;
        client_socket = accept(server_socket, NULL, NULL);
        if (client_socket < 0) 
        {
            perror("accept() failed");
            exit(1);
        }

        //TCP Keepalive configuration//////////////////////
        //enable TCP Keepalive
        uint8_t val = 1;
        setsockopt(client_socket, SOL_SOCKET, SO_KEEPALIVE,&val, sizeof(val));
        
        //set idle time in seconds before sending keepalive packets
        val = 30;
        setsockopt(client_socket, SOL_TCP, TCP_KEEPIDLE, &val, sizeof(val));
        
        //Set # of keepalive packets to send before declaring connection dead
        val = 5;
        setsockopt(client_socket, SOL_TCP, TCP_KEEPCNT, &val, sizeof(val));

        //Set time interval in seconds between keepalive packets
        val = 6;
        setsockopt(client_socket, SOL_TCP, TCP_KEEPCNT, &val, sizeof(val));
        /////////////////////////////////////////////////////
        
        while (1)
        {
            char* data = (char*)fifoPull(tcpHandler->write_buffer,1);

            int data_len = strlen(data);

            ssize_t send_status = send(client_socket, data, data_len, MSG_NOSIGNAL);
			if (send_status >= 0) 
			{
				if(send_status < data_len) 
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
			}

        }
    }
    
 
 }