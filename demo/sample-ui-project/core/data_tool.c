/**
  **************************** sample_ui_project: data_tool.c ****************************
  * Created by Juntong on 2022/8/4.
  * @author     Juntong
  * @date       2022-08-04
  * @file       data_tool.c
  * @brief      **BriefHere**
  **************************** sample_ui_project: data_tool.c ****************************
 */

#include "data_tool.h"
#include "platform.h"

#include <iso646.h>
#include <string.h>
#include <stdlib.h>

char DATA_BUFFER[WRITE_SPACE_LENGTH];


int *get_integer(char *name, int *write_ptr) {

    /**
      *  @brief    向服务器获取名为 name 的整型变量, 并将转换后的结果写入 write_ptr 指向的地址
      *  @param name
      *            变量名称指针
      *  @param write_ptr
      *            写入地址
     **  @returns  当返回正常时返回 write_ptr, 不正确时返回 GET_NONE_PTR
     */

    char *end_ptr;
    int code;

    memset(DATA_BUFFER, 0, sizeof(DATA_BUFFER));  // 将缓冲区赋0
    code = get_formatted_variable(name, DATA_BUFFER);  // 调用 platform 库函数

    if (memcmp(DATA_BUFFER, "NONE", 5) == 0 or code <= 0) {
        // 收到了字符"NONE" (长度为5包括了结束符) 或者 获取值时错误
        return GET_NONE_PTR;
    }

    // 这里变量 code 被挪用做结果值暂存, 小朋友们(误)不要学我哦
    code = (int) strtol(DATA_BUFFER, &end_ptr, 10);

    if ((*end_ptr) != '\0') {
        // 发现数字结束位置不是文字结束处
        return GET_NONE_PTR;
    }

    // 确认返回值正确, 将数字写入结果地址
    * write_ptr = code;

    return write_ptr;

}

