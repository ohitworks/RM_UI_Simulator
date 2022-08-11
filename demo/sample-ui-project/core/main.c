#include "data_tool.h"
#include "platform.h"
#include "circle_and_line.h"

#include <stdio.h>
#include <main.h>


cal_handel cal;


int main() {

    platform_init();

    circleLine_init();

    while (keep_running()) {
        circleLine_update();
    }

    printf("stop running");
    platform_finish();

    return 0;
}


int keep_running(void) {
    int ret = 0;
    return *get_integer("keep_running", &ret);
}


void circleLine_init() {

    // 声明为静态变量防止被释放
    static uint8_t circle_graph_name[GRAPHIC_NAME_LENGTH], line_graph_name[GRAPHIC_NAME_LENGTH];
    int degree;

    get_a_not_used_graphic_name(circle_graph_name);  // 获取一个没用过的图形名
    get_a_not_used_graphic_name(line_graph_name);
    degree = *get_integer("line degree", &degree);

    cal_init(&cal, circle_graph_name, line_graph_name,
             25, 40, 500, 500,
             degree, 0, 1, 4, 6);
}


void circleLine_update() {
    int degree;
    cal_change_degree(&cal, *get_integer("line degree", &degree));
}
