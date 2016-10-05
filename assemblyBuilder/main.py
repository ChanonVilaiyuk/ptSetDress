
import sys,os,time
from string import *

from qtshim import QtCore, QtGui
from qtshim import Signal
from qtshim import wrapinstance

sys.path.append('O:/studioTools/maya/python')

from utils import fileUtils
reload(fileUtils)

from tool.sceneAssembly import asm_utils as asmUtils
reload(asmUtils)

from tool.utils import projectInfo 
reload(projectInfo)

asset = projectInfo.info()

from tool.setDress.assemblyBuilder import ui
reload(ui)

# MAYA UI
import maya.OpenMayaUI as mui
import maya.cmds as mc
import maya.mel as mm

def getMayaWindow():
    ptr = mui.MQtUtil.mainWindow()
    if ptr is None:
        raise RuntimeError('No Maya window found.')
    window = wrapinstance(ptr)
    assert isinstance(window, QtGui.QMainWindow)
    return window



class MyForm(QtGui.QMainWindow):
    def __init__(self,parent=None):
        # QtGui.QWidget.__init__(self,parent)
        super(MyForm, self).__init__(parent)
        
        self.ui = ui.Ui_assemblyBuilderUI()
        self.ui.setupUi(self)

        self.initialUI()
        self.initConnect()

    def initialUI(self):

        self.pathDrive = {  'project' : '',
                            'type' : '',
                            'subtype' : '',
                            'assetName' : '',
                            'step' : '',
                            'task' : '',
                            'filename' : ''         }
        self.arInScene = {}
        self.showList = {}

        self.setProjects()
        self.setARList()
        self.countAR()

    def initConnect(self):
        # self.ui.projectComboBox.activated.connect(self.setTypes)
        self.ui.typeComboBox.activated.connect(self.setSubtype)
        self.ui.subtypeComboBox.activated.connect(self.setAssetListByType)

        self.ui.searchLineEdit.textChanged.connect(self.searchList)
        self.ui.viewComboBox.activated.connect(self.setViewMode)

        self.ui.seperateCheckBox.toggled.connect(self.enabledTLine)
        self.ui.addPushButton.clicked.connect(self.addAsset)

        # self.ui.arListWidget.itemClicked.connect(self.getName)

        self.ui.refreshPushButton.clicked.connect(self.refresh)

        self.ui.replacePushButton.clicked.connect(self.getNameReplaceAsset)

    def setProjects(self):
        self.ui.projectComboBox.clear()
        self.ui.subtypeComboBox.clear()

        prjInfo = fileUtils.readFile('P:/.config/activeProjectConfig')
        prjs = eval(prjInfo)
        prjNames = []

        for p in prjs:
            prjNames.append(p['name'])

        prjNames.sort()
        self.ui.projectComboBox.addItems(prjNames)

    def setSubtype(self):
        self.ui.subtypeComboBox.clear()
        self.showList = {}
        self.pathDrive['project'] = self.ui.projectComboBox.currentText()
        self.pathDrive['type'] = self.ui.typeComboBox.currentText()

        tpPath = asset.getTypePath(self.pathDrive['project'], self.pathDrive['type'])
        
        subs = fileUtils.listFolder(tpPath)
        self.ui.subtypeComboBox.addItems(subs)

    def searchList(self):
        txt = self.ui.searchLineEdit.text()

        if txt:
            sName = {}
            keys = self.showList.keys()

            for key in keys:
                if txt in key:
                    sName[key] = self.showList[key]

            self.showList = sName
        if not txt:
            self.showList = {}

        self.setAssetList()

    def setViewMode(self):
        view = str(self.ui.viewComboBox.currentText())
        if 'List' in view:
            self.ui.assetListWidget.setViewMode(QtGui.QListView.ListMode)
        if 'Icon' in view:
            self.ui.assetListWidget.setViewMode(QtGui.QListView.IconMode)
            self.ui.assetListWidget.setIconSize(QtCore.QSize(80,80))

    def getLastImage(self,dirt):
        # find last image in icon folder
        imgs = fileUtils.listFile(dirt)
        last = 0
        lastimg = ''

        for imgName in imgs:
            if not '.db' in imgName:
                img = dirt +'/'+imgName
                if os.path.getmtime(img) > last:
                    last = os.path.getmtime(img)
                    lastimg = img

        return lastimg

    def setItemListWidget(self,iconPath,iconName,wgName,adPath=''):
        icon = QtGui.QIcon()
        pixmap = QtGui.QPixmap(iconPath)
        icon.addPixmap(pixmap,QtGui.QIcon.Normal,QtGui.QIcon.Off)
        items = QtGui.QListWidgetItem(wgName)
        items.setIcon(icon)
        items.setText(iconName)
        if adPath and not os.path.exists(adPath):
            items.setBackground(QtGui.QColor(255,0,0))
            # RGB 0,255,255 = Red

    def setAssetListByType(self):
        self.showList = {}
        self.setAssetList()

    def setAssetList(self):
        self.ui.assetListWidget.clear()
        
        if not self.showList:
            self.pathDrive['subtype'] = self.ui.subtypeComboBox.currentText()
            stPath = asset.getSubTypePath(self.pathDrive['project'], self.pathDrive['type'],self.pathDrive['subtype'])

            for name in fileUtils.listFolder(stPath) :
                img = self.getLastImage(stPath + '/' + name + '/images/icon')
                adFile = os.path.join(stPath,name,'ref','%s_AD.ma' %name)
                if img :
                    self.showList[name] = { 'icon' : img, 'ad' : adFile }

        if self.showList:
            keys = self.showList.keys()
            keys.sort()

            for name in keys:
                self.setItemListWidget(self.showList[name]['icon'],name,self.ui.assetListWidget,self.showList[name]['ad'])

    def addAsset(self):
        start,x,z = 0,0.0,0.0
        num = int(self.ui.numCreateLineEdit.text())
        sel = self.ui.assetListWidget.currentItem()

        if sel:
            self.pathDrive['assetName'] = sel.text()

            adPath,imgPath = self.getADandIcon()

            if os.path.exists(adPath):

                if mc.objExists('%s*_AD_AR' %(self.pathDrive['assetName'])):

                    same = mc.ls('%s*_AD_AR' %(self.pathDrive['assetName']))
                    start = len(same)

                    num += start

                for i in range(start,num):

                    pre = mc.ls(sl=True)

                    self.createAR(i+1,adPath)

                    if self.ui.seperateCheckBox.isChecked():
                        x,z = self.checkSeperate(pre,x,z)

                self.setARList()
                self.countAR()
                self.setTip()

            else:
                self.setTip('Warning : No Exists File \"%s\"' %(adPath))

        if not sel:
            self.setTip('Warning : Select Asset in List.')

    def checkSeperate(self,pre,x=0,z=0):

        tx = float(self.ui.txLineEdit.text())
        tz = float(self.ui.tzLineEdit.text())

        if len(pre) > 0 and self.pathDrive['assetName'] in pre[-1] :

            x = mc.getAttr('%s.tx' %(pre[-1]))
            z = mc.getAttr('%s.tz' %(pre[-1]))

            x += tx
            z += tz

            mc.move(x,0,z)

        if len(pre) == 0:

            mc.move(0,0,0)

        return x,z

    def enabledTLine(self):
        if not self.ui.seperateCheckBox.isChecked():
            self.ui.txLineEdit.setEnabled(False)
            self.ui.tzLineEdit.setEnabled(False)
        if self.ui.seperateCheckBox.isChecked():
            self.ui.txLineEdit.setEnabled(True)
            self.ui.tzLineEdit.setEnabled(True)

    def setTip(self,txt=''):
        self.ui.tipPlainTextEdit.clear()
        self.ui.tipPlainTextEdit.setPlainText(txt)

    def setARList(self):
        self.ui.arListWidget.clear()
        self.arInScene = {}

        arLists = mc.ls(type='assemblyReference')

        for ar in arLists:

            adPath = mc.getAttr('%s.definition' %(ar))
            adPath = adPath.replace('\\','/')
            adName = adPath.split('/')[-1].split('_AD')[0]

            if not self.arInScene.has_key(adName):
                assetPath = adPath.split('/ref')[0]
                iconDir = assetPath + '/images/icon'
                iconPath = self.getLastImage(iconDir)

                self.arInScene[adName] = {'icon':iconPath,'number':0}

            if self.arInScene.has_key(adName):
                self.arInScene[adName]['number'] += 1

        key = self.arInScene.keys()
        key.sort()

        for k in key:
            name = k + ' x ' + str(self.arInScene[k]['number'])
            icon = self.arInScene[k]['icon']

            self.setItemListWidget(icon,name,self.ui.arListWidget)

    def countAR(self):
        self.ui.countLineEdit.clear()

        ar = mc.ls(type='assemblyReference')

        self.ui.countLineEdit.setText(str(len(ar)))

    def refresh(self):
        self.setARList()
        self.countAR()

    # def getName(self):
    #     sel = mc.ls(sl=True)

    #     self.ui.nameLineEdit.setText( '%s*' %(name.split(' ')[0]))

    def getNameReplaceAsset(self):

        arList = mc.ls(type='assemblyReference')
        sel = self.ui.arListWidget.currentItem()

        if not sel:

            self.setTip('Warning : Select Asset in List.')

        if sel:
            selAsset = sel.text()
            count = 0

            self.pathDrive['assetName'] = selAsset.split(' ')[0]

            arList.sort()

            for ar in arList:

                if selAsset.split(' ')[0] in ar:

                    num = int(ar.split(self.pathDrive['assetName'])[-1].split('_AD_AR')[0])

                    if num > count:
                        count = num

                    adPath = mc.getAttr('%s.definition' %(ar))

            if self.ui.selectRadioButton.isChecked():

                selected = mc.ls(sl=True)

                self.replaceAsset(selected,count,adPath)

            if self.ui.nameRadioButton.isChecked():

                name = self.ui.nameLineEdit.text()

                if name == '':

                    self.setTip('Input in Name Line')

                if not name == '':

                    selected = mc.ls(name,type='assemblyReference')

                    self.replaceAsset(selected,count,adPath)

    def replaceAsset(self,selected,count,adPath):

        for sl in selected:

            count += 1

            arName = self.createAR(count,adPath)

            mc.setAttr('%s.t' %(arName), mc.getAttr('%s.t' %(sl))[0][0], mc.getAttr('%s.t' %(sl))[0][1], mc.getAttr('%s.t' %(sl))[0][2] )
            mc.setAttr('%s.r' %(arName), mc.getAttr('%s.r' %(sl))[0][0], mc.getAttr('%s.r' %(sl))[0][1], mc.getAttr('%s.r' %(sl))[0][2] )
            mc.setAttr('%s.s' %(arName), mc.getAttr('%s.s' %(sl))[0][0], mc.getAttr('%s.s' %(sl))[0][1], mc.getAttr('%s.s' %(sl))[0][2] )

            mc.delete(sl)

    def getADandIcon(self):

        astPath = asset.getAssetNamePath(self.pathDrive['project'], self.pathDrive['type'],self.pathDrive['subtype'],self.pathDrive['assetName'])
        adPath = os.path.join(astPath,'ref','%s_AD.ma' %self.pathDrive['assetName'])
        imgDir = os.path.join(astPath,'images','icon')
        imgPath = self.getLastImage(imgDir)

        return adPath,imgPath

    def createAR(self,count,adPath):
        assemblyNode = '%s%d_AD_AR' %(self.pathDrive['assetName'],count)
        asmUtils.createARNode(assemblyNode)
        asmUtils.setARDefinitionPath(assemblyNode, adPath)
        try:
            asmUtils.setActiveRep(assemblyNode, 'Gpu')
        except RuntimeError as exc:
            self.setTip('RuntimeError : %s' %exc)

        return assemblyNode