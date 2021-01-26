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

//logger logic functions

//High level interface functions
void loggerInit(logger_t* logger, uint16_t buffer_size) {}
void logClose(logger_t* logger) {}
void logPriorityClose() {}
void logMsg(logger_t* logger, char* msg, uint16_t msg_size, char* abs_path) {}
