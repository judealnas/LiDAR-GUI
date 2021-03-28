#include "fifo.h"
#include <unistd.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <string.h>

#include <netinet/in.h>
#include <netinet/tcp.h>


typedef enum TcpHandlerCMD {
    WRITE,
    DISCONNECT,
    CLOSE
} tcp_cmd_t;

typedef enum TcpHandlerState {
    UNCONNECTED,
    CONNECTED,
    ERROR
} tcp_state_t;

typedef struct TcpHandlerMsg {
    tcp_cmd_t CMD;
    char* data;
    size_t data_len;
} tcp_msg_t;

typedef struct TcpHandler {
    struct sockaddr_in server_address;  //address to place socket that listens for client connections
    tcp_state_t tcp_state;              //current state of the tcp_handler; check from producer to see if ready for writes
    fifo_buffer_t* write_buffer;        //fifo buffer holding data to write
} tcp_handler_t;

tcp_msg_t* tcpMsgCreate(tcp_cmd_t CMD, char* data, size_t data_len)
{
    tcp_msg_t* tcp_msg = (tcp_msg_t*) malloc(sizeof(tcp_msg_t));
    tcp_msg->CMD = CMD;
    tcp_msg->data_len = data_len;
    
    if (data != NULL)
    {
        //if valid data provided, duplicate into message struct (tcp_msg->data MUST BE FREED USING DESTRUCTOR)
        tcp_msg->data = strndup(data, data_len);
    }
    else
    {
        //OTW assign NULL pointer
        tcp_msg->data = NULL;
    }
    return tcp_msg;
} //end tcpMsgCreate()

void tcpMsgDestroy(tcp_msg_t* tcp_msg)
{
    free(tcp_msg->data);
    free(tcp_msg);

    return;
} //end tcpMsgDestroy()

int tcpConfigKeepalive(int socket, int idle_time_sec, int num_probes, int probe_intvl_sec)
{
    uint8_t val = 1;
    setsockopt(socket, SOL_SOCKET, SO_KEEPALIVE,&val, sizeof(val));
    
    //set idle time in seconds before sending keepalive packets
    setsockopt(socket, SOL_TCP, TCP_KEEPIDLE, &idle_time_sec, sizeof(idle_time_sec));
    
    //Set # of keepalive packets to send before declaring connection dead
    setsockopt(socket, SOL_TCP, TCP_KEEPCNT, &num_probes, sizeof(num_probes));

    //Set time interval in seconds between keepalive packets
    setsockopt(socket, SOL_TCP, TCP_KEEPCNT, &probe_intvl_sec, sizeof(probe_intvl_sec));
}

tcp_handler_t* tcpHandlerInit(struct sockaddr_in server_address, int max_buffer_size)
{   
    /*  Assumes [server_address] is already configured with the desired port, settings, etc.
        Instantiates the tcp_handler structure for access from main thread and handling thread */

    tcp_handler_t* tcp_handler = (tcp_handler_t*) malloc(sizeof(struct sockaddr_in) + sizeof(tcp_state_t) + sizeof(fifo_buffer_t*));
    tcp_handler->server_address = server_address;
    tcp_handler->tcp_state = UNCONNECTED;
    tcp_handler->write_buffer = fifoBufferInit(max_buffer_size);
    
    return tcp_handler;
} //end tcpHandlerInit()

tcp_msg_t** tcpHandlerDestroy(tcp_handler_t* tcp_handler) 
{   
    tcp_msg_t** leftover = (tcp_msg_t**)fifoBufferClose(tcp_handler->write_buffer);
    free(tcp_handler);
    return leftover; 
} //end tcpHandlerDestroy()

int tcpHandlerWrite(tcp_handler_t* tcp_handler, char* data, size_t data_len, int priority, bool blocking)
{
    void* msg = (void*)tcpMsgCreate(WRITE, data, data_len);
    return fifoPush(tcp_handler->write_buffer, msg, priority, blocking);
} //end tcpHandlerWrite()

int tcpHandlerClose(tcp_handler_t* tcp_handler, int priority, bool blocking)
{
    void* msg = (void*)tcpMsgCreate(CLOSE, NULL, 0);
    return fifoPush(tcp_handler->write_buffer, msg, priority, blocking);
} //end tcpHandlerWrite()

int tcpHandlerDisconnect(tcp_handler_t* tcp_handler, int priority, bool blocking)
{
    void* msg = (void*)tcpMsgCreate(DISCONNECT, NULL, 0);
    return fifoPush(tcp_handler->write_buffer, msg, priority, blocking);
} //end tcpHandlerDisconnect()


