#include <pthread.h>
#include <stdint.h>


typedef enum LoggerCommand {
    INIT,
    LOG,
    CLOSE
} logger_cmd_t;

typedef struct LoggerThread {
    pthread_mutex_t mutex;
    pthread_cond_t cond;
    int status; //status
    uint16_t buffer_size;
    char *buffer;
    int buffer_head; //addre

} logger_t; 

typedef struct LoggerMessage {
    LoggerCommand cmd;
    char *abs_path; //absolute path
    char *msg;
    uint16_t size;
} logger_msg_t;

logger_t* initLogger();
int loggerMain(logger_t *log_config);