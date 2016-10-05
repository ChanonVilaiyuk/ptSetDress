# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'O:\studioTools\maya\python\tool\setDress\setManager2\ui.ui'
#
# Created: Mon Jul 11 19:21:53 2016
#      by: PyQt4 UI code generator 4.9.5
#
# WARNING! All changes made in this file will be lost!

from qtshim import QtCore, QtGui
from qtshim import Signal
from qtshim import wrapinstance


try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_SetManagerUI(object):
    def setupUi(self, SetManagerUI):
        SetManagerUI.setObjectName(_fromUtf8("SetManagerUI"))
        SetManagerUI.resize(533, 600)
        self.centralwidget = QtGui.QWidget(SetManagerUI)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.verticalLayout_4 = QtGui.QVBoxLayout(self.centralwidget)
        self.verticalLayout_4.setObjectName(_fromUtf8("verticalLayout_4"))
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.label = QtGui.QLabel(self.centralwidget)
        self.label.setObjectName(_fromUtf8("label"))
        self.verticalLayout.addWidget(self.label)
        self.set_tableWidget = QtGui.QTableWidget(self.centralwidget)
        self.set_tableWidget.setObjectName(_fromUtf8("set_tableWidget"))
        self.set_tableWidget.setColumnCount(0)
        self.set_tableWidget.setRowCount(0)
        self.verticalLayout.addWidget(self.set_tableWidget)
        self.compare_listWidget = QtGui.QListWidget(self.centralwidget)
        self.compare_listWidget.setObjectName(_fromUtf8("compare_listWidget"))
        self.verticalLayout.addWidget(self.compare_listWidget)
        self.compareCurrent_checkBox = QtGui.QCheckBox(self.centralwidget)
        self.compareCurrent_checkBox.setObjectName(_fromUtf8("compareCurrent_checkBox"))
        self.verticalLayout.addWidget(self.compareCurrent_checkBox)
        self.gridLayout_4 = QtGui.QGridLayout()
        self.gridLayout_4.setObjectName(_fromUtf8("gridLayout_4"))
        self.asset_radioButton = QtGui.QRadioButton(self.centralwidget)
        self.asset_radioButton.setObjectName(_fromUtf8("asset_radioButton"))
        self.gridLayout_4.addWidget(self.asset_radioButton, 0, 0, 1, 1)
        self.shot_radioButton = QtGui.QRadioButton(self.centralwidget)
        self.shot_radioButton.setObjectName(_fromUtf8("shot_radioButton"))
        self.gridLayout_4.addWidget(self.shot_radioButton, 1, 0, 1, 1)
        self.shot_lineEdit = QtGui.QLineEdit(self.centralwidget)
        self.shot_lineEdit.setObjectName(_fromUtf8("shot_lineEdit"))
        self.gridLayout_4.addWidget(self.shot_lineEdit, 1, 1, 1, 1)
        self.asset_lineEdit = QtGui.QLineEdit(self.centralwidget)
        self.asset_lineEdit.setText(_fromUtf8(""))
        self.asset_lineEdit.setObjectName(_fromUtf8("asset_lineEdit"))
        self.gridLayout_4.addWidget(self.asset_lineEdit, 0, 1, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout_4)
        self.gridLayout_7 = QtGui.QGridLayout()
        self.gridLayout_7.setObjectName(_fromUtf8("gridLayout_7"))
        self.import_pushButton = QtGui.QPushButton(self.centralwidget)
        self.import_pushButton.setMinimumSize(QtCore.QSize(0, 30))
        self.import_pushButton.setObjectName(_fromUtf8("import_pushButton"))
        self.gridLayout_7.addWidget(self.import_pushButton, 1, 0, 1, 1)
        self.autoBuild_checkBox = QtGui.QCheckBox(self.centralwidget)
        self.autoBuild_checkBox.setObjectName(_fromUtf8("autoBuild_checkBox"))
        self.gridLayout_7.addWidget(self.autoBuild_checkBox, 0, 0, 1, 1)
        self.merge_pushButton = QtGui.QPushButton(self.centralwidget)
        self.merge_pushButton.setMinimumSize(QtCore.QSize(0, 30))
        self.merge_pushButton.setObjectName(_fromUtf8("merge_pushButton"))
        self.gridLayout_7.addWidget(self.merge_pushButton, 1, 1, 1, 1)
        self.horizontalLayout_6 = QtGui.QHBoxLayout()
        self.horizontalLayout_6.setObjectName(_fromUtf8("horizontalLayout_6"))
        self.sync_radioButton = QtGui.QRadioButton(self.centralwidget)
        self.sync_radioButton.setObjectName(_fromUtf8("sync_radioButton"))
        self.horizontalLayout_6.addWidget(self.sync_radioButton)
        self.position_radioButton = QtGui.QRadioButton(self.centralwidget)
        self.position_radioButton.setObjectName(_fromUtf8("position_radioButton"))
        self.horizontalLayout_6.addWidget(self.position_radioButton)
        self.gridLayout_7.addLayout(self.horizontalLayout_6, 0, 1, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout_7)
        self.verticalLayout.setStretch(1, 1)
        self.verticalLayout.setStretch(2, 2)
        self.verticalLayout_4.addLayout(self.verticalLayout)
        SetManagerUI.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(SetManagerUI)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 533, 21))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        SetManagerUI.setMenuBar(self.menubar)

        self.retranslateUi(SetManagerUI)
        QtCore.QMetaObject.connectSlotsByName(SetManagerUI)

    def retranslateUi(self, SetManagerUI):
        SetManagerUI.setWindowTitle(QtGui.QApplication.translate("SetManagerUI", "Set Manager", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("SetManagerUI", "Sets : ", None, QtGui.QApplication.UnicodeUTF8))
        self.compareCurrent_checkBox.setText(QtGui.QApplication.translate("SetManagerUI", "Compare with Current scene", None, QtGui.QApplication.UnicodeUTF8))
        self.asset_radioButton.setText(QtGui.QApplication.translate("SetManagerUI", "Asset", None, QtGui.QApplication.UnicodeUTF8))
        self.shot_radioButton.setText(QtGui.QApplication.translate("SetManagerUI", "Shot", None, QtGui.QApplication.UnicodeUTF8))
        self.import_pushButton.setText(QtGui.QApplication.translate("SetManagerUI", "Import Locator", None, QtGui.QApplication.UnicodeUTF8))
        self.autoBuild_checkBox.setText(QtGui.QApplication.translate("SetManagerUI", "Auto Build", None, QtGui.QApplication.UnicodeUTF8))
        self.merge_pushButton.setText(QtGui.QApplication.translate("SetManagerUI", "Merge", None, QtGui.QApplication.UnicodeUTF8))
        self.sync_radioButton.setText(QtGui.QApplication.translate("SetManagerUI", "Sync", None, QtGui.QApplication.UnicodeUTF8))
        self.position_radioButton.setText(QtGui.QApplication.translate("SetManagerUI", "Position", None, QtGui.QApplication.UnicodeUTF8))

