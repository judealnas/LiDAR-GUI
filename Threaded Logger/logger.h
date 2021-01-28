#include <pthread.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>
#include <time.h>

typedef enum LoggerCommand {
    LOG,
    CLOSE
} logger_cmd_t;

typedef struct LoggerMessage {
    logger_cmd_t cmd;
    uint16_t path_leng;
    uint16_t data_leng;
    char *abs_path;
    char *data;
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
    logger_buff_t *buffer;
    char *stat_log_path;
    FILE *stat_log_file;  
} logger_t; 

logger_buff_node_t* loggerMsgNodeCreate(logger_cmd_t cmd, char* path, char* data, uint16_t data_size);
void loggerMsgNodeDestroy(logger_buff_node_t* node);
logger_buff_t* loggerBufferInit(uint16_t max_size);
int loggerBufferDestroy(logger_buff_t* buffer);
int push(logger_buff_t *buffer, logger_buff_node_t *new_node, bool hi_priority, bool blocking);
logger_buff_node_t* pull(logger_buff_t* buffer);
void flush(logger_buff_t* buffer);
int loggerDestroy(logger_t* logger);
int logStatus(logger_t* logger, char* msg);
void* loggerMain(void* logger);
logger_t* loggerCreate(uint16_t buffer_size);
void loggerClose(logger_t* logger, bool hi_priority, bool blocking);
int loggerMsg(logger_t* logger, char* msg, uint16_t msg_size, char* path, uint16_t path_size);
int loggerPriorityMsg(logger_t* logger, char* msg, uint16_t msg_size, char* path, uint16_t path_size);
