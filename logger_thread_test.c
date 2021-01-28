#include <logger.h>
#include <pthread.h>

int main() {
    logger_t* logger = loggerCreate(50);
    for (int i = 0; i < 6; i++) {
        char data[5];
        sprintf(data, "%d", i);
        logger_buff_node_t* msg = loggerMsgNodeCreate(LOG,"./test.txt",data,sizeof(data));
        push(logger->buffer, msg, 1, 1);
        logStatus(logger, "PUSHED");
    }
    
    printf("Buffer Occupancy: %d\n", logger->buffer->occupancy);

    for (int i = 0; i < 6; i++) {
        logger_buff_node_t* rec = pull(logger->buffer);
        printf("%s to %s\n",rec->msg.abs_path, rec->msg.data);
        logStatus(logger,"PULL");
        loggerMsgNodeDestroy(rec);
    }
    loggerDestroy(logger);
    return 0;
}