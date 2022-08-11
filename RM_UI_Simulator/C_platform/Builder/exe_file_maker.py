"""

"""
import os
import re
import sys
import random
import typing
import itertools
from collections import abc

from PyQt5 import QtWidgets, QtCore, QtGui

from .choose_files import Ui_ChooseFilesABC

PLATFORM_INCLUDE_DIR = os.path.dirname(os.path.dirname(__file__)).replace("\\", "/") + f"/{sys.platform}"
PLATFORM_LINK_FILES = ("w""sock32.lib",)
PLATFORM_SOURCE_FILES = (PLATFORM_INCLUDE_DIR + "/platform.c",)


def abspath(path, project_path: typing.Optional[str]):
    if os.path.isabs(path):
        path = path.replace("\\", "/")
        if " " in path:
            path = path.join('""')
        if project_path:
            m = re.match(f"^{project_path}/(.+)", path)
            if m:
                return m.group(1)
    return path.replace("\\", "/")


def make_cmake_text(inc_files, src_files, link_files, project_name,
                    c_compiler="", cxx_compiler="",
                    platform_link_files=PLATFORM_LINK_FILES,
                    platform_source=PLATFORM_SOURCE_FILES,
                    platform_include_dirs=(PLATFORM_INCLUDE_DIR,),
                    *, project_path: typing.Optional[str] = None) -> str:
    """生成 CMakeList.txt 的文本。
        若填充了 project_path, 则会简化inc_files, src_files路径
    """
    ls: list[str] = ["cmake_minimum_required(VERSION 3.21)"]

    if c_compiler:
        ls.append(f"SET(CMAKE_C_COMPILER {c_compiler})")

    if cxx_compiler:
        ls.append(f"SET(CMAKE_CXX_COMPILER {cxx_compiler})")

    ls.extend((f"project({project_name} C)",
               "set(CMAKE_C_STANDARD 99)",
               ""))

    if project_path:
        project_path = abspath(project_path, None)
        if project_path[-1] == "/":
            project_path = project_path[:-1]

    src_dirs = {}  # {文件夹: {文件名, ...}, ...}
    for i in itertools.chain(src_files, platform_source):
        dir_name, file_name = os.path.split(i)
        src_dirs.setdefault(dir_name, set()).add(file_name)
    # write_inc_dirs = {abspath(os.path.dirname(i), project_path) for i in inc_files} | set(platform_include_dirs)
    write_inc_dirs = {abspath(os.path.dirname(i), project_path) for i in inc_files} | set(platform_include_dirs)
    write_src_dirs = []
    src_vars = []
    write_src_files = []

    for d in src_dirs:
        d_path = d if os.path.isabs(d) else f"{project_path}/{d}"
        try:
            files = {i for i in os.listdir(d_path)}
        except FileNotFoundError as err:
            e = FileNotFoundError(*err.args)
            e.filename = d_path
            if any(i.startswith(d) for i in platform_source):
                e.strerror = err.strerror + "也许模拟器不兼容您的系统？"
                raise e
            else:
                e.strerror = err.strerror + "项目文件是否变更？"
                raise e
        if d and all(i.endswith(".c") for i in files) and files == src_dirs[d]:
            write_src_dirs.append(abspath(d, project_path))
        else:
            write_src_files.extend(abspath(d_path + "/" + i, project_path) for i in src_dirs[d])

    if write_inc_dirs:
        ls.append("include_directories(%s)" % " ".join(write_inc_dirs))

    for i, d in enumerate(write_src_dirs):
        v = f"DIR_SRCS_{i}"
        src_vars.append(v)
        ls.append(f'AUX_SOURCE_DIRECTORY({d} {v})')

    ls.append('add_executable(${PROJECT_NAME} ' + " ".join(i.join(("${", "}")) for i in src_vars) +
              " " + " ".join(write_src_files) + ")")

    if link_files or platform_link_files:
        ls.append("target_link_libraries(${PROJECT_NAME} %s)" %
                  " ".join(itertools.chain(link_files, platform_link_files)))

    return "\n".join(ls)


class MessageEventBase:
    text: str = ""
    facial_expression: str = ""
    sender: typing.Any = "initial"


