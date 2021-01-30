#include <logger.h>

void printBuffer(logger_buff_t* buffer) {
    int n = 0;
    logger_buff_node_t* p;
    for (p = buffer->head; p != NULL; p = p->next) {
        printf("Buffer entry %d: Address=%p\tNext=%p\tPrev=%p\n",n,p,p->next,p->prev);
        n++;
    }

    return;
}

void* loggerMain(void* arg_logger) {
    /** CORE FUNCTIONALITY OF LOGGER IMPLEMENTED HERE.
     * Pass as argument to pthreads_create for multithreading.
     * Pass a logger constructed using loggerInit(). **/
    logger_t* logger = (logger_t*) arg_logger;
    while (1) {
        logger_buff_node_t* rec_node = loggerPull(logger->buffer);
        if (rec_node == NULL) {
            printf("NULL pointer received\n");
        }
        logger_msg_t rec_msg = rec_node->msg;

        printf("loggerMain:: CMD: %d\t PATH: %s\t MSG: %s\n", rec_msg.cmd, rec_msg.path, rec_msg.data);
        switch (rec_msg.cmd)
        {
        case LOG:;
            usleep(1000000);
            FILE* f = fopen(rec_msg.path, "a");
            if (f == NULL) {
                char msg[] = "loggerMain: Error opening provided path"; 
                printf("%s\n",msg);
                logStatus(logger, msg); 
            }
            else {
                printf("Writing \"%s\"\n", rec_msg.data);
                if (fprintf(f,"%s",rec_msg.data) < 0) {
                    char msg[] = "loggerMain: Error writing to provided path";
                    printf("%s\n", msg);
                    logStatus(logger,msg);
                }
            }
            fclose(f);
            break;
        case CLOSE:;
            /** FREE MEMORY HERE **/
            int* return_status = (int*) malloc(sizeof(int));
            *return_status = loggerDestroy(logger);
            return (void*) (return_status);
            break;
        default:
            break;
        
        loggerMsgNodeDestroy(rec_node); //destroy message after processing
        }
    }
}

//Constructors
logger_t* loggerCreate(uint16_t buffer_size) {
    /**Returns a configured logger struct to the buffer pointed to by logger
     * Calls buffer initialization and create a log file for status reports.
     * Use as parameter to pthreads_create for threaded logging **/

    //stat log initialization////////////////////////////
    char *stat_log_stem = "/logger_logs.txt"; //WARNING: ASSUME UNIX PATH SEPARATOER
    char *stat_log_root = "./logs";
    mkdir(stat_log_root, S_IRWXU | S_IRWXG | S_IROTH | S_IXOTH); 
    char *stat_log_path = (char*) malloc(strlen(stat_log_root)+strlen(stat_log_stem)+2); //MEMCHECK 4
    if (stat_log_path == NULL) {
        printf("ERROR ALLOCATING MEMORY FOR STAT LOG PATH IN LOGGER INITIALIZATION");
    }

    strcpy(stat_log_path,stat_log_root);
    strcat(stat_log_path,stat_log_stem);
    FILE* stat_log_file = fopen(stat_log_path, "a");
    if (stat_log_file == NULL) {
        printf("ERROR OPENING STAT LOG FILE REFERENCE");
    }
    
    //write current time and separator to file
    uint8_t timestring_size = 32;
    char sep[] = "-----------------------------------\n";
    char timestring[timestring_size];
    struct tm now;
    time_t rawtime = time(NULL);
    gmtime_r(&rawtime,&now);
    strftime(timestring, timestring_size,"\n%F %T %Z\n",&now);
    fprintf(stat_log_file,"%s", timestring);
    fprintf(stat_log_file,"%s", sep);
    /////////////////////////////////////////////////////////////////

    //Buffer initialization
    logger_buff_t* buffer = loggerBufferCreate(buffer_size); //returns pointer to buffer in allocated memory

    //once data members are allocated
    logger_t* logger = (logger_t*) malloc(sizeof(stat_log_file) + sizeof(stat_log_path)+sizeof(*buffer));
    logger->buffer = buffer;
    logger->stat_log_file = stat_log_file;
    logger->stat_log_path = stat_log_path;
    return logger; 
}

