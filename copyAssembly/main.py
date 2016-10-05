#Import python modules
import os, sys

#Import GUI
from PySide import QtCore
from PySide import QtGui
from PySide import QtUiTools
from shiboken import wrapInstance

# Import Maya module
import maya.OpenMayaUI as mui
import maya.cmds as mc
import maya.mel as mm

from tool.utils import fileUtils
from tool.sceneAssembly import asm_utils as asmUtils
reload(fileUtils)
reload(asmUtils)

moduleFile = sys.modules[__name__].__file__
moduleDir = os.path.dirname(moduleFile)
sys.path.append(moduleDir)

def getMayaWindow():
    ptr = mui.MQtUtil.mainWindow()
    if ptr is not  None:
        # ptr = mui.MQtUtil.mainWindow()
        return wrapInstance(long(ptr), QtGui.QMainWindow)

def deleteUI(ui) : 
    if mc.window(ui, exists = True) : 
        mc.deleteUI(ui)

class MyForm(QtGui.QMainWindow):

    def __init__(self, parent=None):
        #Setup Window
        super(MyForm, self).__init__(parent)
        self.runUI()
        self.initialUI()
        self.initConnect()

    def runUI(self):
        self.mayaUI = 'copyAssemblyUI'
        deleteUI(self.mayaUI)

        # read .ui directly
        loader = QtUiTools.QUiLoader()
        loader.setWorkingDirectory(moduleDir)

        f = QtCore.QFile("%s/ui.ui" % moduleDir)
        f.open(QtCore.QFile.ReadOnly)

        self.myWidget = loader.load(f, self)
        self.ui = self.myWidget

        f.close()

        self.ui.show()

    def initConnect(self):
        self.ui.pathLineEdit.editingFinished.connect(self.listCopy)
        self.ui.searchLineEdit.textEdited.connect(self.search)
        self.ui.copyPushButton.clicked.connect(self.copy)
        self.ui.pastePushButton.clicked.connect(self.paste)

        self.ui.overrideCheckBox.toggled.connect(self.chkOverride)

    def initialUI(self):
        path = 'O:/pipeline/tmp/asmClipboard'
        self.ui.pathLineEdit.setText(path)
        self.getUser()
        self.listCopy()
        

    def listCopy(self):
        self.ui.copyListWidget.clear()
        copylist = []

        user     = str(self.ui.userLineEdit.text())
        path     = str(self.ui.pathLineEdit.text())
        copylist = fileUtils.listFile(path)
        
        verlist  = [ int(n.split('_')[-1].split('.')[0]) for n in copylist if n.split('_')[-1].split('.')[0].isdigit()  ]
        verlist.sort()
        version  = verlist[-1] + 1
        logName  = '%s_asm_%03d' %(user,version)

        self.ui.copyListWidget.addItems(copylist)
        self.ui.filenameLineEdit.setText(logName)

    def getUser(self):
        user = mc.optionVar(q = 'PTuser')
        self.ui.userLineEdit.setText(user)

    def chkOverride(self):

        if self.ui.overrideCheckBox.isChecked():
            self.ui.filenameLineEdit.setEnabled(True)
        if not self.ui.overrideCheckBox.isChecked():
            self.ui.filenameLineEdit.setEnabled(False)

    def copy(self):
        path     = str(self.ui.pathLineEdit.text())
        user     = str(self.ui.userLineEdit.text())
        copylist = fileUtils.listFile(path)
        verlist  = [ int(n.split('_')[-1].split('.')[0]) for n in copylist if n.split('_')[-1].split('.')[0].isdigit() ]
        verlist.sort()
        version  = verlist[-1] + 1

        if not self.ui.overrideCheckBox.isChecked():
            logPath  = '%s/%s_asm_%03d.db' %(path,user,version)

        if self.ui.overrideCheckBox.isChecked():
            filename = str(self.ui.filenameLineEdit.text())
            logPath  = '%s/%s.db' %(path,filename)

        logPath  = logPath.replace('\\','/')

        # print logPath

        sel   = mc.ls(sl=True,type='assemblyReference')
        allAR = dict()

        # print sel

        for ar in sel:
            if ':' in ar:
                arParent = ar.split('_NS')[0]

                if not allAR.has_key(arParent):
                    path = mc.getAttr('%s.definition' %arParent)

                    t = list(mc.getAttr('%s.t' %arParent)[0])
                    r = list(mc.getAttr('%s.r' %arParent)[0])
                    s = list(mc.getAttr('%s.s' %arParent)[0])

                    allAR[arParent] = {'definition': path, 't' : t, 'r' : r, 's' : s ,'type': 'parent'}

                path = mc.getAttr('%s.definition' %ar)

                t = list(mc.getAttr('%s.t' %ar)[0])
                r = list(mc.getAttr('%s.r' %ar)[0])
                s = list(mc.getAttr('%s.s' %ar)[0])

                if not allAR[arParent].has_key('child'):
                    allAR[arParent]['child'] = dict()

                allAR[arParent]['child'][ar] = {'definition': path, 't' : t, 'r' : r, 's' : s }

            else:
                path = mc.getAttr('%s.definition' %ar)

                t = list(mc.getAttr('%s.t' %ar)[0])
                r = list(mc.getAttr('%s.r' %ar)[0])
                s = list(mc.getAttr('%s.s' %ar)[0])

                allAR[ar] = {'definition': path, 't' : t, 'r' : r, 's' : s ,'type': 'child'}

        fileUtils.ymlDumper(logPath, allAR)

        if os.path.exists(logPath):
            self.listCopy()

    def paste(self):
        path = str(self.ui.pathLineEdit.text())
        item = self.ui.copyListWidget.currentItem()
        name = str(item.text())
        ars  = []

        logPath = '%s/%s' %(path,name)

        if os.path.exists(logPath):
            log = fileUtils.ymlLoader(logPath)

            for ar in log.keys():
                adName = log[ar]['definition'].split('/')[-1].split('_AD')[0]
                if mc.objExists('%s*' %(adName)):
                    num = len(mc.ls('%s*' %(adName)))+1
                else:
                    num = 1

                arName = asmUtils.createARNode('%s%d_AD_AR' %(adName,num))
                asmUtils.setARDefinitionPath(arName,log[ar]['definition'])

                mc.setAttr('%s.t' %arName, log[ar]['t'][0],log[ar]['t'][1],log[ar]['t'][2])
                mc.setAttr('%s.r' %arName, log[ar]['r'][0],log[ar]['r'][1],log[ar]['r'][2])
                mc.setAttr('%s.s' %arName, log[ar]['s'][0],log[ar]['s'][1],log[ar]['s'][2])

                if log[ar]['type'] == 'parent':
                    asmUtils.setActiveRep(arName,'AR')
                    gpuList = mc.listRelatives(arName,children=True)
                    
                    for child in log[ar]['child'].keys():
                        mc.setAttr('%s_NS:%s.t' %(arName,child.split(':')[-1]), log[ar]['child'][child]['t'][0],log[ar]['child'][child]['t'][1],log[ar]['child'][child]['t'][2])
                        mc.setAttr('%s_NS:%s.r' %(arName,child.split(':')[-1]), log[ar]['child'][child]['r'][0],log[ar]['child'][child]['r'][1],log[ar]['child'][child]['r'][2])
                        mc.setAttr('%s_NS:%s.s' %(arName,child.split(':')[-1]), log[ar]['child'][child]['s'][0],log[ar]['child'][child]['s'][1],log[ar]['child'][child]['s'][2])

                asmUtils.setAllActiveRep(arName)
                ars.append(arName)

            mc.select(ars)

        if self.ui.delAfterCheckBox.isChecked():
            os.remove(logPath)

    def search(self):
        self.ui.copyListWidget.clear()

        path     = str(self.ui.pathLineEdit.text())
        txt      = str(self.ui.searchLineEdit.text())
        copylist = fileUtils.listFile(path)

        for copy in copylist:
            if txt in copy:
                self.ui.copyListWidget.addItem(copy)