class MessageEvent(MessageEventBase):
    """
    消息事件，用于方便地更新信息框。
    """
    facial_expressions = {"（*＾-＾*）", "(●'◡'●)", "o(*^＠^*)o", "(^人^)", "( ¯(∞)¯ )",
                          "（＾∀＾●）ﾉｼ ", "(๑•̀ㅂ•́)و✧", "＜（＾－＾）＞", "(╹ڡ╹ )", "(^^ゞ"}
    last: MessageEventBase = MessageEventBase()

    def __new__(cls, text: str, facial_expression: typing.Union[None, str, typing.Iterable[str]] = "", *,
                facial_expression_not: typing.Optional[set[str]] = None, sender="function"):
        """
                text: str 展示的信息
                facial_expressions: None or str or iterable 颜表情， None表示无表情， iterable将从中随机选择一个表情，
                                    ""将随机使用与上一个不同的表情，其他则使用该文本作为表情

                facial_expression_not: None or set 随机的颜表情不能是此集合中的表情，None表示上一个的表情
                sender: 消息的发送者。
                """
        self = object.__new__(cls)

        # initial
        if facial_expression == "":
            facial_expression = tuple(self.facial_expressions - {self.last.facial_expression})
        if isinstance(facial_expression, abc.Iterable):
            # 从所给的集合中抽取一个表情
            if not facial_expression_not:
                expressions = tuple(facial_expression)
            else:
                # 需要从表情集中去掉facial_expression_not内容
                expressions = set(facial_expression) - facial_expression_not
                if not expressions:
                    # 表情集为空
                    expressions = ("",)
                else:
                    expressions = tuple(expressions)
            # 随机抽取一个表情
            facial_expression = random.choice(expressions)
        elif facial_expression is None:
            facial_expression = ""

        self.text = text
        self.facial_expression = facial_expression
        self.sender = sender
        # finish initial

        self.last = cls.last
        cls.last = self

        return self

    def __str__(self):
        return f"{self.text}{self.facial_expression}"