logger_buff_t* loggerBufferCreate(uint16_t max_size) {
    logger_buff_t* buffer = (logger_buff_t*) malloc(sizeof(logger_buff_t));
    pthread_mutex_init(&buffer->lock, NULL);
    pthread_cond_init(&buffer->cond_nonempty, NULL);
    pthread_cond_init(&buffer->cond_nonfull, NULL);
    buffer->max_buff_size = max_size;
    buffer->head = NULL;
    buffer->tail = NULL;
    buffer->occupancy = 0;

    return buffer;
}

logger_buff_node_t* loggerMsgNodeCreate(logger_cmd_t cmd, char* path, char* data, size_t data_size) {
    /** Given message parameters, first constructs a LoggerMessage structure followed by
     * a Logger Buffer Node structure **/

    //Building message on local heap
    logger_msg_t msg;
    msg.path = strdup(path); //strdup allocates memory that must be freed
    msg.data = strndup(data, data_size); //strdup allocates memory that must be freed
    msg.data_leng = data_size;
    msg.cmd = cmd;

    //copy msg data by-value into memory allocated for buffer node
    logger_buff_node_t* node = (logger_buff_node_t*) malloc(sizeof(logger_buff_node_t) + sizeof(msg));
    node->msg = msg;
    
    return node;
}

//Destructors
int loggerDestroy(logger_t* logger) {
    loggerBufferDestroy(logger->buffer);
    free(logger->stat_log_path);
    int f_status = fclose(logger->stat_log_file);

    return f_status;
}

int loggerBufferDestroy(logger_buff_t* buffer) {
    /** ASSUMES ONE MASTER PRODUCER THAT STOPS CALLING MUTEXES/CONDS AFTER CLOSE COMMAND IS SENT **/
    loggerFlush(buffer);
    pthread_cond_destroy(&buffer->cond_nonfull);
    pthread_cond_destroy(&buffer->cond_nonempty);
    pthread_mutex_destroy(&buffer->lock);
    free(buffer);

    return 0;
}

void loggerMsgNodeDestroy(logger_buff_node_t* node) {
    /** Destroys a buffer node and the encapsulated message **/
    if (node != NULL) {
        free(node->msg.path);
        free(node->msg.data);
        free(node);
    }
    return;
}

//Buffer functions
int loggerPush(logger_buff_t *buffer, logger_buff_node_t *new_node, bool hi_priority, bool blocking) {
    /** Add a node to the linked list buffer. If hi_priority is true, new_node is added at the tail of buffer. 
     *  Otherwise, new_node is appended at the head. If blocking is true, this function will block if the buffer
     * is full and will wait until space is available. Otherwise it immediately returns -1.**/

    int lock_status;
    if (blocking) {
        //block until mutex acquired
        printf("loggerPush:: waiting for lock\n");
        lock_status = pthread_mutex_lock(&buffer->lock);
    }
    else {
        //return if mutex is not immediately available
        lock_status = pthread_mutex_trylock(&buffer->lock);
        if (lock_status) {
            return lock_status;
        }
    }
    printf("loggerPush:: lock\n");

    if (lock_status == 0) { 
        if (buffer->occupancy >= buffer->max_buff_size) {
            if (blocking) {
                printf("loggerPush: waiting for cond_nonfull\n");
                pthread_cond_wait(&buffer->cond_nonfull,&buffer->lock);
                printf("loggerPush: cond_nonfull\n");
            } //if blocking set, wait for signal that space available
            else {
                pthread_mutex_unlock(&buffer->lock);
                return -1;
            } //otw release mutex and exit with -1
        } //wait or exit if buffer is full
        
        printf("loggerPush: buffer head: %p\n", buffer->head);
        if (buffer->head == NULL) {
            printf("loggerPush: adding initial element\n");
            //if the buffer is empty, add appropriately
            new_node->prev = NULL;
            new_node->next = NULL;
            buffer->head = new_node;
            buffer->tail = new_node;
        }
        else if (hi_priority) {
            // add node at tail
            printf("loggerPush: adding to tail\n");
            new_node->next = NULL;
            new_node->prev = buffer->tail;
            buffer->tail->next = new_node;
            buffer->tail = new_node;
        }
        else {
            //add node to head
            printf("loggerPush: adding to head\n");
            new_node->next = buffer->head; //current head is now second
            new_node->prev = NULL; //new node has nothing before
            buffer->head->prev = new_node; //old node points to new node
            buffer->head = new_node; //head points to new node
        }
    
        buffer->occupancy++;
        printBuffer(buffer);
        printf("Buffer occupancy after push: %d\n", buffer->occupancy);
        printf("loggerPush:: signal\n");
        pthread_cond_signal(&buffer->cond_nonempty);
        printf("loggerPush:: unlock\n");
        pthread_mutex_unlock(&buffer->lock); //IMPORTANT: Unlock mutex before signaling so waiting threads can acquire lock
    } //continue if mutex successfully locked

    return lock_status;
}

