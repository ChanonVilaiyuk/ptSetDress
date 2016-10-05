#!/usr/bin/env python
# -- coding: utf-8 --

#Import python modules
import os, sys
from datetime import datetime
from functools import partial
import logging 

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)

for handler in logger.handlers[::-1] : 
    if type(handler).__name__ == 'MayaGuiLogHandler' : 
        handler.setFormatter(formatter)

# logger.addHandler(streamHandler)

#Import GUI
from PySide import QtCore
from PySide import QtGui
from PySide import QtUiTools
from shiboken import wrapInstance

# Import Maya module
import maya.OpenMayaUI as mui
import maya.cmds as mc
import maya.mel as mm

# custom modules 
from tool.utils import entityInfo, mayaTools, fileUtils, icon
from tool.setDress.utils import sd_utils
reload(sd_utils)

debug = False

moduleFile = sys.modules[__name__].__file__
moduleDir = os.path.dirname(moduleFile).replace('\\', '/')
sys.path.append(moduleDir)


def getMayaWindow():
    ptr = mui.MQtUtil.mainWindow()
    if ptr is not  None:
        return wrapInstance(long(ptr), QtGui.QMainWindow)

class MyForm(QtGui.QMainWindow):

    def __init__(self, parent=None):
        self.count = 0
        #Setup Window
        super(MyForm, self).__init__(parent)

        self.mayaUI = 'setCheckUI'
        deleteUI(self.mayaUI)

        # read .ui directly
        self.showUI()
        self.ui.setWindowTitle('Scene Assembly Asset Conflict v.0.0.1')

        self.initSignals()
        self.initFuctions()

    def showUI(self) : 
        loader = QtUiTools.QUiLoader()
        loader.setWorkingDirectory(moduleDir)

        f = QtCore.QFile("%s/checkUI.ui" % moduleDir)
        f.open(QtCore.QFile.ReadOnly)

        self.myWidget = loader.load(f, self)
        self.ui = self.myWidget

        f.close()

        self.ui.show()

    def initFuctions(self) : 
        self.runCheck()
        
    def initSignals(self) : 
        self.ui.adRemove_listWidget.itemSelectionChanged.connect(partial(self.selectObject, 'rig'))
        self.ui.hide_listWidget.itemSelectionChanged.connect(partial(self.selectObject, 'hide'))
        self.ui.show_listWidget.itemSelectionChanged.connect(partial(self.selectObject, 'show'))
        self.ui.confirmRig_pushButton.clicked.connect(self.confirmUsingRig)
        self.ui.hide_pushButton.clicked.connect(partial(self.hideGpu, True))
        self.ui.confirmShow_pushButton.clicked.connect(partial(self.hideGpu, False))
        self.ui.show_pushButton.clicked.connect(partial(self.showGpu, True))
        self.ui.confirmHide_pushButton.clicked.connect(partial(self.showGpu, False))

    def runCheck(self, hidePanel=False): 
        if hidePanel: 
            self.ui.rig_frame.setVisible(False)
            self.ui.hide_frame.setVisible(False)
            self.ui.show_frame.setVisible(False)

        # check lost link rig 
        rigResult = self.setupLostLinkRigList()

        # asset that not supposed to show, but it show 
        hideResult = self.setupAssetHide()

        # asset that supposed to show, but it hidden
        showResult = self.setupAssetShow()

        if not rigResult and not hideResult and not showResult: 
            result = QtGui.QMessageBox.question(self, 'Information', 'Scene Assembly clean. No more visibility conflict.', QtGui.QMessageBox.Ok)

            if result == QtGui.QMessageBox.Ok: 
                deleteUI(self.mayaUI)

    def setupLostLinkRigList(self): 
        missingAds = sd_utils.checkLostLinkADRig()
        self.ui.adRemove_listWidget.clear()
        if missingAds: 
            self.ui.rig_frame.setVisible(True)
            self.ui.adRemove_listWidget.addItem('..')
            self.ui.adRemove_listWidget.addItems([missingAds[a].split('.')[0] for a in missingAds])
            return True

        return False

    def setupAssetHide(self): 
        missSyncOff, missSyncOn = sd_utils.checkHiddenSync()
        self.ui.hide_listWidget.clear()
        if missSyncOff: 
            self.ui.hide_frame.setVisible(True)
            self.ui.hide_listWidget.addItem('..')
            self.ui.hide_listWidget.addItems(missSyncOff)
            return True

        return False

    def setupAssetShow(self): 
        missSyncOff, missSyncOn = sd_utils.checkHiddenSync()
        self.ui.show_listWidget.clear()
        if missSyncOn: 
            self.ui.show_frame.setVisible(True)
            self.ui.show_listWidget.addItem('..')
            self.ui.show_listWidget.addItems(missSyncOn)
            return True

        return False

    def selectObject(self, arg=None): 
        if arg == 'rig': 
            items = self.ui.adRemove_listWidget.selectedItems()

        if arg == 'hide': 
            items = self.ui.hide_listWidget.selectedItems()

        if arg == 'show': 
            items = self.ui.show_listWidget.selectedItems()

        if items: 
            if len(items) > 1: 
                assets = [str(a.text()) for a in items if not str(a.text()) == '..'] 
                mc.select(assets)

            elif len(items) == 1: 
                if str(items[0].text()) == '..': 
                    mc.select(cl=True)
                else: 
                    mc.select(str(items[0].text()))

    def confirmUsingRig(self): 
        items = self.ui.adRemove_listWidget.selectedItems()
        shot = entityInfo.info()
        step = shot.department()
        if items: 
            for item in items: 
                assetName = str(item.text())
                attr = '%s.%s_confirm' % (assetName, step)
                mc.setAttr(attr, True)

        self.runCheck(hidePanel=False)

    def hideGpu(self, state=True): 
        items = self.ui.hide_listWidget.selectedItems()
        assets = [str(a.text()) for a in items if mc.objExists(str(a.text()))]
        sd_utils.setHidden(assets, state)

        self.runCheck(hidePanel=False)

    def showGpu(self, state=True): 
        items = self.ui.show_listWidget.selectedItems()
        assets = [str(a.text()) for a in items if mc.objExists(str(a.text()))]
        sd_utils.setHidden(assets, not state)

        self.runCheck(hidePanel=False)

    def translateUTF8(self, text) : 
        return QtGui.QApplication.translate("ShotPublishUI", text, None, QtGui.QApplication.UnicodeUTF8)
        

def deleteUI(ui) : 
    if mc.window(ui, exists = True) : 
        mc.deleteUI(ui)