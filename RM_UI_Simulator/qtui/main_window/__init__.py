"""
构建主界面对象
"""
from PyQt5 import QtWidgets, QtCore

from . import welcome_window, ask_server_port
from .. import player_ui, option_ui
from ... import data
from ...C_platform import ChooseFilesABC, make_cmake_text, MessageEvent

import os
import re
import sys
import typing
import shutil
import subprocess

WELCOME_INDEX = 0
SIMULATOR_INDEX = 1
MAKE_INDEX = 2


class DynamicMenuOptions(option_ui.WindowOptions):  # 用法详见 Simulator.__init__ 中`dmo`的使用
    def __init__(self):
        super(DynamicMenuOptions, self).__init__([], {})
        self._options = []
        self._option_action_dict = {}

    def add_option(self, get_text: typing.Callable, do_what: typing.Callable):
        self._options.append(get_text)
        self._option_action_dict[get_text] = do_what

    @property
    def options(self):
        self.option_action_dict.clear()
        ret = []
        for get_text in self._options:
            text = get_text()
            ret.append(text)
            self.option_action_dict[text] = self._option_action_dict[get_text]
        return ret

    @options.setter
    def options(self, val):
        pass


class Simulator(QtWidgets.QWidget):
    # NOTE: self.settings 不会有project_path一值
    def __init__(self, parent, *, server_port=0):
        # parent 的类型应为MainWindow
        super(Simulator, self).__init__(parent)
        self.player = player_ui.Player(parent=self)
        self.manager = player_ui.PlayerManager(self.player)

        self.splitter = QtWidgets.QSplitter(self)
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.splitter.addWidget(self.player)
        self.splitter.addWidget(self.manager)

        layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(layout)
        layout.addWidget(self.splitter)

        self.option = option_ui.OptionButton(self.player)
        self.option.move(45, 45)

        self.working_path = ""
        self.settings = {}

        # 设置按钮
        self.option.basic_options.append(QtWidgets.QAction("无文件"))

        act = QtWidgets.QAction("构建")
        act.setShortcut("F4")
        self.option.basic_options.append(act)
        # self.option.构建 = self.build
        setattr(self.option, "构建", self.build)

        act = QtWidgets.QAction("执行")
        act.setShortcut("F5")
        self.option.basic_options.append(act)
        setattr(self.option, "执行", self.run)

        if server_port is None:  # MainWindow里默认填 None
            server_port = data.get_global_config()["default server port"]

        dmo = DynamicMenuOptions()
        dmo.add_option(self.get_show_socket_text, self.ui_change_socket_server_port)
        self.option.window_options.append(dmo)

        self.server_port = server_port  # 记录服务器端口

        funcs = {"回到欢迎界面": self.back_to_welcome, "重新编辑项目": self.remake_project}
        self.option.add_window_options(option_ui.WindowOptions(funcs, funcs))

        dmo = DynamicMenuOptions()
        dmo.add_option(lambda: ("程序正在运行，点击终止" if self.is_running_subject() else "没有程序运行"),
                       lambda: getattr(self, "popen_progress").kill())

        self.option.add_window_options(dmo)

        # 启动服务器
        self.server = player_ui.player_widgets.ServerPlayer(self.player)
        if server_port:
            self.server.start_server(server_port)

        self.popen_progress = subprocess.Popen("echo 模拟器初始化完成", shell=True)

    def get_show_socket_text(self) -> str:
        if self.server_port:
            key = f"PORT {self.server_port}"
        else:  # 端口号填 0 表示不启动服务
            key = "未启动服务器"
        return key

    def ui_change_socket_server_port(self):
        """
        在图形化界面中修改套接字服务器端口, 此方法调用change_socket_server_port
        """
        dialog = QtWidgets.QDialog(self)
        ask_dialog = ask_server_port.Ui_AskServerPort()
        ask_dialog.setupUi(dialog)
        ask_dialog.messsage_box.setText("当前 " + self.get_show_socket_text())
        ask_dialog.spinBox.setValue(self.server_port)
        if not dialog.exec_():
            # 用户关闭或点击“取消”按钮都会进入这里
            return
        try:
            self.change_socket_server_port(ask_dialog.spinBox.value())
        except Exception as err:
            QtWidgets.QMessageBox.critical(self, "转换端口时出错", type(err).__name__ + str(err))
        else:
            QtWidgets.QMessageBox.information(self, "转换端口", "转换端口成功")

    # def kill_popen_progress(self):
    #     self.popen_progress

    def change_socket_server_port(self, port):
        """
        (not port) == True: stop server
        """
        if not port:
            # 关闭服务器
            if not self.server_port:
                # 无需更改
                return
            # 关闭服务器
            self.server.socket_server.shutdown()  # 好消息是这个服务器真的在另一个线程运行(如果不是会卡死)
            # 修改保存的端口
            self.server_port = 0
        else:
            if self.server_port == port:
                # 无需更改
                return
            if self.server.socket_server:
                # 关闭服务器
                self.server.socket_server.shutdown()
            # 指定端口启动服务器
            self.server.start_server(port)
            # 修改保存的端口
            self.server_port = port

    def is_running_subject(self):
        return self.popen_progress.poll() is None

    def __del__(self):
        sup = super()
        try:
            if hasattr(sup, "__del__"):
                sup.__del__()
        finally:
            self.popen_progress.kill()

    def remove_outside_files(self, _re: None | re.Pattern = None) -> bool:
        """
        将不属于项目目录的文件移出项目组，修改self.settings,不写入配置文件。返回是否有修改。
        Args:
            _re:
                re.Pattern | None, 如果为None则构建正则表达式用于判断路径。否则使用_re.match进行判断
        Returns:
        bool, 表示是否进行了修改
        """
        if _re is None:
            _re = re.compile(rf"^{self.working_path}")
        changed = False
        objs = (self.settings.get("inc_files", ()),
                self.settings.get("src_files", ()),
                self.settings.get("link_files", ()))
        for ls in objs:
            i = 0
            while i < len(ls):
                file_path = ls[i]
                if os.path.isabs(file_path):
                    if not _re.match(file_path):
                        ls.pop(i)
                        changed = True
                else:
                    i += 1
        return changed

    def remove_nonexistent_files(self) -> bool:
        """将 self.setting 中不存在的文件移除，修改self.settings, 不写入配置文件。返回是否有修改。"""
        changed = False
        objs = (self.settings.get("inc_files", ()),
                self.settings.get("src_files", ()),
                self.settings.get("link_files", ()))
        for ls in objs:
            i = 0
            while i < len(ls):  # 原来的代码是“for p in ls:” 导致了若迭代时删除了p，非常可能导致部分内容不被迭代到
                file_path = ls[i]
                file_path = file_path if os.path.isabs(file_path) else f"{self.working_path}/{file_path}"
                if not os.path.exists(file_path):
                    ls.pop(i)
                    changed = True
                else:
                    i += 1
        return changed

    def remake_project(self):
        """重新编辑项目"""
        self.parent().switch_to_make_project(MessageEvent("你回来啦？"), self.settings, project_path=self.working_path)

    def run(self):
        """执行"""
        if not self.working_path:  # 没有打开的项目
            ret = QtWidgets.QMessageBox.question(self.parent(), "错误", "需要打开一个项目。\n现在打开吗？")
            if ret == QtWidgets.QMessageBox.Yes:
                self.parent().open_folder()
            return
        if self.popen_progress.poll() is None:  # 检查是否正在执行
            ret = QtWidgets.QMessageBox.question(self.parent(), "运行",
                                                 "上一个程序正在运行。需要停止运行后再生成\n要关闭吗？")
            if ret == QtWidgets.QMessageBox.Yes:
                self.popen_progress.kill()
            else:
                return
        config = data.get_local_config(self.working_path)
        if not config["build"]:
            code = self.build(show_info=False)
            if code is not None and code != 0:
                QtWidgets.QMessageBox.information(self.parent(), "构建失败", "代码在构建时失败，无法运行")
        build_path = self.working_path + "/" + self.settings["build_path"]
        cmake_path = self.settings["cmake_path"]
        if " " in cmake_path:
            cmake_path = f'"{cmake_path}"'
        cmd = [cmake_path, "--build", build_path, "--target", self.settings["project_name"]]
        cmd = " ".join(cmd)
        print(cmd)
        subprocess.call(cmd, shell=True)

        self.popen_progress = subprocess.Popen(f'"{build_path}/{self.settings["project_name"]}.exe" & echo 程序结束',
                                               stdout=sys.stdout, stdin=sys.stdin, stderr=sys.stderr, shell=True)

    def build(self, show_info=True):
        """根据配置执行CMake构建"""
        if not self.working_path:
            ret = QtWidgets.QMessageBox.question(self.parent(), "错误", "进行构建，请打开一个项目。\n现在打开吗？")
            if ret == QtWidgets.QMessageBox.Yes:
                self.parent().open_folder()
            return
        cmake_list_path = self.working_path + "/CMakeLists.txt"
        try:
            file_text = make_cmake_text(self.settings["inc_files"], self.settings["src_files"],
                                        self.settings.get("link_files", ()), self.settings["project_name"],
                                        self.settings.get("c_compiler_path"), self.settings.get("cxx_compiler_path"),
                                        project_path=self.working_path)
        except FileNotFoundError as err:
            QtWidgets.QMessageBox.critical(self.parent(), "构建时出错",
                                           type(err).__name__ + "：" + err.strerror + "\n路径：" + err.filename)
            return
        with open(cmake_list_path, "w", encoding="utf-8") as fp:
            fp.write(file_text)

        cmake_path = self.settings["cmake_path"]
        if " " in cmake_path:
            cmake_path = f'"{cmake_path}"'
        build_dir = self.working_path + "/" + self.settings["build_path"]
        cmd = [cmake_path,
               "-S", os.path.relpath(self.working_path, ".").join('""'),
               "-B", build_dir.join('""')]

        cmd = " ".join(cmd)

        # 删除上一次构建生成的文件
        if os.path.isdir(build_dir):
            try:
                shutil.rmtree(build_dir)
            except PermissionError:
                # 出现权限错误
                pass

        print(cmd)

        code = subprocess.call(cmd, shell=True)

        if code == 0:
            # 构建成功
            data.update_local_config(self.working_path, build=True)  # 更新配置
            if show_info:
                QtWidgets.QMessageBox.information(self.parent(), "构建成功", "构建成功")
        elif show_info:
            QtWidgets.QMessageBox.information(self.parent(), "构建失败", "构建失败")

        return code

    def set_setting_information(self, path, settings):
        """
        更新项目和模拟器的配置, 此函数回修改工作区配置文件
        Args:
            path:
                新的工作路径
            settings:
                工作区配置

        Returns:
            None
        """
        self.working_path = path
        if settings:
            self.settings.update(settings)
        self.option.basic_options.pop(0)

        warnings = []

        changed = False

        if self.remove_nonexistent_files():  # 将不存在的文件移除项目配置
            changed = True
            warnings.append("已将不存在的文件移除项目配置")
        if changed:
            data.update_local_config(self.working_path, build=False)

        if warnings:
            QtWidgets.QMessageBox.information(self.parent(), "通知", "\n".join(warnings))

        home_path = os.path.expanduser("~")
        path = path.replace(home_path.replace("\\", "/"), "~")
        if len(path) > 25:  # 最多显示路径文字长度
            path = path[-21:].split("/", 1)
            if len(path) == 2:
                path = path[1]
            else:
                path = path[0]
            path = ".../" + path
        elif not path:
            path = "无文件"
        self.option.basic_options.insert(0, QtWidgets.QAction(path))
        # 切换变量文件, NOTE: 不考虑从总配置中加载文件
        if settings is not None:
            # 此时已选择工作区
            # --- 获取当前打开的变量文件路径 ---
            variables_file = self.manager.buttons_widget.variables_file
            if variables_file is not None:
                variables_file = os.path.realpath(variables_file).replace("\\", "/")
            # --- 获取当前工作区配置中上次打开的变量文件路径 ---
            working_vf = settings.get("variables file")
            if working_vf is not None:
                working_vf = os.path.realpath(path + "/" + working_vf).replace("\\", "/")
            # --- 判断 ---
            if working_vf and variables_file != working_vf:
                # 工作区配置有变量文件, 且工作区变量文件并非已打开的文件
                self.manager.buttons_widget.variables_file = self.settings["variables file"] = working_vf
                if variables_file is None and self.manager.buttons_widget.variables:
                    # 实际打开的文件为空但存在变量, 说明可能创建了新的变量文件且未保存, 此时不加载新的文件文件
                    pass
                else:
                    self.manager.buttons_widget.remove_all_variables()
                    self.manager.buttons_widget.variables_file_init(self.working_path)
                    # self.manager.buttons_widget.load_variable_file(working_vf, update_path_to_working_config=False)

    def back_to_welcome(self):
        """切回到欢迎界面"""
        self.parent().setCurrentIndex(WELCOME_INDEX)