void* tcpHandlerMain(void* tcpHandler_void)
{
    //cast void argument to appropriate pointer type
    tcp_handler_t* tcp_handler = (tcp_handler_t*) tcpHandler_void;

    //create non-blocking server socket that listens for incoming client connections
    int server_socket = socket(AF_INET, SOCK_STREAM | SOCK_NONBLOCK, 0);
	if (server_socket  < 0) 
	{
		perror("socket() call failed!");
        return NULL;
	}
    printf("tcp_handler: server socket created\n");

    // bind server socket to the address
	if (bind(server_socket, (struct sockaddr*) &tcp_handler->server_address, sizeof(tcp_handler->server_address)) < 0) 
	{
		perror("bind() call failed!");
		return NULL;
	}
    printf("tcp_handler: binding\n");

    //listen for at most 1 connection
    if (listen(server_socket, 1) < 0) 
	{
		perror("listen() failed!");
		return NULL;
	}
    printf("tcp_handler: listneing\n");

    tcp_msg_t* recv_msg;
    while (1) 
    {
        switch (tcp_handler->tcp_state)
        {
            case UNCONNECTED:;
                /**This case performs non-blocking calls to accept, waiting for an incoming connection.
                 * accept() returns -1 with errno set to either EAGAIN or EWOULDBLOCK if there are no 
                 * connections pending. If accept() returns something non-zero, continue to socket configuration
                 * and transition to CONNECTED state. Otherwise, poll the command queue for 1 second before 
                 * calling accept again. 
                 */
                printf("tcp_handler: accepting\n");
                
                //Non-blocking call to accept
                int client_socket = accept(server_socket, NULL, NULL);
                if (client_socket < 0 && errno != EAGAIN && errno != EWOULDBLOCK) 
                {   
                    /* A true error occured here; exit */
                    perror("accept() failed");
                    tcp_handler->tcp_state = ERROR;
                    return NULL;
                }
                else if (client_socket >= 0) 
                {
                    /* A connection was made; configure socket and transition to CONNECTED state */
                    
                    //config TCP Keepalive
                    tcpConfigKeepalive(client_socket, 15, 5, 3);

                    //state transition
                    tcp_handler->tcp_state = CONNECTED;
                    break; //end case UNCONNECTED
                }

                /* This point is reached if no pending connections and no error from accept() */
                //poll the write_buffer for 1 second, 100 times spaced by 10 ms
                for(int i = 0; i < 100; i++)
                {
                    recv_msg = (tcp_msg_t*)fifoPull(tcp_handler->write_buffer, false);

                    if (recv_msg != NULL)
                    {
                        printf("accept: recv_msg = %d\n",recv_msg->CMD);
                        if(recv_msg->CMD == CLOSE)
                        {
                            close(server_socket);
                            return NULL;
                        } 
                    }
                    usleep(10000); //sleep for 10 ms
                }
                break;

            case CONNECTED:
            /**In the connected state, receive and execute commands from the buffer
             * until the CLOSE command is received or an error occurs
             * 
             */ 
                while (tcp_handler->tcp_state == CONNECTED)
                {
                    printf("tcpHandlerMain: waiting for CMD\n");
                    recv_msg = (tcp_msg_t*)fifoPull(tcp_handler->write_buffer,true);

                    //if NULL received from buffer, skip to beginning of next iteration
                    if (recv_msg == NULL) continue;

                    printf("tcp_handler: received %d\n", recv_msg->CMD);
                    switch(recv_msg->CMD)
                    {
                        case WRITE:;
                            printf("tcpHandlerMain: about to send\n");
                            ssize_t send_status = send(client_socket,recv_msg->data, recv_msg->data_len, MSG_NOSIGNAL);
                            printf("tcpHandlerMain: send_status=%ld\n", send_status);
                            if (send_status >= 0) //data successfully transmitted
                            {
                                if(send_status < recv_msg->data_len) 
                                {
                                    printf("Not all data sent\n");
                                }
                            }
                            else //else an eror occured, enter nested switch to handle error in errno 
                            {
                                switch(errno)
                                {
                                    case EPIPE: //EPIPE returned if client disconnected
                                        printf("sending on dead socket. Breaking from loop.\n");
                                        tcp_handler->tcp_state = UNCONNECTED;
                                        break;
                                    default: //exit for all unhandled errors
                                        perror("Error in send(): ");
                                        tcp_handler->tcp_state = ERROR;
                                        return NULL;
                                }
                            }
                            break;
                        case DISCONNECT:
                            close(client_socket);
                            printf("tcp_handler: DISCONNECT executed\n");
                            tcp_handler->tcp_state = UNCONNECTED;
                            break;
                        case CLOSE:
                            printf("tcp_handler: CLOSE executing\n");
                            close(client_socket);
                            printf("tcp_handler: closed client\n");
                            close(server_socket);
                            printf("tcp_handler: closed server\n");
                            return NULL;
                        default:
                            break;
                    } //end switch(recv_msg->CMD) in CONNECTED case
                    
                    tcpMsgDestroy(recv_msg);

                } //end while (tcp_handler->tcp_state == CONNECTED)
                break; // end case CONNECTEDs
        } //end switch(tcp_state)
    } //end while (1) [main loop]
} //end tcpHandlerMain()