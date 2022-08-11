# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\RM_UI_Simulator\qtui\player_ui\new_variable.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_NewVariableDialog(object):
    def setupUi(self, NewVariableDialog):
        NewVariableDialog.setObjectName("NewVariableDialog")
        NewVariableDialog.resize(400, 126)
        self.gridLayout = QtWidgets.QGridLayout(NewVariableDialog)
        self.gridLayout.setObjectName("gridLayout")
        self.label = QtWidgets.QLabel(NewVariableDialog)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(NewVariableDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 3, 1, 1, 1)
        self.var_name_input = QtWidgets.QLineEdit(NewVariableDialog)
        self.var_name_input.setObjectName("var_name_input")
        self.gridLayout.addWidget(self.var_name_input, 0, 1, 1, 1, QtCore.Qt.AlignRight)
        self.label_2 = QtWidgets.QLabel(NewVariableDialog)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 2, 0, 1, 1)
        self.comboBox = QtWidgets.QComboBox(NewVariableDialog)
        self.comboBox.setObjectName("comboBox")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.gridLayout.addWidget(self.comboBox, 2, 1, 1, 1, QtCore.Qt.AlignRight)

        self.retranslateUi(NewVariableDialog)
        self.buttonBox.accepted.connect(NewVariableDialog.accept)
        self.buttonBox.rejected.connect(NewVariableDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(NewVariableDialog)

    def retranslateUi(self, NewVariableDialog):
        _translate = QtCore.QCoreApplication.translate
        NewVariableDialog.setWindowTitle(_translate("NewVariableDialog", "Dialog"))
        self.label.setText(_translate("NewVariableDialog", "变量名称"))
        self.var_name_input.setText(_translate("NewVariableDialog", "Var"))
        self.label_2.setText(_translate("NewVariableDialog", "变量类型"))
        self.comboBox.setItemText(0, _translate("NewVariableDialog", "int"))
        self.comboBox.setItemText(1, _translate("NewVariableDialog", "float"))
        self.comboBox.setItemText(2, _translate("NewVariableDialog", "char *"))

