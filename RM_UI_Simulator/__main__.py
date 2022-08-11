"""我觉得这里应该写点什么，但是写什么呢？

"""

if __name__ == "__main__":
    import sys
    from PyQt5 import QtWidgets
    from RM_UI_Simulator import qtui, data

    # 好奇怪，加上这一行之后找不到界面了，系统栏上倒是能显示qt
    # 在 cmd, spyder 里调试都显示正常，唯独在 PyCharm 中显示不正常。找到了，原因是我当时 PyCharm 运行的桌面缩放不是 100%
    # 这么做确实启动了自适应缩放，但如果启动窗口不在100% 不显示窗口
    # QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)

    app = QtWidgets.QApplication([])
    # app.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)  # 事实证明这行代码没用

    if len(sys.argv) == 1:
        main = qtui.MainWindow(0)
        main.show()
        app.exec()

    elif 2 <= len(sys.argv) <= 3:
        if sys.argv[1] == "server":
            if len(sys.argv) == 3 and sys.argv[-1].isnumeric():
                PORT = int(sys.argv[-1])
            else:
                PORT = data.get_global_config()["default server port"]
        elif sys.argv[1].isnumeric():
            PORT = int(sys.argv[-1])
        else:
            raise ValueError
        main = qtui.MainWindow(PORT)
        main.show()
        app.exec()

    else:
        raise ValueError
