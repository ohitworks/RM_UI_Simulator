"""
本模块实现对象 PlayerManager 用于控制 RM_UI_Simulator.player_ui.Player 对象。提供切换背景和模拟下位机返回值功能。
"""
from ... import data  # 这见了鬼的目录结构
from .player import Player
from .new_variable_dialog import Ui_NewVariableDialog as NewVariableDialog

from PyQt5 import QtWidgets, QtGui, QtCore
import yaml

import os
import re
from typing import Union
import functools


class VariableButton(QtWidgets.QPushButton):
    """用于返回值控制中显示并编辑返回值。"""

    def __init__(self, master):

        super().__init__(master.variables_box)
        self.pressed_x = 0
        self.pressed_y = 0

        self.master = master
        self.var_type = None
        self.value: Union[int, float, str] = 0

        self.moved = False

        # policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        # self.setSizePolicy(policy)

    def mouseMoveEvent(self, e: QtGui.QMouseEvent) -> None:
        if self.state == "normal" and e.buttons() == QtCore.Qt.LeftButton:
            point_to = self.mapToParent(QtCore.QPoint(e.x() - self.pressed_x, e.y() - self.pressed_y))
            point_sub = QtCore.QPoint(point_to.x() + self.width(), point_to.y() + self.height())  # 按钮右下角坐标
            rect = self.parent().rect()
            if rect.contains(point_to) and rect.contains(point_sub):
                self.move(point_to)
                self.moved = True

    def mousePressEvent(self, e: QtGui.QMouseEvent) -> None:
        self.pressed_x = e.x()
        self.pressed_y = e.y()
        self.moved = False

    def mouseReleaseEvent(self, e: QtGui.QMouseEvent) -> None:
        if not self.rect().contains(e.pos()):
            return
        if e.button() == QtCore.Qt.LeftButton:  # 神奇，为啥这里要用 e.button(), buttons不行，但 MoveEvent 里只能用 buttons
            if self.state == "del":
                self.master.del_variable(self.text())
                self.deleteLater()
            elif self.state == "edit":
                self.edit()
            elif self.state == "normal" and not self.moved:
                self.set_value()
        elif e.button() == QtCore.Qt.RightButton:
            menu = QtWidgets.QMenu(self.parent())
            menu.addAction(f"{self.var_type} {self.text()} = {repr(self.value)}")
            menu.addSeparator()
            menu.addAction("编辑变量", self.edit)
            menu.addAction("赋值", self.set_value)
            menu.show()
            menu.move(self.mapToGlobal(e.pos()))

    def edit(self):
        """编辑按钮本身，自动更新 master.variables。 ButtonsWidget生成、编辑按钮时调用。编辑取消返回 1"""
        run = QtWidgets.QDialog()
        dia = NewVariableDialog()
        dia.setupUi(run)
        dia.var_name_input.setText(self.text())
        dia.comboBox.setCurrentText(self.var_type)
        if not run.exec():
            return 1
        name = dia.var_name_input.text()
        if not name:
            QtWidgets.QMessageBox.warning(self, "警告", "名称不能为空，请重新输入名称")
            return self.edit()
        if name != self.text():
            if name in self.master.variables:
                QtWidgets.QMessageBox.warning(self, "警告", "名称已存在，请重新输入名称")
                return self.edit()
            self.rename(name)
        var_type = dia.comboBox.currentText()
        if var_type != self.var_type:
            self.set_type(var_type)

    def rename(self, new: str):
        """重命名按钮。此方法会改变显示名称，并更新 master.variables 字典。如果该字典没有注册本对象，自动注册。"""
        if not new:
            raise ValueError("名称不能为空")
        try:
            self.master.variables.pop(self.text())
        except KeyError:
            pass
        self.master.variables[new] = self
        self.setText(new)
        self.adjustSize()  # 事实证明这个方法不能让按钮自动变长

    def set_type(self, var_type):
        if var_type == "int":
            self.value = 0
        elif var_type == "float":
            self.value = .0
        elif var_type == "char *":
            self.value = ""
        else:
            raise ValueError("`var_type` should be a string in", ("int", "float", "char *"))
        self.var_type = var_type

    def set_value(self):
        if self.var_type == "int":
            get = QtWidgets.QInputDialog.getInt(self.master, "编辑值", f"int {self.text()} = ", int(self.value))
            self.value = get[0]
        elif self.var_type == "float":
            get = QtWidgets.QInputDialog.getDouble(self.master, "编辑值", f"float {self.text()} = ", self.value)
            self.value = get[0]
        elif self.var_type == "char *":
            text = repr(self.value)[1:-1]
            get = QtWidgets.QInputDialog.getText(self.master, "编辑值", f"char * {self.text()} = ", text=text)
            if get[1]:
                value = get[0]  # 我原来用eval生成怕不是当时脑子抽了[发抖][发抖]
                while any(ord(s) > 255 for s in value):
                    QtWidgets.QMessageBox.warning(self.master, "警告", "字符应属于 \\0~\\255")
                    get = QtWidgets.QInputDialog.getText(self.master, "编辑值", f"char * {self.text()} = ", text=text)
                    if not get[1]:
                        break
                    value = get[0]
                else:
                    self.value = value

    @property
    def state(self):
        return self.master.state


