//
// Created by Jessi on 2022/3/25.
//

#include "platform.h"
#include <stdio.h>
#include <winsock2.h>
#include <math.h>

#define cmd_add_number(x) idx+=sprintf(&data[idx],"%d, ",x)

char data[WRITE_SPACE_LENGTH];

SOCKET client;
struct sockaddr_in addr;
WSADATA wsaData;

int platform_init() {
    WSAStartup(MAKEWORD(2, 1), &wsaData);
    if (client == INVALID_SOCKET) {
        printf("建立套接字失败");
        return -1;
    }
    addr.sin_family = AF_INET;
    addr.sin_addr.S_un.S_addr = inet_addr("127.0.0.1");
    addr.sin_port = htons(PART);
}

int platform_finish() {
    WSACleanup();
}

int send_message(char *cmd, int length) {
    client = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);

    if (connect(client, (struct sockaddr *) &addr, sizeof(addr)) == SOCKET_ERROR) {
        printf("send_message: 接听失败\n");
        closesocket(client);
        return -2;
    }

    send(client, cmd, length, 0);

    closesocket(client);

    return 0;
}


int send_and_read_message(char *cmd, int cmd_length, char *buf) {
    int success;

    if (client == INVALID_SOCKET) {
        printf("建立套接字失败");
        return -1;
    }
    addr.sin_family = AF_INET;
    addr.sin_addr.S_un.S_addr = inet_addr("127.0.0.1");
    addr.sin_port = htons(PART);

    client = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);

    if (connect(client, (struct sockaddr *) &addr, sizeof(addr)) == SOCKET_ERROR) {
        printf("send_and_read_message: 接听失败\n");
        closesocket(client);
        return -2;
    }

    send(client, cmd, cmd_length, 0);

    success = recv(client, buf, WRITE_SPACE_LENGTH, 0);

    closesocket(client);

    return success;
}

int write_colour(char *str, int color_code) {

    if (color_code == 0) {
        return sprintf(str, "%s", "red, ");
    } else if (color_code == 1) {
        return sprintf(str, "%s", "yellow, ");
    } else if (color_code == 2) {
        return sprintf(str, "%s", "green, ");
    } else if (color_code == 3) {
        return sprintf(str, "%s", "orange, ");
    } else if (color_code == 4) {
        return sprintf(str, "%s", "purple, ");
    } else if (color_code == 5) {
        return sprintf(str, "%s", "pink, ");
    } else if (color_code == 6) {
        return sprintf(str, "%s", "cyan, ");
    } else if (color_code == 7) {
        return sprintf(str, "%s", "black, ");
    } else if (color_code == 8) {
        return sprintf(str, "%s", "white, ");
    }

    return -1;
}

int get_a_not_used_graphic_name(uint8_t *write_space) {
    int idx = sprintf(data, "not_graphic_name(%d)", GRAPHIC_NAME_LENGTH);
    int len = send_and_read_message(data, idx, write_space);
    if (len == GRAPHIC_NAME_LENGTH && write_space[0] != '\0') {
        return 0;
    }
    return 1;
}

int has_name(uint8_t *name) {
    return -1;  // TODO: 还没写
}

int draw_a_line(const uint8_t *graphic_name_array, int start_x, int start_y, int end_x, int end_y,
                int color_code, int line_width, int layer) {
    int idx = 5;
    data[0] = 'l';
    data[1] = 'i';
    data[2] = 'n';
    data[3] = 'e';
    data[4] = '(';
    for (int i = 0; i < GRAPHIC_NAME_LENGTH; i++) {
        data[idx++] = graphic_name_array[i];
    }
    idx += sprintf(&data[idx], ", ");
    cmd_add_number(start_x);
    cmd_add_number(start_y);
    cmd_add_number(end_x);
    cmd_add_number(end_y);
    idx += write_colour(&data[idx], color_code);
    cmd_add_number(line_width);
    data[idx] = ')';
    idx += 1;
    return send_message(data, idx);
}

int
draw_a_rectangular(const uint8_t *graphic_name_array, int start_x, int start_y, int end_x, int end_y, int color_code,
                   int line_width, int layer) {
    int idx = sprintf(data, "rect(");
    for (int i = 0; i < GRAPHIC_NAME_LENGTH; i++) {
        data[idx++] = graphic_name_array[i];
    }
    idx += sprintf(&data[idx], ", ");
    cmd_add_number(start_x);
    cmd_add_number(start_y);
    cmd_add_number(end_x);
    cmd_add_number(end_y);
    idx += write_colour(&data[idx], color_code);
    cmd_add_number(line_width);
    data[idx] = ')';
    idx += 1;
    return send_message(data, idx);
}

