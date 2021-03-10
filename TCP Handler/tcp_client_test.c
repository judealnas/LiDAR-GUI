#include "tcp_handler.c"
#include <unistd.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <string.h>

#include <netinet/in.h>
#include <netinet/tcp.h>
#include <arpa/inet.h>

#define PORT 49217

int main() 
{   
    //Configure server socket that listens for incoming client connections
    struct sockaddr_in server_address;
    server_address.sin_family = AF_INET; //TCP
	server_address.sin_port = htons(PORT); //define port
    server_address.sin_addr.s_addr = inet_addr("127.0.0.1"); //reconfigure sockaddr_in for use by client; tcpHandleInit uses copy

    int server_socket = socket(AF_INET, SOCK_STREAM, 0);
    if(connect(server_socket, (struct sockaddr*) &server_address, sizeof(server_address)) < 0)
    {
        perror("connect()");
        return -1;
    }
    
    tcpConfigKeepalive(server_socket, 10, 5, 1);

    //print usage
    printf("c = Close client\n");
    printf("r = Receive data\n");
    
    char c;
    do
    {
        scanf("%c", &c);
        switch(c)
        {
            case 'c':
                printf("Closing socket and exiting\n");
                close(server_socket);
                break;
            case 'r':;
                char recv_buff[20];
                printf("recv return= %ld\n",recv(server_socket, recv_buff, sizeof(recv_buff), 0));
                printf("Received: \"%s\"\n", recv_buff);
                break;
            default:
                break;
        }    
    } while (c != 'c');
} //end main()