#include <logger.h>
#include <stdlib.h>

int main() {
    logger_t* logger = loggerCreate(5);
    for (int i = 0; i < 30; i++) {
        char data[5];
        sprintf(data, "%d", i);
        if(loggerSendLogMsg(logger->buffer, data,sizeof(data), "./test.txt",0,true) >= 0) {
            printf("Sent: %s\n", data);
        }
        else {
            printf("NO MESSAGE SENT\n");
        }
        if (((float)rand())/RAND_MAX < 0.3) {
            printf("PULLING\n");
            logger_msg_t* rec = loggerPull(logger->buffer);
            printf("Received: %s\n",rec->data);
        }
    }

    printf("Buffer Occupancy: %d\n", logger->buffer->buffer_occupancy);
    loggerDestroy(logger);
    return 0;
}