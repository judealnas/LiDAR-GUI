#include <logger.h>
#include <stdlib.h>

int main() {
    logger_t* logger = loggerCreate(5);
    for (int i = 0; i < 30; i++) {
        char data[5];
        sprintf(data, "%d", i);
        logger_buff_node_t* msg = loggerMsgNodeCreate(LOG,"./test.txt",data,sizeof(data));
        if(loggerPush(logger->buffer, msg, 0, 0) >= 0) {
            printf("Sent: %s\n", data);
        }
        else {
            printf("NO MESSAGE SENT\n");
        }
        if (((float)rand())/RAND_MAX < 0.3) {
            printf("PULLING\n");
            logger_buff_node_t* rec = loggerPull(logger->buffer);
            printf("Received: %s\n",rec->msg.data);
        }
    }

    printf("Buffer Occupancy: %d\n", logger->buffer->occupancy);
    loggerDestroy(logger);
    return 0;
}