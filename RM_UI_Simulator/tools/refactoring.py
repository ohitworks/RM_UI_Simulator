"""
帮助重构UI
"""
import re
import array
import bisect
import typing

QUOTES = "'"'"'
re_get_include = re.compile(r'^ *#include +(?:"(.+\.h)"|<(.+\.h)>)$', flags=re.MULTILINE)
re_get_form_note = re.compile(r".*?// +!Form\W{0,2}(.*?) *$")
re_match_if_p = r"if *\(.+\)(?: *|( *{.*))$"
re_match_switch_p = r"switch *\(.+\)(?: *|( *{.*))$"


def load_file(path_or_fp, encoding=None):
    try:
        file_text = path_or_fp.read()
    except AttributeError:
        with open(path_or_fp, "r", encoding=encoding) as fp:
            file_text = fp.read()
    if not isinstance(file_text, str):
        raise ValueError("加载失败", file_text)
    return file_text


class LoadData:
    """
    用于分析 UI 表格绘制文件，可以对文件中的表格进行快速修改。
    一个文件绘制一个表格，表格的单元以 ".*?// +!Form\\W{0,2}(.*?) *$" 为开头，以其后第一个if或switch结构结束为结尾。

    注意：表格单元不可嵌套
    """

    def __init__(self, path: str, read_config=None):
        self.path = path
        self.file_text: str = ""
        self.file_lines: list[str] = []
        self.keys: dict[tuple[int]: str] = {}
        self.xys: dict[tuple[int]: dict[tuple[int]: list[str]]] = {}

        self.reload(read_config)
        self.analysis()

    def reload(self, read_config=None):
        if read_config is None:
            read_config = {}
        with open(self.path, "r", **read_config) as fp:
            self.file_text = fp.read()
        self.file_lines = self.file_text.splitlines()

    def analysis(self):
        """分析已加载的文件，会清空并重新填充self.keys 和 self.xys"""
        self.keys.clear()
        notes_to_write: list[int] = []

        it = iter(enumerate(self.file_lines, 1))  # 套 iter 是为了适配代码检查，运行时加不加都一样

        for num, line in it:
            m = re_get_form_note.match(line)
            if not m:
                continue
            notes_to_write.append(num)  # 找到了开头
            frame_text = m.group(1)
            while len(notes_to_write) == 1:
                m = re.match(r" *(?://)? *%s$" % re_match_if_p, line) or re.match(r" *%s$" % re_match_switch_p, line)
                if not m:
                    num, line = next(it)
                    continue
                # 匹配到了 if 或 switch
                if m.group(1):  # 说明该表达式有大括号结尾
                    numbers = 1
                    while numbers > 0:
                        num, line = next(it)
                        numbers += line.count("{")
                        numbers -= line.count("}")
                    notes_to_write.append(num)
                else:
                    next(it)
                    notes_to_write.append(num + 1)
                self.keys[tuple(notes_to_write)] = frame_text
                notes_to_write.clear()

        self.xys.clear()
        for x, y in self.keys.keys():
            ls = self.xys[(x, y)] = {}
            for index in range(x, y):
                line = self.file_lines[index].strip()
                line = re.sub("// ?", "", line)
                m = re.match(r"(?://)? *Char_Draw(.*)", line)
                if not m:
                    continue
                # 匹配到了
                string = ""
                cd_sta = index  # Char_Draw 起始行
                line = m.group(1)
                while 1:
                    if ";" in line:
                        # Char_Draw 函数只在着一行
                        string += line.split(";", 1)[0]
                        break
                    else:
                        string += line
                    index += 1
                    line = self.file_lines[index].strip()
                    line = re.sub("// ?", "", line)
                n = 0  # 括号数
                val = array.array("u")
                values = []
                for char in string:
                    if char == "(":
                        n += 1
                    elif char == ")":
                        n -= 1

                    if char == "," and n == 1:
                        # n == 1 说明是的Char_Draw的参数
                        values.append(val.tounicode().strip())
                        val = array.array("u")
                    elif not (n == 1 and char == "(" or char == ")"):  # elif 用于避免把Char_Draw参之间的逗号添加进来
                        # 说明不是是的Char_Draw对应的括号
                        val.append(char)
                if val:
                    values.append(val.tounicode().strip())
                ls[(cd_sta, index + 1)] = values

    def reverse_state(self, range_or_value, write_to_file=True, sep="\n"):
        if isinstance(range_or_value, str):
            (sta, end), *_ = [i for i, v in self.keys.items() if v.startswith(range_or_value)]
        else:
            sta, end = range_or_value
        for index in range(sta, end):
            sl = self.file_lines[index].strip()
            if not sl:
                continue
            if sl.startswith("//"):
                self.file_lines[index] = re.sub("// ?", "", self.file_lines[index])
            else:
                self.file_lines[index] = "// " + self.file_lines[index]
        if write_to_file:
            with open(self.path, "w", encoding="utf-8") as fp:
                fp.write(sep.join(self.file_lines))
            self.reload()

    def get_xy_from_note(self, note: str) -> list[tuple[int, int]]:
        """从描述中找到对应的表格选项起末坐标，用于 self.keys 和 self.xys 的索引"""
        return [i for i, v in self.keys.items() if v.startswith(note)]

    def get_data_frame(self):
        import pandas as pd
        ret = {}
        for k, v in self.xys.items():
            columns = ["image", "name", "operate", "layer", "colour", "size", "length", "width", "x", "y", "data"]
            data = list(v.values())
            df = pd.DataFrame(data, columns=columns)
            ret[k] = df
        return ret

    def show(self):
        ret = []
        for k, v in self.get_data_frame().items():
            ret.append(f"# {k}\n{v}\n")
        return "\n".join(ret)

    def _change_char_draw_value(self, key, main_key, new_value):
        sta, end = key
        if callable(new_value):
            if main_key is None:
                ls = [i[0] for i in self.keys]
                main_key = bisect.bisect_left(ls, sta) - 1
                main_key = [i for i in self.keys if i[0] == ls[main_key]][0]
            values = new_value(self.xys[main_key][key])
        else:
            values = new_value
        text_sta = self.file_lines[sta].split("Char_Draw", 1)[0]
        text_end = self.file_lines[end - 1].split(";", 1)[1]
        text_main = "Char_Draw(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)" % tuple(values)

        if end - 1 == sta:
            self.file_lines[sta] = text_sta + text_main + ";" + text_end
        else:
            self.file_lines[sta] = text_sta + text_main + ";"
            for index in range(sta + 1, end - 1):
                self.file_lines[index] = ""
            else:
                self.file_lines[end - 1] = re.match("( *(?://)? *)", self.file_lines[end - 1]).group(1) + text_end

    def change_char_draw_value(self, key: tuple[int, int],
                               new_value: typing.Union[
                                   typing.Iterable[str],
                                   typing.Callable],
                               sep="\n"):
        """
        替换 Char_Draw 的参数
        :param key:
        :param new_value: 如果为可调用对象，则传入原先Char_Draw的参数，返回值作为新的参数；否则将以new_value为新的Char_Draw参数
        :param sep: (str) 换行符
        :return:
        """
        if key in self.keys:
            # 说明要修改整个小表格的内容
            for k in self.xys[key].keys():
                self._change_char_draw_value(k, key, new_value)
        else:
            self._change_char_draw_value(key, None, new_value)
        with open(self.path, "w", encoding="utf-8") as fp:
            fp.write(sep.join(self.file_lines))
        self.reload()


if __name__ == "__main__":
    ld = LoadData(r"Infantry\Gimbal\application\UI_label.c")

    # ld.reverse_state((114, 132))  # 翻转代码注释状态

    def change(x):
        """将 "022" 替换为 "023" """
        ret = []
        for i in x:
            if i == '"022"':
                ret.append('"023"')
            else:
                ret.append(i)
        return ret


    # ld.change_char_draw_value((142, 143), change)

    print(ld.show())

    # def add_y_30(args: list):
    #     """将小于770的y值减小30"""
    #     ret = args.copy()
    #     ret[-2] = int(ret[-2])
    #     if ret[-2] < 770:
    #         ret[-2] += 30
    #     ret[-2] = str(ret[-2])
    #     return ret
    #
    # for k in ld.get_data_frame().keys():  # 应用全部
    #     ld.change_char_draw_value(k, add_y_30)
    #     ld.reload()
