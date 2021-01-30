#include "logger.h"

int main() {
    pthread_t logger_thread;
    logger_t* logger = loggerCreate(50);
    pthread_create(&logger_thread,NULL,&loggerMain,logger);
    printf("Logger Thread ID: %ld\n", logger_thread);
    double n = 0;
    for (int i = 1; i < 200; i++) {
        char msg[500];
        sprintf(msg,"%d\n", i);
        printf("\n\n\n\ntest:: msg=%s",msg);
        loggerLogMsg(logger,msg,sizeof(msg),"./test.txt",0);
        usleep(1);
    }
    
    printf("test:: sending close message\n");
    loggerClose(logger,0,1);
    pthread_join(logger_thread,NULL);
    return 0;
}