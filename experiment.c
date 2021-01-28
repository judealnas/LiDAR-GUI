#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <unistd.h>
//#include <sys/types.h>
#include <sys/stat.h>
#include <time.h>

int main() {
    char timestring[30];
    struct tm now;
    time_t rawtime = time(NULL);
    gmtime_r(&rawtime,&now);
    strftime(timestring, 30,"%F %T",&now);
    printf("%s", timestring);
    return 0;
}
