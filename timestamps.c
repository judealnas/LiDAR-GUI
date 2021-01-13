#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/types.h>
#include <time.h>
#include <sys/time.h>

struct timeval date;
struct tm *timestamp;

void getTimeString(char* str_result, size_t str_size, char delim) {
	struct timeval curr_time_tv;
	char time_str[str_size];
	char out_str[str_size];
	
	//get current time; tv provides sec and usec; tm used for strftime
	gettimeofday(&curr_time_tv, NULL); //get current time in timeval
	struct tm *curr_time_tm = gmtime(&(curr_time_tv.tv_sec)); //use sec of timeval to get struct tm

	//use tm to get timestamp string
	strftime(time_str, str_size, "%Y-%m-%d-%H-%M-%S",curr_time_tm);
	snprintf(str_result, str_size, "%s-%ld",time_str, curr_time_tv.tv_usec); //add microseconds
    
    //replace default '-' delimiter if needed
    if (delim != '-') {
        char* ptr_found; //pointer to found substring
        while (1) {
            ptr_found = strstr(str_result,"-"); //find substring
            if (ptr_found == NULL) {
                break; //if NULL, then no occurences of "-" so done
            }
            else {
                *ptr_found = delim; //otw replace found '-' with desired delimiter
            }
        }    
    }
    
    return;
}

int main(int argc, char *argv[]) {
    size_t s = atoi(argv[1]);
    size_t str_size = s;
    char out[str_size];

    //getTimeString(out,str_size, '-');
    struct timeval curr_time;
    gettimeofday(&curr_time, NULL);
    sprintf(out,"%*lu\.%*lu", sizeof(time_t), curr_time.tv_sec, 
                                sizeof(useconds_t), curr_time.tv_usec);

    printf("out: %s\n",out);
    printf("sizeof(out): %ld\n",sizeof(out));
    return 0;
}