#include <pthread.h>
#include <stdint.h>
#include <stdbool.h>

typedef enum LoggerCommand {
    LOG,
    CLOSE
} logger_cmd_t;

typedef struct LoggerMessage {
    LoggerCommand cmd;
    char *abs_path; //absolute path
    char *data;
    uint16_t data_size;
} logger_msg_t;

typedef struct LoggerBufferNode {
    logger_msg_t msg;
    uint16_t msg_size;
    struct LoggerBufferNode *next;
} logger_buff_node_t;

typedef struct LoggerBuffer {
    uint16_t max_buff_size;
    uint16_t buff_size;
    logger_buff_node_t *head;
    logger_buff_node_t *tail;
} logger_buff_t;

typedef struct Logger {
    pthread_mutex_t prod_lock, cons_lock;
    pthread_cond_t cond;
    logger_buff_t buffer;  
    int status; //status
} logger_t; 

//linked list buffer functions
logger_buff_t* loggerBufferInit(uint16_t);
void push(logger_buff_t *, logger_buff_node_t *);
void pushPriority(logger_buff_t *, logger_buff_node_t *);
logger_buff_node_t* pop(logger_buff_t *buffer);
void flush(logger_buff_t *buffer);

//logger logic
void createMsg();

//High level utility functions exposed to producers
void loggerInit(logger_t *, uint16_t); //initialize Logger and return configured struct
void logClose(logger_t *);
void logMsg(logger_t *, char* , uint16_t , char*);