class ChooseFilesABC(QtWidgets.QFrame, Ui_ChooseFilesABC):
    """
    用于生成 cmake信息的UI界面，是一个抽象基类，需要实现finish方法。
    """
    max_path_length = 45

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.setup_buttons()
        self.setup_edits()

        self.project_files_item_dict = {}
        self.project_files.setColumnCount(1)

        self.project_path: str = ""
        self.build_path: str = self.build_path_edit.text()  # 这么获取可以在仅修改 ui 界面时就改变默认界面
        self.cmake_path: str = self.cmake_path_edit.text()
        self.c_compiler_path: str = self.c_compiler_edit.text()
        self.cxx_compiler_path: str = self.cxx_compiler_edit.text()

        self.model = QtWidgets.QFileSystemModel()
        self.treeView.setModel(self.model)
        self.treeView.setColumnHidden(1, True)
        self.treeView.setColumnHidden(2, True)
        self.treeView.setColumnHidden(3, True)
        self.treeView.clicked.connect(self.tree_view_clicked)

        self.message.mouseReleaseEvent = self.message_event

    def clear_all(self):
        """
        清除所有已填加内容。
        """
        item: QtWidgets.QWidget
        # 删除以挂载的控件
        for item in self.project_files_item_dict.items():
            item.deleteLater()
        # 清空字典
        self.project_files_item_dict.clear()

    def add_project_file(self, dir_name, file_name):
        """在 self.project_files下某个目录添加一个文件
        dir_name == "." 表示在主目录下添加文件
        file_name 为相对 dir_name 的路径
        """
        name = "!" + dir_name + "/" + file_name
        if name in self.project_files_item_dict:
            raise KeyError("add_project_file got an existing path")
        if dir_name == ".":
            master = self.project_files
            parent = self.project_files.headerItem()
        else:
            master = parent = self.project_files_item_dict[dir_name]
        item = QtWidgets.QTreeWidgetItem(master)
        item.setText(0, file_name)
        parent.addChild(item)

        self.project_files_item_dict["!" + dir_name + "/" + file_name] = item

    def add_project_dir(self, dir_path):
        """在 self.project_files下某个目录添加一个文件夹
        注意 dir_path 应该是相对 self.project_path 的相对路径。
        """
        split = os.path.split(dir_path)
        if split[0]:
            try:
                self.add_project_dir(split[0])
            except KeyError:
                pass
        if dir_path in self.project_files_item_dict:
            raise KeyError("add_project_dir got an existing path")

        if split[0]:
            parent = master = self.project_files_item_dict[split[0]]
        else:
            master = self.project_files
            parent = self.project_files.headerItem()

        item = QtWidgets.QTreeWidgetItem(master)
        item.setText(0, split[1] + "/")
        parent.addChild(item)

        self.project_files_item_dict[dir_path] = item

    def remove_project_file(self, dir_path, file_name):
        name = "!" + dir_path + "/" + file_name
        item = self.project_files_item_dict[name]
        if dir_path == ".":
            idx = self.project_files.indexOfTopLevelItem(item)
            self.project_files.takeTopLevelItem(idx)
        else:
            item.parent().removeChild(item)
        self.project_files_item_dict.pop(name)

    def remove_project_dir(self, dir_path):
        item = self.project_files_item_dict[dir_path]

        idx = self.project_files.indexOfTopLevelItem(item)
        if idx < 0:  # 不在顶层
            item.parent().removeChild(item)
        else:
            self.project_files.takeTopLevelItem(idx)

        self.project_files_item_dict.pop(dir_path)
        for i in tuple(self.project_files_item_dict):
            if os.path.split(i)[0].endswith(dir_path):
                self.project_files_item_dict.pop(i)

    def message_event(self, event):
        """消息框事件

        """
        if isinstance(event, MessageEvent):
            self.message.setText(str(event))
        elif isinstance(event, QtGui.QMouseEvent):  # 是鼠标触发
            if event.button() != QtCore.Qt.LeftButton:  # 不是鼠标左键
                self.message_event(MessageEvent("想听听建议吗？请按鼠标左键！"))
                return
            notes = self.check()
            if notes["error(s)"]:
                self.message_event(MessageEvent("输入提示：" + notes["error(s)"][0][1] + "\n这是 error 哦",
                                                sender="error from click"))
            elif notes["warning(s)"]:
                self.message_event(
                    MessageEvent("input warning!" + notes["warning(s)"][0][1] + "\n听说程序员忽略warning",
                                 sender="warning from click"))
            else:
                # TODO: 说一些骚话
                self.message_event(MessageEvent("0 error(s), 0 warning(s)!\n"))
            return
        elif isinstance(event, str):  # 文本信息
            self.message_event(MessageEvent(event, None))

    def tree_view_clicked(self, index):
        info = self.model.fileInfo(index)
        # info.filePath 是完整路径
        if info.isDir():
            # 选择了一个文件夹
            name = os.path.relpath(info.filePath(), self.project_path).replace("\\", "/")
            try:
                self.add_project_dir(name)
                self.message_event(MessageEvent("将文件夹 %s 添加到了项目中" % os.path.basename(name)))
            except KeyError:
                self.remove_project_dir(name)
                self.message_event(MessageEvent("已将文件夹 %s 和它之内的内容移出项目" % os.path.basename(name)))
        else:
            # 选择了一个文件
            dir_path, name = os.path.split(info.filePath())
            dir_path = os.path.relpath(dir_path, self.project_path)
            try:
                self.add_project_file(dir_path, name)
                self.message_event(MessageEvent("将文件 %s 加入了项目" % os.path.basename(name)))
            except KeyError as err:
                if err.args[0] == "add_project_file got an existing path":
                    self.remove_project_file(dir_path, name)
                    self.message_event(MessageEvent("从项目中删除了文件 %s" % os.path.basename(name)))
                else:
                    self.add_project_dir(dir_path)
                    self.add_project_file(dir_path, name)
                    self.message_event(
                        MessageEvent("将文件 %s 和其父目录 %s 加入了项目" % (
                            os.path.basename(dir_path), os.path.basename(name))))

    def get_update_str(self, path: str, replace=True):
        """获取更新的路径文本。用于将输入的路径格式化为适合显示的样式。"""
        if replace:
            if self.project_path:
                path = path.replace(self.project_path, "{PROJECT_PATH}")
        if len(path) > self.max_path_length:  # XXX: 未考虑将{PROJECT_PATH}切开的情况
            path = path[-self.max_path_length + 4:].split("/", 1)
            if len(path) == 2:
                path = path[1]
            else:
                path = path[0]
            path = ".../" + path
        return path

    def change_project_path(self, path):
        """
        切换项目所在地址。
        """
        if os.path.exists(path):
            if not os.path.isdir(path):
                raise NotADirectoryError("请选择一个文件夹")
        else:
            raise ValueError("未找到文件夹")
        if self.project_path != path:
            if not self.project_path:  # 相当于一个初始化的过程。
                self.project_files.headerItem().setText(0, os.path.split(path)[-1] + "/")
                self.project_files.setHeaderHidden(False)
                self.project_files.header().setVisible(True)
                self.message_event(MessageEvent("刚刚更新了项目位置！从左边的目录树中点击文件添加到项目里吧"))
            else:
                self.message_event(MessageEvent("项目位置更新了！原来添加的文件被清除了，来项目文件吧"))  # FIXME: 提示语有误
            # 删除已添加的文件
            for key in tuple(self.project_files_item_dict.keys()):
                if key[0] != "!":
                    try:
                        self.remove_project_dir(key)
                    except KeyError:
                        pass
            self.project_path = path
            self.model.setRootPath(path)
            self.treeView.setRootIndex(self.model.index(path))
            path = self.get_update_str(path, replace=False)
            self.project_path_lable.setText(path)

    def change_cmake_path(self, new: str):
        """
        修改 cmake 路径后，根据输入更新
        """
        self.cmake_path = new
        new = self.get_update_str(new)
        if self.cmake_path_edit.text() != new:
            self.cmake_path_edit.setText(new)
        self.message_event(MessageEvent("更新了 CMake 路径！"))

    def change_build_path(self, new: str):
        """
        修改 build 路径后，根据输入更新
        """
        self.build_path = new
        new = self.get_update_str(new)
        if self.build_path_edit.text() != new:
            self.build_path_edit.setText(new)
        self.message_event(MessageEvent("更新了生成位置"))

    def change_c_compiler_path(self, new: str):
        """修改C编译器路径"""
        if new:  # 可以为空，让CMake自己选择
            self.c_compiler_path = new
            new = self.get_update_str(new)
            if self.c_compiler_edit.text() != new:
                self.c_compiler_edit.setText(new)
        else:
            self.c_compiler_edit.clear()
            self.c_compiler_path = new
        self.message_event(MessageEvent("更新了C语言编译器路径！"))

    def change_cxx_compiler_path(self, new: str):
        """修改CXX编译器路径"""
        if new:  # 可以为空，让CMake自己选择
            self.cxx_compiler_path = new
            new = self.get_update_str(new)
            if self.cxx_compiler_edit.text() != new:
                self.cxx_compiler_edit.setText(new)
        else:
            self.cxx_compiler_edit.clear()
            self.cxx_compiler_path = new
        self.message_event(MessageEvent("更新了CXX编译器路径！"))

    def choose_c_compiler_path(self):
        """点击C编译器对应的修改按钮时触发"""
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "选择C编译器位置", "C:/Program Files")
        if path:
            self.change_c_compiler_path(path)

    def choose_cxx_compiler_path(self):
        """点击CXX编译器对应的修改按钮时触发"""
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "选择CXX编译器位置", "C:/Program Files")
        if path:
            self.change_cxx_compiler_path(path)

    def choose_project_path(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "选择项目所在文件夹")
        if path:
            self.change_project_path(path)

    def choose_cmake_path(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "选择CMake位置", "C:/Program Files")
        if path:
            self.change_cmake_path(path)

    def choose_build_path(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "选择构建文件夹", self.project_path)
        if path:
            self.change_build_path(path)

    def setup_buttons(self):
        self.project_path_button.clicked.connect(self.choose_project_path)
        self.build_path_button.clicked.connect(self.choose_build_path)
        self.cmake_path_button.clicked.connect(self.choose_cmake_path)
        self.c_compiler_button.clicked.connect(self.choose_c_compiler_path)
        self.cxx_compiler_button.clicked.connect(self.choose_cxx_compiler_path)
        self.confirm.clicked.connect(self.confirm_func)
        self.cancel.clicked.connect(self.cancel_func)

    def edit_build_path_finished(self):
        path = self.build_path_edit.text()
        self.change_build_path(path)

    def edit_cmake_path_finished(self):
        path = self.cmake_path_edit.text()
        self.change_cmake_path(path)

    def edit_c_compiler_path_finished(self):
        path = self.c_compiler_edit.text()
        self.change_c_compiler_path(path)

    def edit_cxx_compiler_path_finished(self):
        path = self.cxx_compiler_edit.text()
        self.change_cxx_compiler_path(path)

    def setup_edits(self):
        self.build_path_edit.editingFinished.connect(self.edit_build_path_finished)
        self.cmake_path_edit.editingFinished.connect(self.edit_cmake_path_finished)
        self.c_compiler_edit.editingFinished.connect(self.edit_c_compiler_path_finished)
        self.cxx_compiler_edit.editingFinished.connect(self.edit_cxx_compiler_path_finished)

    def check_project_name(self) -> dict:
        """检查项目名称输入是否正确"""
        project_name = self.project_name.text()
        if len(project_name) < 1:
            return {"error(s)": ["请输入项目名称"]}
        if re.search(r"[^\w_\-]", project_name):  # 正则表达式中括号内^后面的内容表示“名称可以有的字符”
            return {"error(s)": ["项目名称不能有空格或特殊字符"]}
        return {}

    def check_project_path(self) -> dict:
        """检查项目位置输入是否正确"""
        project_path = self.project_path
        if len(project_path) < 1:
            return {"error(s)": ["请选择项目位置"]}
        return {}

    def get_real_path(self, path: str):
        """将路径转化为真实的完整路径"""
        path = path.format_map({"PROJECT_PATH": self.project_path})
        return os.path.realpath(path.replace("\\", "/"))

    def check_build_path(self) -> dict:
        """检查项目构建路径是否正确"""
        path = self.build_path
        if len(path) < 1:
            return {"error(s)": ["请输入构建路径"]}
        if not os.path.isdir(os.path.dirname(self.get_real_path(path))):
            return {"error(s)": ["项目构建路径有误？其父目录不存在。"]}
        return {}

    def check_cmake_path(self) -> dict:
        """检查CMake路径是否正确"""
        if len(self.cmake_path) < 1:
            return {"error(s)": ["请输入CMake路径"]}
        return {}

    def check_project_files(self) -> dict:
        if not self.project_files_item_dict:
            return {"error(s)": ["请点击左侧的目录树中的文件，将其加入项目"]}
        return {}

    def confirm_func(self):
        """结束输入按钮"""
        if self.check()["error(s)"]:
            self.message_event(
                MessageEvent("输入有错误，不能退出！(T_T)\n点我来获取帮助", None, sender="error from confirm"))
        else:
            self.finish(True)

    def cancel_func(self):
        """取消按钮"""
        self.finish(False)

    def check(self) -> dict[str: list[tuple[str, str]]]:
        """
        检查填充内容是否正确
        :return: dict["error(s)": list[tuple[str, str]]
                      "warning(s)": list[tuple[str, str]]]
        list[tuple[str, str]] 顺序是按照界面输入框位置从上到下, tuple 内为(XX错误, 错误内容)。
        """
        ret = {"error(s)": [], "warning(s)": []}

        def update_ret(t, d):
            for error in d.get("error(s)", []):
                ret["error(s)"].append((t, error))
            for warning in d.get("warning(s)", []):
                ret["warning(s)"].append((t, warning))

        update_ret("项目名称", self.check_project_name())
        update_ret("项目位置", self.check_project_path())
        update_ret("项目文件", self.check_project_files())
        update_ret("构建位置", self.check_build_path())
        update_ret("CMake位置", self.check_cmake_path())

        return ret

    def finish(self, finished: bool):
        """
        结束填充时执行的动作。
        :param finished: bool 是否完成填充。
        :return:
        """
        raise NotImplementedError