int
draw_a_circle(const uint8_t *graphic_name_array, int centre_x, int centre_y, int radius, int color_code, int line_width,
              int layer) {
    int idx = 5;
    data[0] = 'c';
    data[1] = 'i';
    data[2] = 'r';
    data[3] = 'c';
    data[4] = '(';
    for (int i = 0; i < GRAPHIC_NAME_LENGTH; i++) {
        data[idx++] = graphic_name_array[i];
    }
    idx += sprintf(&data[idx], ", ");
    cmd_add_number(centre_x);
    cmd_add_number(centre_y);
    cmd_add_number(radius);
    idx += write_colour(&data[idx], color_code);
    cmd_add_number(line_width);
    data[idx] = ')';
    idx += 1;
    return send_message(data, idx);
}

int
write_a_float(const uint8_t *graphic_name_array, int32_t number, int digits, int start_x, int start_y, int font_size,
              int color_code, int line_width, int layer) {
    int idx = 0;
    idx = sprintf(data, "char(");
    for (int i = 0; i < GRAPHIC_NAME_LENGTH; i++) {
        data[idx++] = graphic_name_array[i];
    }
    idx += sprintf(&data[idx], ", ");
    digits = (number % 1000) / pow(10, 3 - digits);  // NOTE: 不知道为什么，如果把这段计算放到下面会得到错误的结果
    idx += sprintf(&data[idx], "%d.%d, ", number / 1000, digits);
    cmd_add_number(start_x);
    cmd_add_number(start_y);
    cmd_add_number(font_size);
    idx += write_colour(&data[idx], color_code);
    cmd_add_number(line_width);
    data[idx] = ')';
    idx += 1;
    return send_message(data, idx);
}

int
write_an_integer(const uint8_t *graphic_name_array, int number, int start_x, int start_y, int font_size, int color_code,
                 int line_width, int layer) {
    int idx = 0;
    idx = sprintf(data, "char(");
    for (int i = 0; i < GRAPHIC_NAME_LENGTH; i++) {
        data[idx++] = graphic_name_array[i];
    }
    idx += sprintf(&data[idx], ", ");
    idx += sprintf(&data[idx], "%d, ", number);
    cmd_add_number(start_x);
    cmd_add_number(start_y);
    cmd_add_number(font_size);
    idx += write_colour(&data[idx], color_code);
    cmd_add_number(line_width);
    data[idx] = ')';
    idx += 1;
    return send_message(data, idx);
}

int
write_a_char(const uint8_t *graphic_name_array, int char_length, char *string, int start_x, int start_y, int font_size,
             int color_code, int line_width, int layer) {
    int idx = 0;
    idx = sprintf(data, "char(");
    for (int i = 0; i < GRAPHIC_NAME_LENGTH; i++) {
        data[idx++] = graphic_name_array[i];
    }
    idx += sprintf(&data[idx], ", ");
    for (int i = 0; i < char_length; i++) {
        data[idx++] = string[i];
    }
    idx += sprintf(&data[idx], ", ");
    cmd_add_number(start_x);
    cmd_add_number(start_y);
    cmd_add_number(font_size);
    idx += write_colour(&data[idx], color_code);
    cmd_add_number(line_width);
    data[idx] = ')';
    idx += 1;
    return send_message(data, idx);
}

int delete(const uint8_t *name) {
    int idx = 4;
    data[0] = 'd';
    data[1] = 'e';
    data[2] = 'l';
    data[3] = '(';
    for (int i = 0; i < GRAPHIC_NAME_LENGTH; i++) {
        data[idx++] = name[i];
    }
    data[idx] = ')';
    idx += 1;
    return send_message(data, idx);
}

int get_formatted_variable(char *variable_name, char *write_space) {
    int idx = 4;
    data[0] = 'g';
    data[1] = 'e';
    data[2] = 't';
    data[3] = '(';
    idx += sprintf(&data[idx], "%s)", variable_name);
    return send_and_read_message(data, idx, write_space);
}
