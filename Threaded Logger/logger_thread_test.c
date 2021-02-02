#include "logger.h"
#include <stdlib.h>

int main() {
    srand(time(NULL));
    pthread_t logger_thread;
    logger_t* logger = loggerCreate(50);
    pthread_create(&logger_thread,NULL,&loggerMain,logger);
    printf("Logger Thread ID: %ld\n", logger_thread);
    for (int i = 1; i < 10; i++) {
        char msg[500];
        sprintf(msg,"%d\n", i);

        static int max = 10;
        static int min = -2;
        int p = rand() % (max-min+1) + min;
        printf("\ntest:: msg=%s p=%d\n",msg,p);

        loggerSendLogMsg(logger,msg,sizeof(msg),"./test.txt",p,true);
    }
    
    printf("test:: sending close message\n");
    loggerSendCloseMsg(logger,0,1);
    pthread_join(logger_thread,NULL);
    return 0;
}