#include <logger.h>
#include <stdio.h>
#include <string.h>

//logging logic functions

//logger buffer logic functions
logger_buff_t loggerBufferInit(uint16_t max_size) {
    logger_buff_t buffer;
    pthread_mutex_init(&buffer.lock, NULL);
    pthread_cond_init(&buffer.cond_nonempty, NULL);
    pthread_cond_init(&buffer.cond_nonfull, NULL);
    buffer.max_buff_size = max_size;
    buffer.head = NULL;
    buffer.tail = NULL;

    return buffer;
}

void push(logger_buff_t *buffer, logger_buff_node_t *node, bool hi_priority, bool blocking) {
    
    pthread_mutex_lock(&buffer->lock);
    if (blocking) {
        if (buffer->occupancy >= buffer->max_buff_size) {
            pthread_cond_wait(&buffer->lock, &buffer->cond_nonfull);
        } 
    } //if desired, block until space available in buffer
    else {
        if (hi_priority) {
            node->next = buffer->head;
            node->prev = NULL;
            buffer->head = node;
        }
        else {
            node->next = NULL;
            node->prev = buffer->tail;
            buffer->tail->next = node;
            buffer->tail = node;
        }
    }
    
    buffer->occupancy++;
    pthread_cond_signal(&buffer->cond_nonempty);
    
    return;
}


logger_buff_node_t* pull(logger_buff_t* buffer) {
/** Returns pointer to last element in list. **/
    logger_buff_node_t *out;   

    pthread_mutex_lock(&buffer->lock);
    if (buffer->occupancy <= 0) {
        pthread_cond_wait(&buffer->cond_nonempty, &buffer->lock);
    } //if the buffer is empty, block until the cond_nonempty signal to continue
    
    out = buffer->tail; //save output address
    if (buffer->tail->prev == NULL) {
        buffer->tail == NULL;
    } //if prev == NULL, then current node is only node in list.
    else {
        buffer->tail->prev->next = NULL; //previous node now links to NULL as end of buffer
        buffer->tail = buffer->tail->prev; //buffer tail now points to this node
    } //else there are more nodes in list. Update next-to-last node's pointers accordingly
    buffer->occupancy--;

    pthread_mutex_unlock(&buffer->lock);

    return out;
}

//Mid level buffer interface
void loggerTryPush(logger_t* logger, logger_buff_node_t* node) {
    pthread_mutex_lock(&logger->buffer.lock);
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

    //try and push to buffer; return depends on buffer capacity
}   