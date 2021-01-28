#include <logger.h>
#include <pthread.h>
#include <stdlib.h>
#include <stdio.h>

int main() {
    pthread_t logger_thread;
    logger_t* logger = loggerCreate(50);
    printf("%s","here");
    pthread_create(&logger_thread,NULL,&loggerMain,logger);
    loggerClose(logger,0,1);
    pthread_join(logger_thread,NULL);
    loggerDestroy(logger);
    return 0;
}