#define _GNU_SOURCE
#include "logger.h"
#include <stdlib.h>
#include <sched.h>

int main() {
    srand(time(NULL));
    pthread_t logger_thread;
    logger_t* logger = loggerCreate(50);
    
    cpu_set_t cpu_set;
    pthread_attr_t attr;
    pthread_attr_init(&attr);
    CPU_ZERO(&cpu_set);
    CPU_SET(0,&cpu_set);
    pthread_attr_setaffinity_np(&attr, sizeof(cpu_set),&cpu_set);

    CPU_ZERO(&cpu_set);
    CPU_SET(1,&cpu_set);
    pthread_setaffinity_np(pthread_self(), sizeof(cpu_set), &cpu_set);

    pthread_create(&logger_thread,&attr,&loggerMain,logger);
    printf("Logger Thread ID: %lX\n", logger_thread);
    printf("Main Thread ID: %lX\n", pthread_self());
    for (int i = 1; i < 100; i++) {
        char msg[50];
        sprintf(msg,"%d\n", i);

        static int max = 10;
        static int min = -2;
        int p = rand() % (max-min+1) + min;
        printf("\ntest:: msg=%s p=%d\n",msg,p);

        loggerSendLogMsg(logger,msg,sizeof(msg),"./test.txt",0,false);
        printf("message sent\n");

    }
    
    printf("test:: sending close message\n");
    loggerSendCloseMsg(logger,0,1);
    printf("test:: close message sent\n");
    //pthread_join(logger_thread,NULL);
    return 0;
}