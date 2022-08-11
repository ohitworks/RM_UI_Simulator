# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\welcome_window.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(551, 801)
        Form.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem)
        self.open_folder = QtWidgets.QPushButton(Form)
        font = QtGui.QFont()
        font.setFamily("华文中宋")
        font.setPointSize(20)
        font.setBold(False)
        font.setWeight(50)
        self.open_folder.setFont(font)
        self.open_folder.setMouseTracking(False)
        self.open_folder.setAutoFillBackground(False)
        self.open_folder.setStyleSheet("color: rgb(0, 85, 255);")
        self.open_folder.setFlat(True)
        self.open_folder.setObjectName("open_folder")
        self.verticalLayout_2.addWidget(self.open_folder)
        self.enter_simulator = QtWidgets.QPushButton(Form)
        font = QtGui.QFont()
        font.setFamily("华文中宋")
        font.setPointSize(20)
        font.setBold(False)
        font.setWeight(50)
        self.enter_simulator.setFont(font)
        self.enter_simulator.setStyleSheet("color: rgb(0, 85, 255);")
        self.enter_simulator.setFlat(True)
        self.enter_simulator.setObjectName("enter_simulator")
        self.verticalLayout_2.addWidget(self.enter_simulator)
        self.settings = QtWidgets.QPushButton(Form)
        font = QtGui.QFont()
        font.setFamily("华文中宋")
        font.setPointSize(20)
        self.settings.setFont(font)
        self.settings.setStyleSheet("color: rgb(0, 85, 255);")
        self.settings.setFlat(True)
        self.settings.setObjectName("settings")
        self.verticalLayout_2.addWidget(self.settings)
        self.about = QtWidgets.QPushButton(Form)
        font = QtGui.QFont()
        font.setFamily("华文中宋")
        font.setPointSize(20)
        self.about.setFont(font)
        self.about.setStyleSheet("color: rgb(0, 85, 255);")
        self.about.setAutoDefault(False)
        self.about.setDefault(False)
        self.about.setFlat(True)
        self.about.setObjectName("about")
        self.verticalLayout_2.addWidget(self.about)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.open_folder.setText(_translate("Form", "打开文件夹"))
        self.enter_simulator.setText(_translate("Form", "进入模拟器"))
        self.settings.setText(_translate("Form", "设置"))
        self.about.setText(_translate("Form", "关于"))

