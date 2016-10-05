#Import python modules
import os, sys
from functools import partial

import logging 
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

#Import GUI
from PySide import QtCore
from PySide import QtGui
from PySide import QtUiTools
from shiboken import wrapInstance

# Import Maya module
import maya.OpenMayaUI as mui
import maya.cmds as mc
import maya.mel as mm

from tool.utils import entityInfo
reload(entityInfo)

from tool.setDress.utils import sd_utils
reload(sd_utils)

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

        self.mayaUI = 'SetManagerUI'
        self.showUI()
        self.ui.show()
        # self.ui.setWindowTitle('PT Vray Matte Export v.1.2')

        # column
        self.setCols = ['Asset Name', 'Root', 'Current', 'Asset', 'Shot']

        # color 
        self.green = [0, 100, 0]
        self.darkGreen = [0, 40, 0]
        self.red = [100, 0, 0]
        self.darkRed = [40, 0, 0]

        self.initFunctions()
        self.initSignals()

    def showUI(self) : 
        deleteUI(self.mayaUI)

        # read .ui directly
        loader = QtUiTools.QUiLoader()
        loader.setWorkingDirectory(moduleDir)

        f = QtCore.QFile("%s/ui.ui" % moduleDir)
        f.open(QtCore.QFile.ReadOnly)

        self.myWidget = loader.load(f, self)
        self.ui = self.myWidget

        f.close()

    def initFunctions(self) : 
        self.setUI()

    def initSignals(self) : 
        # listWidget
        self.ui.set_tableWidget.itemSelectionChanged.connect(self.listSetInfo)

        # radioButton
        self.ui.compare_radioButton.clicked.connect(self.viewData)
        self.ui.view_radioButton.clicked.connect(self.viewData)
        self.ui.asset_radioButton.clicked.connect(self.viewData)
        self.ui.shot_radioButton.clicked.connect(self.viewData)

        # lineEdit 
        self.ui.asset_lineEdit.returnPressed.connect(partial(self.setAsmRoot, 'asset'))
        self.ui.shot_lineEdit.returnPressed.connect(partial(self.setAsmRoot, 'shot'))

        # checkBox
        self.ui.noShape_checkBox.toggled.connect(self.viewContent)
        self.ui.showAll_checkBox.toggled.connect(self.compareData)

        # pushButton
        self.ui.import_pushButton.clicked.connect(self.importSet)
        self.ui.removeSet_pushButton.clicked.connect(self.removeSet)
        self.ui.merge_pushButton.clicked.connect(self.merge)
        self.ui.setOptimize_pushButton.clicked.connect(self.runOptimizer)

    def setUI(self) : 
        shot = entityInfo.info()
        self.ui.info_label.setText(str(shot.fileName()))

        self.setTable()
        self.listSet()

    def setTable(self) : 
        for i, col in enumerate(self.setCols) : 
            self.insertColumn(i, col)

    def refreshUI(self) : 
        self.listSet()

    def listSet(self) : 
        """ list set name, root, current status """ 
        sets = sd_utils.getAssetAsmLocator()
        self.clearTable()

        if sets : 
            for row, assetName in enumerate(sets) : 
                rootLoc, rootExists = self.getRootLoc(assetName)
                rootColor = self.getStatusColor(rootExists)

                self.insertRow(row, 20)
                self.fillInTable(row, self.setCols.index('Asset Name'), assetName)
                self.fillInTable(row, self.setCols.index('Root'), rootLoc, color=rootColor)

        else : 
            result = QtGui.QMessageBox.question(self,'Error', 'No description file. Publish animation first.', QtGui.QMessageBox.Ok)


    def listSetInfo(self) : 
        """ when click to table item, display asset locator, shot locator, assetRoot, shotRoot """
        data = self.getSelectedRowData()

        if data : 
            setName = data[self.setCols.index('Asset Name')]

            self.setAsmLocator(setName)
            self.setAsmRoot(mode='asset')
            self.setAsmRoot(mode='shot')

            self.viewData()

    def getRootLoc(self, assetName) : 
        rootLoc = sd_utils.getShotSetRootLoc(assetName)

        if mc.objExists(rootLoc) : 
            return (rootLoc, True)

        else : 
            return (rootLoc, False)


    def setAsmLocator(self, assetName) : 
        """ get locator path for asset, shot """ 
        abcAssetHero = sd_utils.getAsmLocator(assetName, mode='asset')
        abcShotHero = sd_utils.getAsmLocator(assetName, mode='shot')

        if os.path.exists(abcAssetHero) : 
            assetText = str(abcAssetHero)
        
        else : 
            assetText = '[File not found] %s' % str(abcAssetHero)

        if os.path.exists(abcShotHero) : 
            shotText = str(abcShotHero)

        else : 
            shotText = '[File not found] %s' % str(abcShotHero)
            
        self.ui.asset_lineEdit.setText(assetText)
        self.ui.shot_lineEdit.setText(shotText)

    def setAsmRoot(self, mode='asset') : 
        """ read path and read for root """ 
        if mode == 'asset' : 
            abcHero = str(self.ui.asset_lineEdit.text())
            pathLineEdit = self.ui.asset_lineEdit
            lineEdit = self.ui.assetRoot_lineEdit

        if mode == 'shot' : 
            abcHero = str(self.ui.shot_lineEdit.text())
            pathLineEdit = self.ui.shot_lineEdit
            lineEdit = self.ui.shotRoot_lineEdit

        if os.path.exists(abcHero) : 
            abcAssetInfo = sd_utils.readAbc(abcHero)
            # replace root |
            root = str(abcAssetInfo[0]).replace('|', '')
            statusColor = self.darkRed 

            if mc.objExists(root) : 
                statusColor = self.darkGreen

            self.setLineEdit(lineEdit, root, statusColor)

        else : 
            statusColor = self.darkRed
            self.setLineEdit(lineEdit, '', statusColor)


    def viewData(self) : 
        if self.ui.compare_radioButton.isChecked() : 
            self.compareData()
            print 'compareData'

        if self.ui.view_radioButton.isChecked() : 
            self.viewContent()
            print 'viewContent'

    def compareData(self) : 
        """ compare between current scene and abcFile """ 
        logger.info('Comparing data ...')
        showAll = self.ui.showAll_checkBox.isChecked()
        selData = self.getSelectedRowData()

        if selData : 
            assetName = selData[self.setCols.index('Asset Name')]
            rootLoc, rootExists = self.getRootLoc(assetName)
            
            if rootExists : 
                abcAssetHero = str(self.ui.asset_lineEdit.text())
                abcShotHero = str(self.ui.shot_lineEdit.text())
                add = None 
                remove = None

                if self.ui.compareCurrent_checkBox.isChecked() : 
                    if abcAssetHero : 
                        if self.ui.asset_radioButton.isChecked() : 
                            add, remove = sd_utils.compareLoc(rootLoc, abcAssetHero)

                    if abcShotHero : 
                        if self.ui.shot_radioButton.isChecked() : 
                            add, remove = sd_utils.compareLoc(rootLoc, abcShotHero)

                else : 
                    add, remove = sd_utils.compareAbc(abcShotHero, abcAssetHero)

                self.ui.compare_listWidget.clear()
                
                if not showAll : 
                    if add : 
                        print 'add', add
                        for item in add : 
                            self.addListWidgetItem(item, color=self.green)

                    if remove : 
                        print 'remove', remove
                        for item in remove : 
                            self.addListWidgetItem(item, color=self.red)

                if showAll : 
                    rootLocs = sd_utils.getSceneLocator(rootLoc)

                    for item in rootLocs : 
                        color = [0, 0, 0]

                        if item in remove : 
                            color = self.red 

                        self.addListWidgetItem(item, color=color)

                    if add : 
                        for item in add : 
                            self.addListWidgetItem(item, color=self.green)

        else : 
            logger.info('No set found')


    def viewContent(self) : 
        if self.ui.asset_radioButton.isChecked() : 
            abcHero = str(self.ui.asset_lineEdit.text())
            logger.info('Reading from %s' % abcHero)
        
        if self.ui.shot_radioButton.isChecked() : 
            abcHero = str(self.ui.shot_lineEdit.text())
            logger.info('Reading from %s' % abcHero)

        if abcHero : 
            contents = sd_utils.readAbc(abcHero)
            self.ui.compare_listWidget.clear()
            noShape = self.ui.noShape_checkBox.isChecked()

            if contents : 
                for item in contents : 
                    if noShape : 
                        if not 'Shape' in item.split('|')[-1] : 
                            self.addListWidgetItem(item)
                    
                    else : 
                        self.addListWidgetItem(item)


    

    # button action =======================================================
    def removeSet(self) : 
        removeAll = self.ui.removeAll_checkBox.isChecked()
        removeLoc = self.ui.removeLoc_checkBox.isChecked()

        data = self.getSelectedRowData()

        if removeAll : 
            removeGrp = 'set'

        else : 
            if data : 
                setName = data[self.setCols.index('Root')]
                removeGrp = setName

        if removeGrp : 
            sd_utils.removeSet(removeGrp=removeGrp, removeLoc=removeLoc)

        self.refreshUI()


    def importSet(self) : 
        abcAssetHero = str(self.ui.asset_lineEdit.text())
        assetRoot = str(self.ui.assetRoot_lineEdit.text())
        abcShotHero = str(self.ui.shot_lineEdit.text())
        shotRoot = str(self.ui.shotRoot_lineEdit.text())
        report = None

        if self.ui.asset_radioButton.isChecked() : 
            abcHero = abcAssetHero
            root = assetRoot

        if self.ui.shot_radioButton.isChecked() :  
            abcHero = abcShotHero
            root = shotRoot

        if os.path.exists(abcHero) : 
            if not mc.objExists(root) : 
                valid = True

                if not assetRoot == shotRoot : 
                    message = 'Asset Root and Shot Root not match. You should not continue. Check set name in animation file'
                    result = mc.confirmDialog( title='Warning', message=message, button=['Cancel', 'Continue. I know the consequences'])
                    valid = False 

                    if result == 'Continue. I know the consequences' : 
                        valid = True 

                if valid : 
                    # import asset
                    locs = sd_utils.importAsmLocator(abcHero)
                    # add hidden attr 
                    sd_utils.addHiddenAttr(locs)
                    # sd_utils.getSceneLocator(rootLoc)

                    if self.ui.autoBuild_checkBox.isChecked() : 
                        report = sd_utils.build(locs)


                    if mc.objExists(root) : 
                        if not mc.objExists(sd_utils.grpSet) : 
                            mc.group(em=True, n=sd_utils.grpSet)

                        mc.parent(root, sd_utils.grpSet)

                    self.refreshUI()
                    QtGui.QMessageBox.question(self,'Complete', 'See script editor for details',QtGui.QMessageBox.Ok)

                    if report : 
                        print 'Missing'

                        for each in report : 
                            print each

            else : 
                result = QtGui.QMessageBox.question(self,'Error', 'Cannot import. %s exists' % root ,QtGui.QMessageBox.Ok)

        else : 
            result = QtGui.QMessageBox.question(self,'Error', 'Path not exists' ,QtGui.QMessageBox.Ok)


    def merge(self) : 
        logger.debug('Merging ...')
        data = self.getSelectedRowData()

        if data : 
            assetName = data[self.setCols.index('Asset Name')]
            root = data[self.setCols.index('Root')]
            logger.debug('assetName %s' % assetName)

            if self.ui.sync_radioButton.isChecked() : 
                logger.debug('Sync')
                removeAsset=True
                buildAsset=True
                mergeMode = 'merge-add'

            if self.ui.position_radioButton.isChecked() : 
                logger.debug('Position')
                removeAsset=False
                buildAsset=False
                mergeMode = 'merge-only'

            if self.ui.asset_radioButton.isChecked() : 
                target = 'asset' 
                abcHero = str(self.ui.asset_lineEdit.text())
                targetRoot = str(self.ui.assetRoot_lineEdit.text())

            if self.ui.shot_radioButton.isChecked() : 
                target = 'shot'
                abcHero = str(self.ui.shot_lineEdit.text())
                targetRoot = str(self.ui.shotRoot_lineEdit.text())

            if target and abcHero : 
                if targetRoot == root : 
                    add, remove = sd_utils.mergeAsmLocator(assetName, target=target, abcFile=abcHero, removeAsset=removeAsset, buildAsset=buildAsset, mergeMode=mergeMode)
                    
                    if self.ui.hidden_checkBox.isChecked() : 
                        locs = sd_utils.getSceneLocator(root)
                        sd_utils.restoreHidden(locs)

                    locs = sd_utils.getSceneLocator(root)
                    sd_utils.syncVis(locs, hidden='vis')

                    mc.confirmDialog( title='Complete', message='Complete', button=['OK'])

                else : 
                    mc.confirmDialog( title='Error', message='Root not match "%s" and "%s". Cannot merge' % (root, targetRoot), button=['OK'])

        else : 
            mc.confirmDialog( title='Error', message='Select a set to merge', button=['OK'])

    def runOptimizer(self): 
        from tool.setDress.setOptimizer import setOptimizer_app as app
        reload(app)

        app = app.MyForm(app.getMayaWindow())

    def getStatusColor(self, status) : 
        if status : 
            return self.green

        else : 
            return self.red


    def setLineEdit(self, lineEdit, text, color) : 
        lineEdit.setText(str(text))
        lineEdit.setStyleSheet('''
                                QLineEdit {
                                border: 2px solid rgb(63, 63, 63);
                                color: rgb(255, 255, 255);
                                background-color: rgb(%s, %s, %s);
                                }''' % (color[0], color[1], color[2]))

    def fillInTable(self, row, column, text, color = [0, 0, 0]) : 
        item = QtGui.QTableWidgetItem()
        item.setText(text)
        item.setBackground(QtGui.QColor(color[0], color[1], color[2]))
        self.ui.set_tableWidget.setItem(row, column, item)


    def fillInTableIcon(self, row, column, text, iconPath) : 
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(iconPath), QtGui.QIcon.Normal, QtGui.QIcon.Off)

        item = QtGui.QTableWidgetItem()
        item.setText(str(text))
        item.setIcon(icon)
        
        self.ui.set_tableWidget.setItem(row, column, item)


    def insertRow(self, row, height) : 
        self.ui.set_tableWidget.insertRow(row)
        self.ui.set_tableWidget.setRowHeight(row, height)

    def insertColumn(self, column, name) : 
        self.ui.set_tableWidget.insertColumn(column)
        item = QtGui.QTableWidgetItem()
        item.setText(name)
        self.ui.set_tableWidget.setHorizontalHeaderItem(column, item)


    def clearTable(self) : 
        rows = self.ui.set_tableWidget.rowCount()

        for each in range(rows) : 
            self.ui.set_tableWidget.removeRow(0)



    def getColumnData(self, column) : 
        counts = self.ui.set_tableWidget.rowCount()
        data = []

        for i in range(counts) : 
            item = self.ui.set_tableWidget.item(i, column)
            if item : 
                data.append(str(item.text()))

        return data 

    def getSelectedRowData(self) : 
        row = self.ui.set_tableWidget.currentRow()
        data = []

        for column, name in enumerate(self.setCols) : 
            item = self.ui.set_tableWidget.item(row, column)

            if item : 
                data.append(str(item.text()))

        return data


    def addListWidgetItem(self, text, iconPath='', color=[0, 0, 0]) : 
        item = QtGui.QListWidgetItem(self.ui.compare_listWidget)
        item.setText(text)
        item.setBackground(QtGui.QColor(color[0], color[1], color[2]))
        size = 16

        if iconPath : 
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(iconPath),QtGui.QIcon.Normal,QtGui.QIcon.Off)
            item.setIcon(icon)
            


        self.ui.compare_listWidget.setIconSize(QtCore.QSize(size, size))
        # QtGui.QApplication.processEvents()



def deleteUI(ui) : 
    if mc.window(ui, exists=True) : 
        mc.deleteUI(ui)
        deleteUI(ui)