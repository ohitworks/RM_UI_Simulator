"""
UI 协议中的结构体
"""
import itertools


class GraphData:
    def __init__(self, graphic_name, operate_type, graphic_type, layer, color_code, start_angle, end_angle,
                 width, start_x, start_y, radius, end_x, end_y):
        self.graphic_name = graphic_name
        self.operate_type = operate_type
        self.graphic_type = graphic_type
        self.layer = layer
        self.color_code = color_code
        self.start_angle = start_angle
        self.end_angle = end_angle
        self.width = width
        self.start_x = start_x
        self.start_y = start_y
        self.radius = radius
        self.end_x = end_x
        self.end_y = end_y

    def __repr__(self):
        return "\n".join(itertools.chain([type(self).__name__ + "("],
                                         [f'graphic_name: "{self.graphic_name}"'],
                                         [i.ljust(12) + ": " + str(getattr(self, i)) for i in (
                                             'operate_type', 'graphic_type', 'layer', 'color_code', 'start_angle',
                                             'end_angle', 'width', 'start_x', 'start_y', "radius", "end_x", "end_y")]
                                         )) + ")"


def hex_str_to_bin_str(hex_code: str) -> str:
    mp = {"0": "0000",
          "1": "0001",
          "2": "0010",
          "3": "0011",
          "4": "0100",
          "5": "0101",
          "6": "0110",
          "7": "0111",
          "8": "1000",
          "9": "1001",
          "a": "1010",
          "b": "1011",
          "c": "1100",
          "d": "1101",
          "e": "1110",
          "f": "1111"}
    return "".join(mp[i] for i in hex_code)


def byte_to_graph_data(hex_code: str):
    if len(hex_code) > 30:
        raise ValueError
    hex_code = hex_code.ljust(30, " ")
    bin_code = hex_str_to_bin_str(hex_code)

    parts = []
    sta = 0
    for i in (24, 3, 3, 4, 4, 9, 9, 10, 11, 11, 10, 11, 11)[::-1]:
        parts.append(bin_code[sta: sta + i])
        sta += i

    name_code = parts[-1]
    name = "".join(chr(int(f"0b{i}", 2)) for i in (name_code[:8], name_code[8:16], name_code[16:24]))[::-1]

    operate_type = int(f"0b{parts[-2]}", 2)

    graphic_type = int(f"0b{parts[-3]}", 2)

    layer = int(f"0b{parts[-4]}", 2)

    color = int(f"0b{parts[-5]}", 2)

    start_angle = int(f"0b{parts[-6]}", 2)

    end_angle = int(f"0b{parts[-7]}", 2)

    width = int(f"0b{parts[-8]}", 2)

    start_x = int(f"0b{parts[-9]}", 2)

    start_y = int(f"0b{parts[-10]}", 2)

    radius = int(f"0b{parts[-11]}", 2)

    end_x = int(f"0b{parts[-12]}", 2)

    end_y = int(f"0b{parts[-13]}", 2)

    return GraphData(name, operate_type, graphic_type, layer, color, start_angle, end_angle,
                     width, start_x, start_y, radius, end_x, end_y)