logger_buff_node_t* loggerPull(logger_buff_t* buffer) {
/** Returns pointer to last node in list. **/
    logger_buff_node_t* out;   

    int lock_status;
    printf("loggerPull:: waiting for lock\n");
    lock_status = pthread_mutex_lock(&buffer->lock); 
    printf("loggerPull:: lock\n");

    if (lock_status == 0) {
        printf("loggerPull: before occupancy read\n");
        if (buffer->occupancy <= 0) {
            printf("loggerPull:: waiting for cond_nonempty\n");
            pthread_cond_wait(&buffer->cond_nonempty, &buffer->lock);
            printf("loggerPull:: cond_nonempty\n");
        } //if the buffer is empty, block until the cond_nonempty signal to continue
        
        out = buffer->tail; //save address of just-pulled msg to free later
        printf("loggerPull:: after output assigned\n");
        if (buffer->tail->prev == NULL) {
            buffer->tail = NULL;
            buffer->head = NULL;
        } //if prev == NULL, then current node is only node in list.
        else {
            buffer->tail->prev->next = NULL; //previous node now links to NULL as end of buffer
            buffer->tail = buffer->tail->prev; //buffer tail now points to this node
        } //else there are more nodes in list. Update next-to-last node's pointers accordingly
        
        buffer->occupancy--;
        printBuffer(buffer);
        printf("Buffer occupancy after pull: %d\n", buffer->occupancy);
        printf("loggerPull:: signal\n");
        pthread_cond_signal(&buffer->cond_nonfull);
        printf("loggerPull:: unlock\n");
        pthread_mutex_unlock(&buffer->lock); //IMPORTANT: signal before unlocking mutex so waiting threads can acquire lock
        
        return out;
    } //continue on successful mutex lock
    else {
        return NULL; //otw return a NULL pointer
    }
    
}

int loggerFlush(logger_buff_t* buffer) {
    /** Destroys all messages currently in the buffer **/
    int lock_status;
    lock_status = pthread_mutex_lock(&buffer->lock);
    if (lock_status == 0) {
        if (buffer->occupancy <= 0) return 0;

        logger_buff_node_t* p = buffer->head;
        logger_buff_node_t* p_tmp;
        while (p != NULL) {
            p_tmp = p;
            p = p->next;
            loggerMsgNodeDestroy(p_tmp);
        }
        buffer->head = NULL;
        buffer->tail = NULL;
        buffer->occupancy = 0;
    
        return 0;
    }
    else {
        return lock_status;
    }
}

//Utility Functions
int logStatus(logger_t* logger, char* msg) {
    /** Utility function for internal status logging **/
    //Get timestamp
    uint8_t timestring_size = 32;
    char timestring[timestring_size];
    struct tm now;
    time_t rawtime = time(NULL);
    gmtime_r(&rawtime,&now);
    strftime(timestring, timestring_size,"\n%F %T %Z",&now);

    //write to file
    return fprintf(logger->stat_log_file,"%s: %s",timestring,msg);
}

void loggerClose(logger_t* logger, bool hi_priority, bool blocking) {
    loggerPush(logger->buffer,loggerMsgNodeCreate(CLOSE,"none","NaN",0),hi_priority, blocking);
    return;
}

int loggerLogMsg(logger_t* logger, char* msg, size_t msg_size, char* path, bool hi_priority) {
    /** Utility function meant to be called by producer.
     * Constructs a logger buffer node containing the passed data 
     * and places the node on the buffer queue  **/
    return loggerPush(logger->buffer,loggerMsgNodeCreate(LOG, path, msg, msg_size), hi_priority, 1);
}  

int loggerTryLogMsg(logger_t* logger, char* msg, size_t msg_size, char* path, bool hi_priority) {
    return loggerPush(logger->buffer,loggerMsgNodeCreate(LOG, path, msg, msg_size), hi_priority, 0);
}

