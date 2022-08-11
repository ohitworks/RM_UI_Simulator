/**
 *
 **/

#ifndef TEST_CIRCLE_AND_LINE_H
#define TEST_CIRCLE_AND_LINE_H

#include "stdint.h"

typedef struct {
    uint8_t *circle_graphics_name;
    uint8_t *line_graphics_name;
    uint16_t radius;  // 圆的半径
    uint16_t center_x;
    uint16_t center_y;
    uint8_t circle_colour_code;
    uint16_t length;  // 线的长度
    uint8_t line_colour_code;
    int degree;
    uint8_t width;
    uint8_t layer;
} cal_handel;


int cal_init(cal_handel *self, uint8_t *circle_graph_name, uint8_t *line_graph_name, uint16_t radius, uint16_t length,
             uint16_t center_x, uint16_t center_y, int degree, uint8_t circle_colour_code, uint8_t line_colour_code,
             uint8_t width, uint8_t layer);

int cal_change_degree(cal_handel *self, int degree);


#endif
