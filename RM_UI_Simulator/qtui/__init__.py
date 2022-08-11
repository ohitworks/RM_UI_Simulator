"""
此子模块实现了该模拟器的 UI
"""

from .option_ui import OptionButton, WindowOptions
from .player_ui import Player, PlayerManager
from .main_window import WelcomeWindow, MainWindow, Simulator, ChooseFiles

from . import main_window


def fast_start():
    from PyQt5 import QtWidgets
    app = QtWidgets.QApplication([])
    MainWindow().show()
    app.exec()


__all__ = ["fast_start", "Player", "PlayerManager", "OptionButton", "WindowOptions",
           "WelcomeWindow", "MainWindow", "Simulator", "ChooseFiles"]
