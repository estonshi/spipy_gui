# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'param_setting.ui'
#
# Created by: PyQt5 UI code generator 5.15.0
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Settings(object):
    def setupUi(self, Settings):
        Settings.setObjectName("Settings")
        Settings.resize(385, 440)
        Settings.setDocumentMode(False)
        self.centralwidget = QtWidgets.QWidget(Settings)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.widget_11 = QtWidgets.QWidget(self.centralwidget)
        self.widget_11.setObjectName("widget_11")
        self.horizontalLayout_11 = QtWidgets.QHBoxLayout(self.widget_11)
        self.horizontalLayout_11.setContentsMargins(-1, 0, -1, 0)
        self.horizontalLayout_11.setObjectName("horizontalLayout_11")
        self.label_9 = QtWidgets.QLabel(self.widget_11)
        self.label_9.setObjectName("label_9")
        self.horizontalLayout_11.addWidget(self.label_9)
        self.lineEdit_5 = QtWidgets.QLineEdit(self.widget_11)
        self.lineEdit_5.setObjectName("lineEdit_5")
        self.horizontalLayout_11.addWidget(self.lineEdit_5)
        self.comboBox = QtWidgets.QComboBox(self.widget_11)
        self.comboBox.setObjectName("comboBox")
        self.horizontalLayout_11.addWidget(self.comboBox)
        self.verticalLayout.addWidget(self.widget_11)
        self.widget = QtWidgets.QWidget(self.centralwidget)
        self.widget.setObjectName("widget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.widget)
        self.horizontalLayout.setContentsMargins(-1, 0, -1, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(self.widget)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.lineEdit = QtWidgets.QLineEdit(self.widget)
        self.lineEdit.setObjectName("lineEdit")
        self.horizontalLayout.addWidget(self.lineEdit)
        self.pushButton = QtWidgets.QPushButton(self.widget)
        self.pushButton.setObjectName("pushButton")
        self.horizontalLayout.addWidget(self.pushButton)
        self.verticalLayout.addWidget(self.widget)
        self.widget_5 = QtWidgets.QWidget(self.centralwidget)
        self.widget_5.setObjectName("widget_5")
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout(self.widget_5)
        self.horizontalLayout_5.setContentsMargins(-1, 0, -1, 0)
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.label_5 = QtWidgets.QLabel(self.widget_5)
        self.label_5.setObjectName("label_5")
        self.horizontalLayout_5.addWidget(self.label_5)
        self.lineEdit_4 = QtWidgets.QLineEdit(self.widget_5)
        self.lineEdit_4.setObjectName("lineEdit_4")
        self.horizontalLayout_5.addWidget(self.lineEdit_4)
        self.verticalLayout.addWidget(self.widget_5)
        self.widget_2 = QtWidgets.QWidget(self.centralwidget)
        self.widget_2.setObjectName("widget_2")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.widget_2)
        self.horizontalLayout_2.setContentsMargins(-1, 0, -1, 0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_2 = QtWidgets.QLabel(self.widget_2)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_2.addWidget(self.label_2)
        self.lineEdit_2 = QtWidgets.QLineEdit(self.widget_2)
        self.lineEdit_2.setObjectName("lineEdit_2")
        self.horizontalLayout_2.addWidget(self.lineEdit_2)
        self.pushButton_2 = QtWidgets.QPushButton(self.widget_2)
        self.pushButton_2.setObjectName("pushButton_2")
        self.horizontalLayout_2.addWidget(self.pushButton_2)
        self.verticalLayout.addWidget(self.widget_2)
        self.widget_4 = QtWidgets.QWidget(self.centralwidget)
        self.widget_4.setObjectName("widget_4")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout(self.widget_4)
        self.horizontalLayout_4.setContentsMargins(-1, 0, -1, 0)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.label_4 = QtWidgets.QLabel(self.widget_4)
        self.label_4.setObjectName("label_4")
        self.horizontalLayout_4.addWidget(self.label_4)
        self.lineEdit_3 = QtWidgets.QLineEdit(self.widget_4)
        self.lineEdit_3.setObjectName("lineEdit_3")
        self.horizontalLayout_4.addWidget(self.lineEdit_3)
        self.pushButton_3 = QtWidgets.QPushButton(self.widget_4)
        self.pushButton_3.setObjectName("pushButton_3")
        self.horizontalLayout_4.addWidget(self.pushButton_3)
        self.verticalLayout.addWidget(self.widget_4)
        self.widget_3 = QtWidgets.QWidget(self.centralwidget)
        self.widget_3.setObjectName("widget_3")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.widget_3)
        self.horizontalLayout_3.setContentsMargins(-1, 0, -1, 0)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label_3 = QtWidgets.QLabel(self.widget_3)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_3.addWidget(self.label_3)
        self.spinBox = QtWidgets.QSpinBox(self.widget_3)
        self.spinBox.setMaximum(1024)
        self.spinBox.setObjectName("spinBox")
        self.horizontalLayout_3.addWidget(self.spinBox)
        self.spinBox_2 = QtWidgets.QSpinBox(self.widget_3)
        self.spinBox_2.setMaximum(1024)
        self.spinBox_2.setObjectName("spinBox_2")
        self.horizontalLayout_3.addWidget(self.spinBox_2)
        self.verticalLayout.addWidget(self.widget_3)
        self.widget_6 = QtWidgets.QWidget(self.centralwidget)
        self.widget_6.setObjectName("widget_6")
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout(self.widget_6)
        self.horizontalLayout_6.setContentsMargins(-1, 0, -1, 0)
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.label_6 = QtWidgets.QLabel(self.widget_6)
        self.label_6.setObjectName("label_6")
        self.horizontalLayout_6.addWidget(self.label_6)
        self.spinBox_3 = QtWidgets.QSpinBox(self.widget_6)
        self.spinBox_3.setMaximum(1024)
        self.spinBox_3.setObjectName("spinBox_3")
        self.horizontalLayout_6.addWidget(self.spinBox_3)
        self.verticalLayout.addWidget(self.widget_6)
        self.widget_7 = QtWidgets.QWidget(self.centralwidget)
        self.widget_7.setObjectName("widget_7")
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout(self.widget_7)
        self.horizontalLayout_7.setContentsMargins(-1, 0, -1, 0)
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.label_7 = QtWidgets.QLabel(self.widget_7)
        self.label_7.setObjectName("label_7")
        self.horizontalLayout_7.addWidget(self.label_7)
        self.spinBox_4 = QtWidgets.QSpinBox(self.widget_7)
        self.spinBox_4.setMaximum(2014)
        self.spinBox_4.setObjectName("spinBox_4")
        self.horizontalLayout_7.addWidget(self.spinBox_4)
        self.verticalLayout.addWidget(self.widget_7)
        self.widget_8 = QtWidgets.QWidget(self.centralwidget)
        self.widget_8.setObjectName("widget_8")
        self.horizontalLayout_8 = QtWidgets.QHBoxLayout(self.widget_8)
        self.horizontalLayout_8.setContentsMargins(12, 0, -1, 0)
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")
        self.label_8 = QtWidgets.QLabel(self.widget_8)
        self.label_8.setObjectName("label_8")
        self.horizontalLayout_8.addWidget(self.label_8)
        self.doubleSpinBox = QtWidgets.QDoubleSpinBox(self.widget_8)
        self.doubleSpinBox.setMaximum(1.0)
        self.doubleSpinBox.setProperty("value", 0.1)
        self.doubleSpinBox.setObjectName("doubleSpinBox")
        self.horizontalLayout_8.addWidget(self.doubleSpinBox)
        self.verticalLayout.addWidget(self.widget_8)
        self.widget_9 = QtWidgets.QWidget(self.centralwidget)
        self.widget_9.setObjectName("widget_9")
        self.horizontalLayout_9 = QtWidgets.QHBoxLayout(self.widget_9)
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")
        self.checkBox_2 = QtWidgets.QCheckBox(self.widget_9)
        self.checkBox_2.setObjectName("checkBox_2")
        self.horizontalLayout_9.addWidget(self.checkBox_2)
        self.checkBox = QtWidgets.QCheckBox(self.widget_9)
        self.checkBox.setObjectName("checkBox")
        self.horizontalLayout_9.addWidget(self.checkBox)
        self.verticalLayout.addWidget(self.widget_9)
        self.widget_10 = QtWidgets.QWidget(self.centralwidget)
        self.widget_10.setObjectName("widget_10")
        self.horizontalLayout_10 = QtWidgets.QHBoxLayout(self.widget_10)
        self.horizontalLayout_10.setObjectName("horizontalLayout_10")
        self.pushButton_4 = QtWidgets.QPushButton(self.widget_10)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton_4.sizePolicy().hasHeightForWidth())
        self.pushButton_4.setSizePolicy(sizePolicy)
        self.pushButton_4.setSizeIncrement(QtCore.QSize(0, 0))
        self.pushButton_4.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.pushButton_4.setStyleSheet("background-color: rgb(14, 122, 255);\n"
"color: rgb(255, 255, 255);")
        self.pushButton_4.setObjectName("pushButton_4")
        self.horizontalLayout_10.addWidget(self.pushButton_4)
        self.pushButton_5 = QtWidgets.QPushButton(self.widget_10)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton_5.sizePolicy().hasHeightForWidth())
        self.pushButton_5.setSizePolicy(sizePolicy)
        self.pushButton_5.setStyleSheet("background-color: rgba(189, 20, 50, 170);\n"
"color: rgb(255, 255, 255);")
        self.pushButton_5.setObjectName("pushButton_5")
        self.horizontalLayout_10.addWidget(self.pushButton_5)
        self.verticalLayout.addWidget(self.widget_10)
        Settings.setCentralWidget(self.centralwidget)

        self.retranslateUi(Settings)
        QtCore.QMetaObject.connectSlotsByName(Settings)

    def retranslateUi(self, Settings):
        _translate = QtCore.QCoreApplication.translate
        Settings.setWindowTitle(_translate("Settings", "MainWindow"))
        self.label_9.setText(_translate("Settings", "Tag"))
        self.label.setToolTip(_translate("Settings", "<html><head/><body><p><br/></p></body></html>"))
        self.label.setText(_translate("Settings", "TOBESET"))
        self.pushButton.setText(_translate("Settings", "Browser"))
        self.label_5.setToolTip(_translate("Settings", "<html><head/><body><p><br/></p></body></html>"))
        self.label_5.setText(_translate("Settings", "TOBESET"))
        self.label_2.setToolTip(_translate("Settings", "<html><head/><body><p><br/></p></body></html>"))
        self.label_2.setText(_translate("Settings", "TOBESET"))
        self.pushButton_2.setText(_translate("Settings", "Browser"))
        self.label_4.setToolTip(_translate("Settings", "<html><head/><body><p><br/></p></body></html>"))
        self.label_4.setText(_translate("Settings", "TOBESET"))
        self.pushButton_3.setText(_translate("Settings", "Browser"))
        self.label_3.setText(_translate("Settings", "TOBESET"))
        self.label_6.setText(_translate("Settings", "TOBESET"))
        self.label_7.setText(_translate("Settings", "TOBESET"))
        self.label_8.setText(_translate("Settings", "TOBESET"))
        self.checkBox_2.setText(_translate("Settings", "Append to Input H5"))
        self.checkBox.setText(_translate("Settings", "Force Poisson"))
        self.pushButton_4.setText(_translate("Settings", "Save"))
        self.pushButton_5.setText(_translate("Settings", "Cancel"))
