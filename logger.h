#include <pthread.h>
#include <stdint.h>
#include <stdbool.h>

typedef enum LoggerCommand {
    LOG,
    CLOSE
} logger_cmd_t;

typedef struct LoggerMessage {
    logger_cmd_t cmd;
    char *abs_path; //absolute path
    char *data;
    uint16_t data_size;
} logger_msg_t;

typedef struct LoggerBufferNode {
    logger_msg_t msg;
    struct LoggerBufferNode *next;
    struct LoggerBufferNode *prev;
} logger_buff_node_t;

typedef struct LoggerBuffer {
    pthread_mutex_t lock;
    pthread_cond_t cond_nonempty;
    pthread_cond_t cond_nonfull;
    uint16_t max_buff_size;
    uint16_t occupancy;
    logger_buff_node_t *head;
    logger_buff_node_t *tail;
} logger_buff_t;

typedef struct Logger {
    logger_buff_t buffer;  
    int status; //status
} logger_t; 

//linked list buffer functions
logger_buff_t loggerBufferInit(uint16_t);
void push(logger_buff_t *, logger_buff_node_t *, bool , bool);
logger_buff_node_t* pull(logger_buff_t* );
void flush(logger_buff_t *buffer);

//logger logic
void createMsg();

//High level utility functions exposed to producers
void loggerInit(logger_t *, uint16_t); //initialize Logger and return configured struct
void logClose(logger_t *);
int logMsg(logger_t *, char* , uint16_t , char*);