class ButtonsWidget(QtWidgets.QWidget):
    """用于 PlayerManager 控制模拟返回值界面。"""

    def __init__(self, master, player: Player):
        super().__init__(master)
        self.player = player

        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)

        self.menu = self.setup_menu()
        layout.addWidget(self.menu)

        line = QtWidgets.QFrame(self)
        line.setFrameShape(QtWidgets.QFrame.VLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        layout.addWidget(line)

        self.variables_box = self.setup_values()
        layout.addWidget(self.variables_box)

        self.variables = {}
        self.state = "normal"  # 操作模式
        # 加载变量文件, 优先使用工作区的“上次变量文件”, 其次使用全局配置中的
        self.variables_file = None
        self.variables_file_init(data.get_global_config()["working project path"])

    def variables_file_init(self, working_project_path):
        """加载变量文件, 优先使用工作区的“上次变量文件”, 其次使用全局配置中的"""
        if working_project_path and data.has_local_config(working_project_path):
            # 存在工作区配置
            variables_file_from_global = False
            file = data.get_local_config(working_project_path).get("variables file")
            # NOTE: 特别注意：variables file在全局配置中为绝对路径，工作区配置中为相对(工作区文件夹的)路径
            file = working_project_path + "/" + file
        else:
            # 从全局配置中获取变量文件
            variables_file_from_global = True
            file = data.get_global_config()["variables file"]
        if file is not None:
            try:
                with open(file, "r", encoding="utf-8") as fp:
                    simulator_vars = yaml.safe_load(fp)
            except FileNotFoundError:  # TODO: 变化时提示
                # self.variables_file = None  # 不用加这句话, 此时该值就是 None
                data.update_global_config({"variables file": None})
                if not variables_file_from_global:
                    # 如果该文件位置从工作区配置得来
                    data.update_local_config(working_project_path, {"variables file": None})
            else:
                for name, (type_, value, pos) in simulator_vars.items():
                    bnt = VariableButton(self)
                    bnt.rename(name)
                    bnt.var_type = type_
                    bnt.value = value
                    bnt.move(*pos)
                    bnt.show()
                self.menu.file_label.setText(os.path.split(file)[1])
                self.variables_file = file

    def load_variable_file(self, path, *, update_path_to_working_config=True):
        """加载yaml变量文件"""
        path = os.path.abspath(path)
        with open(path, "r", encoding="utf-8") as fp:
            vars_data = yaml.safe_load(fp)

        copy = self.variables.copy()
        for bnt in self.variables.values():
            bnt.hide()
        self.variables.clear()

        try:
            for name, (type_, value, pos) in vars_data.items():
                bnt = VariableButton(self)
                bnt.rename(name)
                bnt.var_type = type_
                bnt.value = value
                bnt.move(*pos)
                bnt.show()
        except (TypeError, ValueError) as err:  # 出错后回调
            QtWidgets.QMessageBox.warning(self, type(err).__name__, str(err))
            self.remove_all_variables()  # 删除已加载的变量
            self.variables.update(copy)
            for bnt in self.variables.values():
                bnt.show()
        else:
            # 加载文件成功
            # 清除之前的按钮
            for bnt in copy.values():
                bnt.deleteLater()
            # -- 更新配置 --
            global_config = data.get_global_config()
            if global_config["variables file"] != path:
                data.update_global_config({"variables file": path})
            if update_path_to_working_config:
                wpp = global_config["working project path"]
                if data.has_local_config(wpp):
                    data.update_local_config(wpp, {"variables file": os.path.relpath(path, wpp)})
            # 可能存在配置和显示内容不同情况
            self.menu.file_label.setText(os.path.split(path)[-1])
            self.variables_file = path

    def setup_values(self):
        """创建并返回右侧变量栏"""
        widget = QtWidgets.QWidget(self)
        layout = QtWidgets.QHBoxLayout()
        widget.setLayout(layout)
        layout.addStretch(1)

        return widget

    def setup_menu(self):
        """创建并返回左侧菜单栏"""
        widget = QtWidgets.QWidget(self)
        layout = QtWidgets.QFormLayout()
        widget.setLayout(layout)

        widget.file_label = QtWidgets.QLabel("<未选择变量文件>", widget)
        layout.addRow(widget.file_label)

        open_button = QtWidgets.QPushButton("打开", widget)
        open_button.clicked.connect(self.menu_file_open_func)
        open_button.setShortcut("ctrl+o")
        reopen_button = QtWidgets.QPushButton("重载", widget)
        reopen_button.clicked.connect(self.menu_file_reopen_func)
        reopen_button.setShortcut("ctrl+r")
        layout.addRow(open_button, reopen_button)

        new_button = QtWidgets.QPushButton("新建", widget)
        new_button.clicked.connect(self.menu_file_new_func)
        new_button.setShortcut("ctrl+n")
        save_button = QtWidgets.QPushButton("保存", widget)
        save_button.setShortcut("ctrl+s")
        save_button.clicked.connect(self.menu_file_save_func)
        layout.addRow(new_button, save_button)

        add_button = QtWidgets.QPushButton("添加新模拟量", widget)
        add_button.clicked.connect(self.menu_value_add_func)
        layout.addRow(add_button)

        widget.edit_button = edit_button = QtWidgets.QPushButton("编辑模拟量", widget)
        edit_button.clicked.connect(self.menu_value_edit_func)
        layout.addRow(edit_button)

        widget.del_button = del_button = QtWidgets.QPushButton("删除模拟量", widget)
        del_button.clicked.connect(self.menu_value_del_func)
        layout.addRow(del_button)

        return widget

    def menu_file_reopen_func(self):
        if self.variables_file:
            self.load_variable_file(self.variables_file)

    def menu_file_open_func(self):
        file, true = QtWidgets.QFileDialog.getOpenFileName(self, "选择文件", "",
                                                           "YAML (*.yml *.yaml);; All Files (*)")
        if not true:  # 没有选择文件
            return
        self.load_variable_file(file)

    def menu_file_save_func(self):
        if not self.variables_file:
            # 当前没有变量文件
            file, run = QtWidgets.QFileDialog.getSaveFileName(self, "保存文件", "",
                                                              "YAML (*.yml *.yaml);; All Files (*)")
            if not run:
                return
            self.variables_file = file
            self.menu.file_label.setText(os.path.split(file)[1])
        # 生成变量数据
        vars_data = {name: (bnt.var_type, bnt.value, (bnt.pos().x(), bnt.pos().y()))
                     for name, bnt in self.variables.items()}
        with open(self.variables_file, "w", encoding="utf-8") as fp:
            yaml.safe_dump(vars_data, fp)
        # 写入配置文件
        data.update_global_config({"variables file": self.variables_file})
        working_project_path = data.get_global_config()["working project path"]
        if data.has_local_config(working_project_path):
            data.update_local_config(working_project_path,
                                     {"variables file": os.path.relpath(self.variables_file, working_project_path)})

    def menu_file_new_func(self):
        """
        菜单中的"新键文件"按钮对应的函数
        """
        self.remove_all_variables()
        self.menu.file_label.setText("<未选择变量文件>")
        self.variables_file = None
        # if data.get_global_config()["variables file"]:  # 只在保存文件时写入配置
        #     data.update_global_config({"variables file": None})

    def remove_all_variables(self):
        """删除所有变量"""
        for bnt in self.variables.values():
            bnt.deleteLater()
        self.variables.clear()

    def menu_value_add_func(self):
        # 重置操作模式
        if self.state == "del":
            self.menu_value_del_func()
        elif self.state == "edit":
            self.menu_value_edit_func()
        # 设置添加变量内容
        # 创建变量 UI
        btn = VariableButton(self)
        if btn.edit():
            btn.deleteLater()
        else:
            btn.show()

    def menu_value_edit_func(self):
        if self.state == "edit":
            self.menu.edit_button.setStyleSheet("")
            self.state = "normal"
            return
        if self.state == "del":
            self.menu_value_del_func()
        # state = "normal"
        self.menu.edit_button.setStyleSheet("background-color: rgb(65, 165, 238)")
        self.state = "edit"

    def menu_value_del_func(self):
        if self.state == "del":
            self.menu.del_button.setStyleSheet("")
            self.state = "normal"
            return
        if self.state == "edit":
            self.menu_value_edit_func()
        # state = "normal"
        self.menu.del_button.setStyleSheet("background-color: rgb(255, 30, 60)")
        self.state = "del"

    def del_variable(self, name):
        if name not in self.variables:
            QtWidgets.QMessageBox.warning(self, "警告", "未找到该变量。")
        self.variables.pop(name)


class SettingWidget(QtWidgets.QWidget):  # TODO: 实现大小修改
    """用于 PlayerManager 控制播放器背景、大小等属性界面。"""

    def __init__(self, parent, player):
        super().__init__(parent)
        self.player = player

        layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(layout)

        btn_layout = QtWidgets.QHBoxLayout()
        self.change_bg_img_btn = QtWidgets.QPushButton("修改背景图片", self)
        self.change_bg_img_btn.clicked.connect(self.change_bg_img_func)
        self.remove_bg_img_btn = QtWidgets.QPushButton("删除背景图片", self)
        self.remove_bg_img_btn.clicked.connect(self.remove_bg_img_func)
        btn_layout.addWidget(self.change_bg_img_btn)
        btn_layout.addWidget(self.remove_bg_img_btn)
        btn_layout.addStretch(1)
        layout.addLayout(btn_layout, QtCore.Qt.AlignTop)

        layout.addStretch(1)  # 使设置的按键居于顶端

    def change_bg_img_func(self):
        file, true = QtWidgets.QFileDialog.getOpenFileName(self, "选择播放器背景图片", "",
                                                           "PNG (*.png);;JPG (*.jpg);; All Files (*)")
        if true:
            self.player.set_background_picture(file)

    def remove_bg_img_func(self):
        self.player.set_background_picture(None)


class ItemButton(QtWidgets.QPushButton):
    def __init__(self, master, value_type: str, name: str):
        tp = re.match(r"QGraphics(\w+?)Item$", value_type)
        super().__init__(f"{tp.group(1)} {name}", master)
        self.value_type = value_type
        self.name = name

        self.clicked.connect(self.clicked_func)

    def clicked_func(self):  # TODO: 实现修改
        QtWidgets.QMessageBox.information(self.parent(), "抱歉", "我还没写完")


class ItemsWidget(QtWidgets.QWidget):
    BTN_LINE_NUMBER = 4  # 每行放多少按钮

    def __init__(self, master, player):
        super().__init__(master)
        self.player = player

        self.is_setting_item = False
        self.buttons = {}
        self.btn_layout_list = []

        layout = QtWidgets.QHBoxLayout(self)
        self.setLayout(layout)

        self.buttons_widget = btn_widget = QtWidgets.QWidget(self)
        btn_layout = QtWidgets.QFormLayout(btn_widget)
        btn_widget.setLayout(btn_layout)
        self.add_graphic_btn = QtWidgets.QPushButton("添加图形", btn_widget)
        self.add_graphic_btn.clicked.connect(self.add_graphic_func)
        self.del_graphic_btn = QtWidgets.QPushButton("删除图形", btn_widget)
        self.del_graphic_btn.clicked.connect(self.del_graphic_func)
        self.clear_graphic_btn = QtWidgets.QPushButton("删除所有图形", btn_widget)
        self.clear_graphic_btn.clicked.connect(self.clear_graphic_func)
        btn_layout.addRow(self.add_graphic_btn)
        btn_layout.addRow(self.del_graphic_btn)
        btn_layout.addRow(self.clear_graphic_btn)
        layout.addWidget(btn_widget)

        line = QtWidgets.QFrame(self)
        line.setFrameShape(QtWidgets.QFrame.VLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        layout.addWidget(line)

        self.items_btn_widget = items_widget = QtWidgets.QWidget(self)
        h_layout = QtWidgets.QHBoxLayout(items_widget)
        items_widget.setLayout(h_layout)
        self.btn_layout = QtWidgets.QGridLayout()
        h_layout.addLayout(self.btn_layout)
        h_layout.addStretch(0)
        layout.addWidget(items_widget)

    def add_graphic_func(self):  # TODO: 实现添加图形
        QtWidgets.QMessageBox.information(self.parent(), "抱歉", "我还没写完")

    def del_graphic_func(self):  # TODO: 实现删除图形
        QtWidgets.QMessageBox.information(self.parent(), "抱歉", "我还没写完")

    def clear_graphic_func(self):
        """删除所有图形"""
        for i in tuple(self.player.item_names):
            try:
                self.player.remove_item(i)
            except KeyError:
                pass

    def player_item_set(self, name):
        obj = self.player.item_objects[name]

        value_name = type(obj).__name__
        btn = self.buttons.get(name)
        if btn is None:
            col = -1
            row = 0
            for col, rows in enumerate(self.btn_layout_list):
                if len(rows) < self.BTN_LINE_NUMBER:
                    row = (set(range(self.BTN_LINE_NUMBER)) - rows).pop()
                    rows.add(row)
                    break
            else:
                col += 1
                self.btn_layout_list.append({row})
            self.buttons[name] = btn = ItemButton(self, value_name, name)
            self.btn_layout.addWidget(btn, row, col)
        else:
            btn.value_name = value_name

    def player_item_removed(self, name):
        if self.is_setting_item:
            return
        btn = self.buttons.pop(name)
        idx = self.btn_layout.indexOf(btn)
        row, col, _, _ = self.btn_layout.getItemPosition(idx)
        self.btn_layout.removeWidget(btn)
        btn.deleteLater()
        self.btn_layout_list[col].remove(row)


class PlayerManager(QtWidgets.QTabWidget):
    """管理者，包括数值回复等。。"""

    def __init__(self, player: Player, size_x=None, size_y=None):
        super().__init__()
        self.player = player
        if size_x is None:
            size_x = player.size().width()
        if size_y is None:
            size_y = player.size().height() // 3
        self.resize(size_x, size_y)

        self.buttons_widget = ButtonsWidget(self, player)
        self.addTab(self.buttons_widget, "返回值控制")
        self.items_widget = ItemsWidget(self, player)
        self.addTab(self.items_widget, "图形管理")
        self.setting_widget = SettingWidget(self, player)
        self.addTab(self.setting_widget, "基础设置")

        self.update_player_item_options()
        self.update_player_variable_options()

    def update_player_item_options(self):
        set_item = self.player.set_item
        del_item = self.player.remove_item

        def set_(*args, **kwargs):
            self.items_widget.is_setting_item = True
            try:
                set_item(*args, **kwargs)
                name = kwargs.get("name")
                if name is None:
                    name = args[0]
                self.items_widget.player_item_set(name)
            finally:
                self.items_widget.is_setting_item = False

        def del_(*args, **kwargs):
            del_item(*args, **kwargs)
            name = kwargs.get("name")
            if name is None:
                name = args[0]
            self.items_widget.player_item_removed(name)

        functools.update_wrapper(set_, self.player.set_item)
        setattr(self.player, "set_item", set_)
        functools.update_wrapper(del_, self.player.remove_item)
        setattr(self.player, "remove_item", del_)

    def update_player_variable_options(self):
        set_var = self.player.set_variable
        get_var = self.player.get_variable

        def set_(*args, **kwargs):
            name = kwargs.get("name")
            if name is None:
                name = args[0]
            value = kwargs.get("value")
            if value is None:
                value = args[1]
            if name in self.buttons_widget.variables:
                btn = self.buttons_widget.variables[name]
                t = type(value)
                btn.value_type = "char *" if t is str else t.__name__
                btn.value = value
            else:
                btn = VariableButton(self.buttons_widget)
                btn.rename(name)  # 自动更新
                t = type(value)
                btn.value_type = "char *" if t is str else t.__name__
                btn.value = value
            return set_var(*args, **kwargs)

        def get(*args, **kwargs):
            try:
                return get_var(*args, **kwargs)
            except KeyError:
                name = kwargs.get("name")
                if name is None:
                    name = args[0]
                return self.buttons_widget.variables[name].value

        functools.update_wrapper(get, self.player.get_variable)
        functools.update_wrapper(set_, self.player.set_variable)

        setattr(self.player, "get_variable", get)
        setattr(self.player, "set_variable", set_)
