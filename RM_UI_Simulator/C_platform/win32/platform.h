//
// Created by Jessi on 2022/3/25.
//

#ifndef C_PLATFORM_PLATFORM_H
#define C_PLATFORM_PLATFORM_H
#include <stdint.h>

#define GRAPHIC_NAME_LENGTH 1  // 大疆使用长度为三的数组，为了节省名称管理器的内存，这里使用长度为1的数组。
#define WRITE_SPACE_LENGTH 64
#define PART 5510

int platform_init();

int draw_a_line(const uint8_t *graphic_name_array, int start_x, int start_y, int end_x, int end_y, int color_code, int line_width, int layer);

int draw_a_circle(const uint8_t *graphic_name_array, int centre_x, int centre_y, int radius, int color_code, int line_width, int layer);

int write_a_float(const uint8_t *graphic_name_array, int32_t number, int digits, int start_x, int start_y, int font_size, int color_code, int line_width, int layer);

int write_an_integer(const uint8_t *graphic_name_array, int number, int start_x, int start_y, int font_size, int color_code, int line_width, int layer);

int write_a_char(const uint8_t *graphic_name_array, int char_length, char * string, int start_x, int start_y, int font_size, int color_code, int line_width, int layer);

int draw_a_rectangular(const uint8_t *graphic_name_array, int start_x, int start_y, int end_x, int end_y, int color_code, int line_width, int layer);

int platform_finish();

int delete(const uint8_t * name);  // TODO: 若没有使用该名称，则不上传指令并返回-1
int get_a_not_used_graphic_name(uint8_t *write_space);  // 获取一个未使用的图形名称，如果成功，数组长度与{GRAPHIC_NAME_LENGTH}相同，若已没有空变量名则返回 0
int has_name(uint8_t * name);  // 判断是否已使用该名称

int get_formatted_variable(char * variable_name, char * write_space);  // 获取变量值，返回值若>0为格式化的字符长度。若值不存在，格式化后的文本为'None'
#endif //C_PLATFORM_PLATFORM_H
