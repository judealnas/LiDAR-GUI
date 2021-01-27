#include <pthread.h>
#include <stdint.h>
#include <stdbool.h>

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
