#include <logger.h>
#include <pthread.h>
#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>

int main() {
    pthread_t logger_thread;
    logger_t* logger = loggerCreate(50);
    printf("%s\n","here");
    pthread_create(&logger_thread,NULL,&loggerMain,logger);
    printf("%s\n","After create");
    loggerMsg(logger,"Hello World\n",sizeof("hello world\n"),"./test.txt",sizeof("./test.txt"));
    loggerClose(logger,0,1);
    pthread_join(logger_thread,NULL);
    return 0;
}