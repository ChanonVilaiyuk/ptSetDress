#Import python modules
import os, sys
import sqlite3
from collections import Counter

#Import GUI
from PySide import QtCore
from PySide import QtGui
from PySide import QtUiTools
from shiboken import wrapInstance

# Import Maya module
import maya.OpenMayaUI as mui
import maya.cmds as mc
import maya.mel as mm

from tool.utils import mayaTools 
reload(mayaTools)

moduleFile = sys.modules[__name__].__file__
moduleDir = os.path.dirname(moduleFile)
sys.path.append(moduleDir)


def getMayaWindow():
    ptr = mui.MQtUtil.mainWindow()
    if ptr is not  None:
        # ptr = mui.MQtUtil.mainWindow()
        return wrapInstance(long(ptr), QtGui.QMainWindow)

class MyForm(QtGui.QMainWindow):

    def __init__(self, parent=None):
        self.count = 0
        #Setup Window
        super(MyForm, self).__init__(parent)

        self.mayaUI = 'AssetCheckUI'
        deleteUI(self.mayaUI)

        # read .ui directly
        loader = QtUiTools.QUiLoader()
        loader.setWorkingDirectory(moduleDir)

        f = QtCore.QFile("%s/assetCheck_ui.ui" % moduleDir)
        f.open(QtCore.QFile.ReadOnly)

        self.myWidget = loader.load(f, self)
        self.ui = self.myWidget

        f.close()

        self.ui.show()
        self.ui.setWindowTitle('PT Assembly Asset Check v.1.0')

        self.levels = ['cache', 'vrayProxy', 'vProxy', 'geo']
        self.lods = ['', 'lo', 'md', 'hi']

        self.okIcon = 'O:/studioTools/maya/mel/icons/OK_icon.png'
        self.xIcon = 'O:/studioTools/maya/mel/icons/x_icon.png'


        self.initFunctions()
        self.initSignals()


    def initFunctions(self) : 
        self.setUI()

    def initSignals(self) : 
        self.ui.level_comboBox.currentIndexChanged.connect(self.listAsset)
        self.ui.lod_comboBox.currentIndexChanged.connect(self.listAsset)


    def setUI(self) : 
        self.ui.level_comboBox.clear()
        self.ui.level_comboBox.addItems(self.levels)
        self.ui.level_comboBox.setCurrentIndex(self.levels.index('vProxy'))

        self.ui.lod_comboBox.clear()
        self.ui.lod_comboBox.addItems(self.lods)
        self.ui.lod_comboBox.setCurrentIndex(self.lods.index('md'))

        self.listAsset()


    def listAsset(self) : 
        level = str(self.ui.level_comboBox.currentText())
        lod = str(self.ui.lod_comboBox.currentText())

        files = mayaTools.checkAssemblyDressing(level, lod, echo = True)

        self.ui.listWidget.clear()

        count = 0 
        for each in files : 
            fileName = each[0]
            status = each[1]
            iconPath = self.xIcon
            color = [0, 0, 0]
            display = '%s' % fileName

            if status : 
                iconPath = self.okIcon
                count += 1

            self.addListWidgetItem('listWidget', display, iconPath, color, addIcon = 1)

        info = 'Asset available (%s/%s) asset(s)' % (count, len(files))
        self.ui.info_label.setText(info)


    def addListWidgetItem(self, listWidget, text, iconPath, color, addIcon = 1) : 
        cmd = 'QtGui.QListWidgetItem(self.ui.%s)' % listWidget
        item = eval(cmd)

        if addIcon : 
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(iconPath),QtGui.QIcon.Normal,QtGui.QIcon.Off)
            item.setIcon(icon)

        item.setText(text)
        item.setBackground(QtGui.QColor(color[0], color[1], color[2]))
        size = 16

        cmd2 = 'self.ui.%s.setIconSize(QtCore.QSize(%s, %s))' % (listWidget, size, size)
        eval(cmd2)
        QtGui.QApplication.processEvents()
        


def deleteUI(mayaUI) : 
    if mc.window(mayaUI, exists = True) : 
        mc.deleteUI(mayaUI)

        deleteUI(mayaUI)