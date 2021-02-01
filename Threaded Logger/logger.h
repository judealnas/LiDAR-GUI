#include <pthread.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>
#include <time.h>
#include <fifo.h>

typedef enum LoggerCommand {
    LOG,
    CLOSE
} logger_cmd_t;

typedef struct LoggerMessage {
    logger_cmd_t cmd;
    uint16_t path_leng;
    uint16_t data_leng;
    char *path;
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

//CORE FUNCTION
void* loggerMain(void* logger);

//Constructor functions
logger_t* loggerCreate(uint16_t buffer_size);
logger_buff_t* loggerBufferCreate(uint16_t max_size);
logger_buff_node_t* loggerMsgNodeCreate(logger_cmd_t cmd, char* path, char* data, size_t data_size);

//Destructor functions
int loggerDestroy(logger_t* logger);
int loggerBufferDestroy(logger_buff_t* buffer);
void loggerMsgNodeDestroy(logger_buff_node_t* node);

//Buffer functions
int loggerPush(logger_buff_t *buffer, logger_buff_node_t *new_node, bool hi_priority, bool blocking);
int loggerTryPush(logger_buff_t *buffer, logger_buff_node_t *new_node, bool hi_priority);
logger_buff_node_t* loggerPull(logger_buff_t* buffer);
int loggerFlush(logger_buff_t* buffer);

//Utility functions
int logStatus(logger_t* logger, char* msg); //logs msg to Loggers status log file
void loggerClose(logger_t* logger, bool hi_priority, bool blocking);
int loggerLogMsg(logger_t* logger, char* msg_str, size_t msg_size, char* path, bool hi_prioirty);
int loggerTryLogMsg(logger_t* logger, char* msg_str, size_t msg_size, char* path, bool hi_prioirty);

