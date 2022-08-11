#include "platform.h"
#include <stdio.h>

#define cmd_add_number(x) sprintf(&data[idx],"%d, ",x)

int main() {
//    draw_a_line("0", 0, 0, 100, 300, 2, 2, 0);
//    printf("press to next"); getchar();
//    draw_a_circle("1", 120, 175, 30, 7, 8, 1);
//    printf("press to next"); getchar();
//    delete("0");
    char data[1500];
    int code = get_a_not_used_graphic_name(data);
    printf("code: %d\ndata: %s\n", code, data);
    return 0;
}
