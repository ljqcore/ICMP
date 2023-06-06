# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'frame.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.
import threading
import socket

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTextEdit

from ping import ping
from tracert import tracert


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(791, 514)
        self.scrollArea = QtWidgets.QScrollArea(Form)
        self.scrollArea.setGeometry(QtCore.QRect(0, 30, 791, 501))
        self.scrollArea.setStyleSheet("#scrollArea{\n"
                                      "    background-color: rgb(0, 0, 0);\n"
                                      "}")
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 789, 499))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.textEdit = TextEdit(self.scrollAreaWidgetContents)
        self.textEdit.setGeometry(QtCore.QRect(0, 0, 801, 501))
        self.textEdit.setStyleSheet("#textEdit{\n"
                                    "    \n"
                                    "    font: 10pt \"Arial\";\n"
                                    "    font-color:rgb(255, 255, 255);\n"
                                    "    background-color:rgb(0, 0, 0);\n"
                                    "    color: rgb(255, 255, 255);\n"
                                    "}")
        self.textEdit.setObjectName("textEdit")
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.label = QtWidgets.QLabel(Form)
        self.label.setGeometry(QtCore.QRect(0, 0, 791, 31))
        self.label.setStyleSheet("#label{\n"
                                 "    background-color:rgb(0, 0, 0);\n"
                                 "    font: 75 10pt \"Arial\";\n"
                                 "    color: rgb(255, 255, 255);\n"
                                 "}")
        self.label.setObjectName("label")

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.label.setText(_translate("Form", " 基于ICMP的Ping和Tracert"))


class TextEdit(QTextEdit):
    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if event.key() in (Qt.Key_Enter, Qt.Key_Return):
            text = self.toPlainText()
            lines = text.split('\n')
            last_line = lines[-2]  # -1 is always an empty string
            words = last_line.split(' ')
            print(words)
            if words[0] == 'ping':
                tx = ping(words[1])
                self.insertPlainText(tx)
            elif words[0] == 'tracert':
                tx = tracert(words[1])
                self.insertPlainText(tx)
                # thread = threading.Thread(target=lambda words:self.insertPlainText(tracert(words[1])))

                # thread = threading.Thread(target=lambda words: (tracert(words[1])))
                # tx = tracert(host)

            else:
                print("请重新输入")