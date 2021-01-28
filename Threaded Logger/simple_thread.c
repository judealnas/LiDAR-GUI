#include <pthread.h>
#include <stdio.h>

void* function(void* arg) {
    char* str = (char*) arg;
    printf("%s",str);
    return 0;
}

int main() {
    pthread_t tid;
    char* string = "Hello World\n";
    pthread_create(&tid,NULL,&function,string);
    printf("%ld",tid);
    pthread_join(tid,NULL);
    return 0;
}
