"""
图形界面中的设置选项。
"""
from PyQt5 import QtWidgets, QtCore, QtGui
import typing


class WindowOptions:
    """设置菜单中当前桌面的选项，使用此方法是为了避免设置时再调用 Qt 。
    初始化时先传入选项名称，以字典形式传入选项名称和对应的函数
    
    菜单生成中设置动作后调用 update_action 方法，并传入设置动作时返回的QAction对象
    """  # 尽管这样避免调用时再写 QMenu，但是现在还不支持子菜单

    def __init__(self, options: typing.Iterable[str], option_action_dict: dict[str: typing.Callable]):
        self.options = options
        self.option_action_dict = option_action_dict

    def __getitem__(self, item):
        return self.option_action_dict[item]

    def update_action(self, action: QtWidgets.QAction):
        """菜单生成中设置动作后调用该方法，并传入设置动作时返回的QAction对象"""
        return


class OptionButton(QtWidgets.QPushButton):
    """
    图形界面设置键。

    basic_options: list[Union[str, QAction]]
        通过修改 basic_options 内容改变设置基础选项。如果内容为str，选择后调用 self.{选项名称}。为QAction则不执行。

    Menu: QtWidget | define: QtWidgets.QMenu
        显示设置时生成的菜单类，可通过修改来改变调用。注意这里不是实例。
    """

    basic_options: list[QtWidgets.QAction] = []  # UI基础选项，无论在哪个页面都会在设置最上方，用户选择后调用self.{选项名称}
    Menu = QtWidgets.QMenu  # 显示设置时生成的菜单类，可通过修改来改变调用。

    def __init__(self, master, radius: int = 20, background_colour="rgb(255, 40, 40)"):
        super().__init__(master)

        self.window_options = []  # 设置菜单中当前桌面的选项

        diameter = radius * 2
        self.resize(diameter, diameter)
        self.setFixedSize(diameter, diameter)
        self.setText("设置")
        self.setStyleSheet(f"border-radius: {radius}px; background-color: {background_colour}; padding: 2px 4px")

        opacity_effect = QtWidgets.QGraphicsOpacityEffect()
        opacity_effect.setOpacity(0)
        self.setGraphicsEffect(opacity_effect)  # 设置后调用self.graphicsEffect()即可得到 opacity_effect

        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

    def add_window_options(self, option: WindowOptions) -> None:
        """添加对应窗口的设置选项"""
        self.window_options.append(option)

    def remove_window_options(self, option: WindowOptions) -> None:
        """删除该窗口的设置选项"""
        self.window_options.remove(option)

    def enterEvent(self, a0: QtCore.QEvent) -> None:  # 鼠标进入事件
        self.graphicsEffect().setOpacity(1)

    def leaveEvent(self, a0: QtCore.QEvent) -> None:  # 鼠标离开事件
        self.graphicsEffect().setOpacity(0)

    def mouseReleaseEvent(self, e: QtGui.QMouseEvent) -> None:
        """当鼠标松开时，显示菜单栏"""
        if not self.rect().contains(e.pos()):
            return

        cmenu = QtWidgets.QMenu()

        for action in self.basic_options:
            cmenu.addAction(action)

        window_options = {}
        for options in self.window_options:
            window_options[str(options)] = actions = []  # 用于保存每个窗口选项和它设置的动作，用于后期识别哪个窗口的动作被调用
            cmenu.addSeparator()
            for name in options.options:
                action = cmenu.addAction(name)
                options.update_action(action)
                actions.append(action)

        ret = cmenu.exec_(self.mapToGlobal(e.pos()))

        if ret is None:  # 什么都没选
            return

        if ret in self.basic_options:  # 调用基础选项函数
            try:
                call = getattr(self, ret.text(), None)
            except UnicodeError:
                # 若方法不存在且搜索的方法名不能编码为ascii
                pass
            else:
                if callable(call):
                    call()
        else:
            for options in self.window_options:
                actions = window_options[str(options)]
                if ret in actions:
                    options[ret.text()]()
                    break
