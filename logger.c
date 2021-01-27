#include <logger.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>
#include <time.h>

//logging logic functions

//logger buffer logic functions
logger_buff_t* loggerBufferInit(uint16_t max_size) {
    logger_buff_t* buffer = (logger_buff_t*) malloc(sizeof(logger_buff_t));
    pthread_mutex_init(&buffer->lock, NULL);
    pthread_cond_init(&buffer->cond_nonempty, NULL);
    pthread_cond_init(&buffer->cond_nonfull, NULL);
    buffer->max_buff_size = max_size;
    buffer->head = NULL;
    buffer->tail = NULL;

    return buffer;
}

int push(logger_buff_t *buffer, logger_buff_node_t *new_node, bool hi_priority, bool blocking) {
    /** Add a node to the linked list buffer. If hi_priority is true, new_node is added at the tail of buffer. 
     *  Otherwise, new_node is appended at the head. If blocking is true, this function will block if the buffer
     * is full and will wait until space is available. Otherwise it immediately returns -1.**/
    pthread_mutex_lock(&buffer->lock);
    if (buffer->occupancy >= buffer->max_buff_size) {
        if (blocking) {
            pthread_cond_wait(&buffer->lock, &buffer->cond_nonfull);
        }
        else {
            return -1;
        } 
    } //if desired, block until space available in buffer
    else {
        if (buffer->head == NULL) {
            //if the buffer is empty, add appropriately
            new_node->prev = NULL;
            new_node->next = NULL;
            buffer->head = new_node;
            buffer->tail = new_node;
        }
        else if (hi_priority) {
            // add node at tail
            new_node->next = NULL;
            new_node->prev = buffer->tail;
            buffer->tail->next = new_node;
            buffer->tail = new_node;
        }
        else {
            //add node to head
            new_node->next = buffer->head; //current head is now second
            new_node->prev = NULL; //new node has nothing before
            buffer->head->prev = new_node; //old node points to new node
            buffer->head = new_node; //head points to new node
        }
    }
    
    buffer->occupancy++;
    pthread_mutex_unlock(&buffer->lock); //IMPORTANT: Unlock mutex before signaling so waiting threads can acquire lock
    pthread_cond_signal(&buffer->cond_nonempty);
    
    return 0;
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
        buffer->head == NULL;
    } //if prev == NULL, then current node is only node in list.
    else {
        buffer->tail->prev->next = NULL; //previous node now links to NULL as end of buffer
        buffer->tail = buffer->tail->prev; //buffer tail now points to this node
    } //else there are more nodes in list. Update next-to-last node's pointers accordingly
    
    buffer->occupancy--;

    pthread_mutex_unlock(&buffer->lock); //IMPORTANT: Unlock mutex before signaling so waiting threads can acquire lock
    pthread_cond_signal(&buffer->cond_nonfull);

    return out;
}

int loggerMain(logger_t* logger) {
    int status;
    while (1) {
        logger_buff_node_t *rec_node = pull(&logger->buffer);
        logger_msg_t rec_msg = rec_node->msg;

        switch (rec_msg.cmd)
        {
        case LOG:
            FILE *f = fopen(rec_msg.abs_path, 'a');
            if (f == NULL) {
                //log error 
                
            }
            break;
        case CLOSE:
            /** FREE MEMORY HERE **/
            return;
            break;
        default:
            break;
        }
    }
}

//High level interface functions
void loggerInit(logger_t* logger, uint16_t buffer_size) {
    /**Returns a configured logger struct to the buffer pointed to by logger
     * Calls buffer initialization and create a log file for status reports **/
    
    //stat log initialization////////////////////////////
    char *stat_log_stem = "/logger_logs.txt"; //WARNING: ASSUME UNIX PATH SEPARATOER
    char *stat_log_root = "./logs";
    mkdir(stat_log_root, S_IRWXU | S_IRWXG | S_IROTH | S_IXOTH); 
    logger->stat_log_path = (char*) malloc(strlen(stat_log_root)+strlen(stat_log_stem)+); //MEMCHECK 4
    if (logger->stat_log_path == NULL) {
        printf("ERROR ALLOCATING MEMORY STAT LOG PATH IN LOGGER INITIALIZATION");
    }
    strcpy(logger->stat_log_path,stat_log_root);
    strcat(logger->stat_log_path,stat_log_stem);
    logger->stat_log_file = fopen(logger->stat_log_path, 'a');

    //write current time and separator to file
    char sep[] = '-----------------------------------\n';
    char timestring[32];
    struct tm now;
    time_t rawtime = time(NULL);
    gmtime_r(&rawtime,&now);
    strftime(timestring, 30,"%F %T\n",&now);
    fprintf(logger->stat_log_file,"%s", timestring);
    fprintf(logger->stat_log_file,"%s", sep);
    /////////////////////////////////////////////////////////////////

    //Buffer initialization
    logger->buffer = loggerBufferInit(buffer_size);
}

int logStatus(logger_t logger, char* msg, uint16_t msg_size) {

}
void loggerClose(logger_t* logger) {}
void loggerPriorityClose() {}
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