class ChooseFiles(ChooseFilesABC):
    def finish(self, finished: bool):
        if finished:
            # 切换到模拟器界面
            settings = self.make_settings()
            working_path = settings.pop("working_path")
            data.update_local_config(working_path, settings)  # 将设置更新到配置文件中
            self.parent().switch_to_simulator(working_path, settings)
        else:
            # 切换回欢迎界面
            self.parent().setCurrentIndex(WELCOME_INDEX)

    def make_settings(self):
        """构建项目配置"""  # TODO: 将路径改为相对路径
        working_path = self.project_path
        project_files = [i[1:] for i in self.project_files_item_dict if i[0] == "!"]
        ret = {"working_path": working_path,
               "cmake_path": self.cmake_path,
               "build_path": os.path.relpath(self.get_real_path(self.build_path), working_path),
               "project_name": self.project_name.text(),
               "inc_files": [i for i in project_files if i.endswith(".h")],  # 为啥存绝对路径啊？
               "src_files": [i for i in project_files if i.endswith(".c")],  # 虽然是我写的，但真的忘了
               "link_files": [i for i in project_files if i.endswith((".a", ".lib"))],
               "c_compiler_path": self.c_compiler_path,
               "cxx_compiler_path": self.cxx_compiler_path,
               }

        return ret


