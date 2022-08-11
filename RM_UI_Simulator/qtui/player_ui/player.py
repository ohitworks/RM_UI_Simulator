"""
播放器主体
"""
from PyQt5 import QtWidgets, QtCore, QtMultimedia, QtMultimediaWidgets, QtGui


class Player(QtWidgets.QGraphicsView):
    """
    播放总控件，仅支持图片。
    """

    def __init__(self, size_x=960, size_y=540, board_x=1920, board_y=1080, *, parent=None):
        super().__init__(parent)

        self.item_objects = {}
        self.item_names = set()
        self.variables = {}  # NOTE: Player的变量属于普及式功能，主要还是靠 PlayerManager

        self.resize(size_x, size_y)

        self.setScene(QtWidgets.QGraphicsScene(0, 0, board_x, board_y))  # TODO: 支持可调节场景大小

    def get_variable(self, name):
        return self.variables[name]

    def set_variable(self, name, value):
        if not isinstance(value, (int, float, str)):
            raise TypeError("value 属性应为(int, float, str)中的一个，收到了", type(value))
        self.variables[name] = value

    def set_background_picture(self, file):
        """
        展示图片。若为空字符，则停止展示。
        """
        if file:
            file = file.replace("\\", "/")  # NOTE: QT background-image 路径不能用反斜杠
            self.setStyleSheet(f"background-image: url({file});")
        else:
            self.setStyleSheet("")

    def set_item(self, name, item):
        self.scene().addItem(item)
        if name in self.item_objects:
            self.scene().removeItem(self.item_objects[name])
        self.item_names.add(name)
        self.item_objects[name] = item
        self.scene().update()

    def remove_item(self, name):
        item = self.item_objects.pop(name)
        self.scene().removeItem(item)
        self.item_names.remove(name)

    def draw_a_line(self, name, start_x, start_y, end_x, end_y, colour, width):
        pen = QtGui.QPen(QtGui.QColor(colour))
        pen.setWidth(width)

        line = QtWidgets.QGraphicsLineItem()
        # start = self.mapToScene(start_x, start_y)
        # end = self.mapToScene(end_x, end_y)
        # print(start, end)
        # line.setLine(start.x(), start.y(), end.x(), end.y())
        line.setLine(start_x, start_y, end_x, end_y)
        line.setPen(pen)
        self.set_item(name, line)

    def draw_a_circle(self, name, centre_x, centre_y, radius, colour, width):
        pen = QtGui.QPen(QtGui.QColor(colour))
        pen.setWidth(width)

        circle = QtWidgets.QGraphicsEllipseItem()
        circle.setPen(pen)
        circle.setRect(centre_x - radius, centre_y - radius, radius * 2, radius * 2)

        self.set_item(name, circle)

    def draw_a_rectangular(self, name, start_x, start_y, end_x, end_y, colour, width):
        pen = QtGui.QPen(QtGui.QColor(colour))
        pen.setWidth(width)

        line = QtWidgets.QGraphicsRectItem()
        line.setRect(start_x, start_y, end_x - start_x, end_y - start_y)
        line.setPen(pen)

        self.set_item(name, line)

    def write_char(self, name, string, start_x, start_y, font_size, colour, width):
        pen = QtGui.QPen(QtGui.QColor(colour))
        pen.setWidth(width)

        item = QtWidgets.QGraphicsSimpleTextItem()
        item.setPos(start_x, start_y)
        item.setText(string)
        item.setPen(pen)
        font = QtGui.QFont()
        font.setPixelSize(font_size)
        item.setFont(font)

        self.set_item(name, item)


class VideoPlayer(QtMultimediaWidgets.QVideoWidget):
    """视频播放器，但现在看已经没用了。"""

    def __init__(self, min_size_x=960, min_size_y=540, master=None, volume=0):
        if master:
            super().__init__(master)
        else:
            super().__init__()
        self.media_player = QtMultimedia.QMediaPlayer()

        self.media_player.setVideoOutput(self)
        self.media_player.setVolume(volume)

        self.setMinimumSize(min_size_x, min_size_y)

    def set_volume(self, volume):
        """设置音量，默认为0"""
        self.media_player.setVolume(volume)

    def play(self, filename):  # TODO 支持流文件
        video = QtCore.QUrl.fromLocalFile(filename)
        self.stop()
        self.media_player.setMedia(QtMultimedia.QMediaContent(video))
        self.media_player.play()

    def stop(self):
        self.media_player.stop()

    def __del__(self):
        self.stop()
