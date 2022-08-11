"""
附加控件，用于提高自定义程度。
"""
from . import player

import os
import re
import time
import typing
import itertools
import socketserver

from PyQt5 import QtCore


# 以下代码实现了player套接字服务器，然而由于过于复杂的继承关系我已经看不懂代码了
#
#

class ServerHandler(socketserver.BaseRequestHandler):
    """供ServerPlayer使用"""

    def handle(self) -> None:
        data = self.request.recv(1024)
        self.server.player.finished = False
        self.server.player.handle = self
        self.server.player.server_thread.signal.emit(data.decode())

    def finish(self) -> None:
        while not self.server.player.finished:
            time.sleep(0.1)


class ServerThread(QtCore.QThread):
    """供ServerPlayer使用"""
    signal = QtCore.pyqtSignal(str)

    def __init__(self, server):
        super().__init__()
        self.server = server

    def run(self):
        self.server.serve_forever()


class ServerPlayer:
    """
    在player.Player的基础上使用套接字服务器。启动时调用 start_server 方法。
    """

    def __init__(self, server_player: player.Player):
        self.handle: ServerHandler  # handle 在 ServerHandler.handle 方法中被传递
        self.finished = True
        self.server_thread = None
        self.socket_server: typing.Optional[socketserver.TCPServer] = None
        self.server_player = server_player

    def run_command(self, cmd: str):  # 我知道这个代码像 ** 一样，但懒得改了。 FIXME: 不能处理命令中带","的情况
        print(os.getpid(), ": get command", cmd)
        if m := re.match(r"line\((.+?), *(.+?), *(.+?), *(.+?), *(.+?), *(.+?), *(.+?),? *\)", cmd):  # 绘制直线
            self.server_player.draw_a_line(m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4)),
                                           int(m.group(5)), m.group(6), int(m.group(7)))
        elif m := re.match(r"circ\((.+?), *(.+?), *(.+?), *(.+?), *(.+?), *(.+?),? *\)", cmd):  # 绘制圆
            self.server_player.draw_a_circle(m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4)), m.group(5),
                                             int(m.group(6)))
        elif m := re.match(r"del\((.+)\)", cmd):  # 删除
            self.server_player.remove_item(m.group(1))
        elif m := re.match(r"rect\((.+?), *(.+?), *(.+?), *(.+?), *(.+?), *(.+?), *(.+?),? *\)", cmd):
            self.server_player.draw_a_rectangular(m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4)),
                                                  int(m.group(5)),
                                                  m.group(6), int(m.group(7)))
        elif m := re.match(r"get\((.+?),? *\)", cmd):  # 获取变量
            try:
                v = self.server_player.get_variable(m.group(1))
            except KeyError:
                v = None
            try:
                self.handle.request.sendall(format(v).encode())  # handle 在 ServerHandler.handle 方法中被传递
            except OSError as err:
                print(type(err).__name__, err, "是否因为连接已断开？")
        elif m := re.match(r"not_graphic_name\((.+),? *\)", cmd):  # 返回一个未使用过的名称
            length = int(m.group(1))
            for name in itertools.combinations_with_replacement(
                    itertools.chain(range(48, 58), range(97, 123), range(65, 91)), length):  # 0~9 a~z A~Z
                name = "".join(chr(i) for i in name)
                if name not in self.server_player.item_names:
                    self.server_player.item_names.add(name)
                    break
            else:
                name = "\0"
            try:
                self.handle.request.sendall(format(name).encode())
            except OSError as err:
                print(type(err).__name__, err, "是否因为连接已断开？")
        elif m := re.match(r"char\((.+?), *(.+?), *(.+?), *(.+?), *(.+?), *(.+?), *(.+?),? *\)", cmd):  # 写文字
            self.server_player.write_char(m.group(1), m.group(2), int(m.group(3)), int(m.group(4)), int(m.group(5)),
                                          m.group(6), int(m.group(7)))
        self.finished = True

    def set_signal(self, str_signal: QtCore.pyqtSignal):
        """绑定信号"""
        str_signal.connect(self.run_command)

    def start_server(self, port=501, host="127.0.0.1", handler=ServerHandler) -> ServerThread:
        """利用 QThread 实现后台运行的服务器。
        Warning: 此命令不会检查是否已经启动了服务器
        """
        self.socket_server = server = Server(self, port, host, handler)
        # NOTE: thread应当被保留，否则被gc了就无法执行。有意思的是，若开启debug这个bug就不会复现
        self.server_thread = thread = ServerThread(server)
        self.set_signal(thread.signal)
        thread.start()
        return thread


class Server(socketserver.TCPServer):
    """供ServerPlayer使用的服务器"""

    def __init__(self, server_player, port=501, host="127.0.0.1", handler=ServerHandler):
        super().__init__((host, port), handler)
        self.player = server_player
