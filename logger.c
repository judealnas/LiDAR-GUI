#include <logger.h>

//logger buffer functions
logger_buff_t loggerBufferInit(uint16_t buff_size) {
    return;
}

void push(logger_buff_t *buffer, logger_buff_node_t *node) {
    node->next = buffer->head;
    buffer->head = node;
    return;
}


void pushPriority(logger_buff_t *buffer, logger_buff_node_t *node) {
    node->next = NULL;
    buffer->tail->next = node;
    buffer->tail = node;
    return;
}

logger_buff_node_t* pop() {}

//Mid level buffer interface
void tryPush(logger_t* logger, logger_buff_node_t* node) {
    pthread_mutex_lock(&logger->lock);
    if (logger->buffer.occupancy == logger->buffer.max_buff_size) {
        return -1;
    }
    else {

    }
}

//High level interface functions
void loggerInit(logger_t* logger, uint16_t buffer_size) {
    logger->buffer = loggerBufferInit(buffer_size);
}
void logClose(logger_t* logger) {}
void logPriorityClose() {}
int logMsg(logger_t* logger, char* msg, uint16_t msg_size, char* abs_path) {
    //Build logger message
    logger_msg_t logger_msg;
    logger_msg.cmd = LOG;
    logger_msg.abs_path = strdup(abs_path); //memcheck 1
    logger_msg.data = strdup(msg); //memcheck 2
    logger_msg.data_size = msg_size;
    
    //allocate buffer node and copy msg
    logger_buff_node_t* logger_node = (logger_buff_node_t*) calloc(sizeof(logger_buff_node_t)); //memcheck 3
    logger_node->msg = logger_msg;

}   