class MainWindow(QtWidgets.QStackedWidget):
    def __init__(self, server_part=None):
        super(MainWindow, self).__init__()
        self.welcome_widget = WelcomeWindow(self)
        self.simulator_widget = Simulator(self, server_port=server_part)
        self.make_widget = ChooseFiles(self)

        self.addWidget(self.welcome_widget)
        self.addWidget(self.simulator_widget)
        self.addWidget(self.make_widget)

        if working_path := data.get_global_config()["working project path"]:
            try:
                self.switch_to_simulator(working_path, data.get_local_config(working_path), False)
            except FileNotFoundError:
                # 原来打开的文件被删除
                data.update_global_config({"working project path": ""})

        self.have_switched_to_choose_interface = False

    def switch_to_simulator(self, working_path: str = "", settings: typing.Union[None, dict] = None,
                            update=True):
        """注意：调用时，working_path 若与 settings["project_path"] 不一致，则按working_path为准，
        set_setting_information 将把不属于项目目录的文件移出项目组。"""
        self.setCurrentIndex(SIMULATOR_INDEX)
        self.simulator_widget.set_setting_information(working_path, settings)
        if update:  # 更新配置
            data.update_global_config({"working project path": working_path})

    def open_folder(self):
        """选择并打开文件夹"""
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "打开文件夹", os.environ.get("HOME""PATH", "~"))
        if not path:
            return
        config = None
        if data.has_local_config(path):
            config = data.get_local_config(path)
            if config["project_name"]:
                # 在此打开
                self.switch_to_simulator(path, config)  # 注意这时 path 可能于 config["project_path"] 不一致
                return
        else:
            data.init_local_config(path)
        self.switch_to_make_project("Hello！点我获得提示~", config, project_path=path)

    def switch_to_make_project(self, message_event=None, sittings=None, **kwargs):
        """切换到配置界面
        sittings和kwargs 表示更新的配置
        message_event 表示初始消息"""
        if sittings:
            kwargs.update(sittings)
        path = kwargs.get("cmake_path")
        if path:
            self.make_widget.change_cmake_path(path)
        name = kwargs.get("project_name")
        if name:
            self.make_widget.project_name.setText(name)
        project_path = kwargs.get("project_path")  # 项目路径
        if project_path and self.have_switched_to_choose_interface != project_path:
            try:
                self.make_widget.change_project_path(project_path)
            except (FileNotFoundError, NotADirectoryError):
                msg = "文件夹 %s 打开错误。请重新选择文件夹" % project_path
                if message_event is None:
                    message_event = msg
                elif isinstance(message_event, MessageEvent):
                    message_event.text += "\n%s" % msg
            else:
                files = kwargs.get("inc_files", []) + kwargs.get("src_files", [])
                for file in files:
                    dir_name, file = os.path.split(file.replace("\\", "/"))  # 注意 relpath 回把/变为\ 这里要变回来
                    if dir_name not in self.make_widget.project_files_item_dict:
                        # 文件的父目录不在项目内，需要手动添加
                        self.make_widget.add_project_dir(dir_name)
                    self.make_widget.add_project_file(dir_name, file)
                path = kwargs.get("build_path")
                if path:
                    self.make_widget.change_build_path(project_path + "/" + path)
            self.have_switched_to_choose_interface = project_path
        if message_event:
            self.make_widget.message_event(message_event)
        self.setCurrentIndex(MAKE_INDEX)  # 切换到项目构建界面


class WelcomeWindow(welcome_window.Ui_Form, QtWidgets.QWidget):
    # TODO: 弹出设置和信息
    def __init__(self, parent: MainWindow):
        super().__init__(parent)
        self.setupUi(self)

        self.open_folder.clicked.connect(self.open_folder_func)
        self.enter_simulator.clicked.connect(self.enter_simulator_func)
        self.settings.clicked.connect(self.enter_setting_func)
        self.about.clicked.connect(self.enter_about_func)
        self.master = parent

    def enter_simulator_func(self):
        self.master.switch_to_simulator("", None)

    def open_folder_func(self):
        """按下“打开文件夹”时触发"""
        self.master.open_folder()

    def enter_setting_func(self):
        """进入设置界面"""  # TODO: 实现设置界面
        QtWidgets.QMessageBox.information(self.master, "抱歉", "未完成")

    def enter_about_func(self):
        """进入消息界面"""  # TODO: 实现消息界面
        QtWidgets.QMessageBox.information(self.master, "未完待续……",
                                          "\n".join(["版本号： " + data.get_variables().get("version", "ERROR!"),
                                                     "西交利物浦大学 G-Master 战队 电控-UI组 2022赛季出品"]))
