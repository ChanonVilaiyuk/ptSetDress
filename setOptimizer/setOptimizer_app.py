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

from tool.utils import entityInfo, mayaTools
reload(entityInfo)
reload(mayaTools)

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

        self.mayaUI = 'SetOptimizeUI'
        self.showUI()
        self.ui.show()
        # self.ui.setWindowTitle('PT Vray Matte Export v.1.2')

        self.levels = ['vProxy', 'Cache', 'Anim', 'Render']
        self.levelMap = {'vProxy': 'vProxy', 'Cache': 'cache', 'Anim': 'anim', 'Render': 'render'}
        self.setGrp = 'set'

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
        self.setupUI()

    def initSignals(self) : 
        # select 
        self.ui.selectHidden_pushButton.clicked.connect(partial(self.selectLocs, 'hidden'))
        self.ui.selectEmptyLoc_pushButton.clicked.connect(partial(self.selectLocs, 'empty'))
        self.ui.selectAll_pushButton.clicked.connect(partial(self.selectLocs, 'all'))
        self.ui.search_lineEdit.returnPressed.connect(partial(self.selectLocs, 'search'))
        self.ui.selectSameAsset_pushButton.clicked.connect(partial(self.selectLocs, 'sameAsset'))
        self.ui.selectLocator_pushButton.clicked.connect(partial(self.selectLocs, 'root'))
        self.ui.selectUnmatchTransform_pushButton.clicked.connect(partial(self.selectLocs, 'unmatch'))

        # replace 
        self.ui.setLo_pushButton.clicked.connect(partial(self.replaceReference, 'lo'))
        self.ui.setMd_pushButton.clicked.connect(partial(self.replaceReference, 'md'))
        self.ui.setHi_pushButton.clicked.connect(partial(self.replaceReference, 'hi'))

        # hide 
        self.ui.hide_pushButton.clicked.connect(partial(self.showHide, 'hide'))
        self.ui.show_pushButton.clicked.connect(partial(self.showHide, 'show'))
        self.ui.unload_pushButton.clicked.connect(partial(self.unloadReference, False))
        self.ui.remove_pushButton.clicked.connect(partial(self.unloadReference, True))

        # utils 
        self.ui.applyAssetTransform_pushButton.clicked.connect(partial(self.applyTransform, 'asset'))
        self.ui.applyShotTransform_pushButton.clicked.connect(partial(self.applyTransform, 'shot'))

    def setupUI(self) : 
        self.setLevel()
        # lock unload 
        self.ui.unload_pushButton.setEnabled(False)

    def setLevel(self) : 
        self.ui.level_comboBox.clear()
        self.ui.level_comboBox.addItems(self.levels)

    def selectLocs(self, mode='hidden') : 
        locs = []

        if mode == 'all' : 
            locs = self.getLocator()

        if mode == 'hidden' : 
            locs = self.getHidden()

        if mode == 'empty' : 
            locs = self.getEmptyLocator()

        if mode == 'search' : 
            locs = self.getSearch()

        if mode == 'root' : 
            locs = self.getRoot()

        if mode == 'sameAsset' : 
            locs = self.getSameAsset()

        if mode == 'unmatch': 
            locs = self.getUnMatchTransform()

        if locs : 
            mc.select(locs)


    def replaceReference(self, mode='md') : 
        lod = mode
        locs = self.getRoot()
        level = self.levelMap[str(self.ui.level_comboBox.currentText())]
        if self.ui.custom_checkBox.isChecked(): 
            level = str(self.ui.custom_lineEdit.text())
        forceReplace = self.ui.force_checkBox.isChecked()
        skipHidden = self.ui.hidden_checkBox.isChecked()
        validLocs = []

        if skipHidden : 
            for loc in locs : 
                attr = '%s.%s' % (loc, 'hidden')

                if mc.objExists(attr) : 
                    hidden = mc.getAttr(attr)

                    if not hidden : 
                        validLocs.append(loc)

        else : 
            validLocs = locs

        if validLocs : 
            report = sd_utils.build(locs=validLocs, level=level, lod=lod, forceReplace=forceReplace, returnValue='loc')

            if report : 
                mc.confirmDialog( title='Warning', message='There are %s asset(s) missing. See script editor for details.' % len(report), button=['OK'])
                missingLocs = [a[1] for a in report]
                mc.select(missingLocs)

            else : 
                mc.confirmDialog( title='Complete', message='Complete', button=['OK'])

    def showHide(self, mode='hide') : 
        locs = self.getRoot()
        setHidden = self.ui.setHidden_checkBox.isChecked()

        if mode == 'show' : 
            vis = True 

        if mode == 'hide' : 
            vis = False

        for loc in locs : 
            mc.setAttr('%s.visibility' % loc, vis)

            if setHidden : 
                if mc.objExists('%s.hidden' % loc) : 
                    mc.setAttr('%s.hidden' % loc, not vis)

        mc.select(locs)

    def unloadReference(self, remove=False) : 
        objs = mc.ls(sl=True)
        pathInfo = dict()
        setHidden = self.ui.setHidden_checkBox.isChecked()
        locs = []

        for obj in objs : 
            if mc.referenceQuery(obj, isNodeReferenced = True) : 
                path = mc.referenceQuery(obj, f = True)

                if not path in pathInfo.keys() : 
                    loc = self.getRoot([obj])
                    rnNode = mc.referenceQuery(obj, referenceNode=True)
                    pathInfo.update({path: {'rnNode': rnNode, 'loc': loc}})

            else : 
                if mc.listRelatives(obj, s=True, f=True, type='locator') : 
                    info = sd_utils.findReferenceChild(obj)

                    for path, rnNode in info.iteritems() : 
                        pathInfo.update({path: {'rnNode': rnNode, 'loc': [obj]}})


        if pathInfo : 
            for path, item in pathInfo.iteritems() : 
                rnNode = item['rnNode']
                loc = item['loc']
                
                if remove : 
                    mc.file(path, rr=True)

                else : 
                    mc.file(path, unloadReference=rnNode)


                if setHidden : 
                    if loc : 
                        if mc.objExists('%s.hidden' % loc[0]) : 
                            mc.setAttr('%s.hidden' % loc[0], True)

                locs.append(loc[0])

        mc.select(locs)


    def getHidden(self) : 
        locs = self.getLocator()
        hiddenLocs = []

        for each in locs : 
            attr = '%s.%s' % (each, 'hidden')

            if mc.objExists(attr) : 
                hidden = mc.getAttr(attr)

                if hidden : 
                    hiddenLocs.append(each)

        return hiddenLocs

    def getLocator(self, longname=False) : 
        # if no select 
        sels = mc.ls(sl=True, l=longname)
        allLocs = []

        if not sels : 
            if mc.objExists(self.setGrp) : 
                rootLocs = self.getRootLocs()

                for rootLoc in rootLocs : 
                    locs = sd_utils.getSceneLocator(rootLoc)

                    allLocs = allLocs + locs 

        if sels : 
            for sel in sels : 
                locs = sd_utils.getSceneLocator(sel)

                allLocs = allLocs + locs 

        return allLocs

    def getLocReferenceAttr(self) : 
        locs = self.getLocator(longname=True)
        locInfo = dict()

        for loc in locs : 
            attr = '%s.reference' % loc 
            ref = ''

            if mc.objExists(attr) : 
                ref = mc.getAttr(attr)

            if not ref in locInfo.keys() : 
                locInfo.update({ref: [loc]})

            if ref in locInfo.keys() : 
                locInfo[ref].append(loc)

        return locInfo


    def getRootLocs(self) : 
        if mc.objExists(self.setGrp) : 
            rootLocs = mc.listRelatives(self.setGrp, c=True)

            return rootLocs


    def getEmptyLocator(self) : 
        emptyLocs = []
        locs = self.getLocator()
            
        for loc in locs : 
            childs = mc.listRelatives(loc, ad=True)
            empty = True 
            
            for child in childs : 
                if mc.referenceQuery(child, isNodeReferenced = True) : 
                    empty = False 
                    break         
            
            if empty : 
                emptyLocs.append(loc)

        return emptyLocs 

    def getSearch(self) : 
        key = str(self.ui.search_lineEdit.text())
        sels = mc.ls(key)
        locs = [a for a in sels if mc.objExists('%s.reference' % a)]

        return locs

    def getSameAsset(self) : 
        objs = mc.ls(sl=True)
        mc.select(cl=True)
        refs = self.getLocReferenceAttr()
        targetLocs = []

        if objs : 
            locs = self.getRoot(objs)

            for loc in locs : 
                attr = '%s.reference' % loc 

                if mc.objExists(attr) : 
                    ref = mc.getAttr(attr)

                    if ref in refs.keys() : 
                        targetLocs = targetLocs + refs[ref]

        return targetLocs

    def getUnMatchTransform(self): 
        assetAttr = 'assetTransform'
        shotAttr = 'shotTransform'
        emptyLocs = []
        locs = self.getLocator()
        unmatch = []

        for loc in locs: 
            locAssetAttr = '%s.%s' % (loc, assetAttr)
            locShotAttr = '%s.%s' % (loc, shotAttr)

            if mc.objExists(locAssetAttr) and mc.objExists(locShotAttr): 
                strAssetTransform = mc.getAttr(locAssetAttr)    
                strShotTransform = mc.getAttr(locShotAttr)
                
                if not strAssetTransform == strShotTransform: 
                    unmatch.append(loc)
                    print loc

        return unmatch 

    def getRoot(self, objs=[]) : 
        if not objs : 
            objs = mc.ls(sl=True)

        locs = []
        validLocs = []

        if objs : 
            for obj in objs : 
                loc = sd_utils.findParent(obj)

                if loc : 
                    if not loc in locs : 
                        locs.append(loc)

        if locs : 
            attr = 'parent' 

            for loc in locs : 
                if mc.objExists('%s.%s' % (loc, attr)) : 
                    if not mc.getAttr('%s.%s' % (loc, attr)) : 
                        validLocs.append(loc)

                # disable this for new set 
                else : 
                    validLocs.append(loc)

            return validLocs

    def applyTransform(self, entity): 
        assetAttr = 'assetTransform'
        shotAttr = 'shotTransform'
        locs = self.getRoot()
        failed = []

        for loc in locs: 
            locAssetAttr = '%s.%s' % (loc, assetAttr)
            locShotAttr = '%s.%s' % (loc, shotAttr)
            success = False

            if mc.objExists(locAssetAttr) and mc.objExists(locShotAttr): 
                strAssetTransform = mc.getAttr(locAssetAttr)    
                strShotTransform = mc.getAttr(locShotAttr)
                assetTransform = self.getTransform(strAssetTransform)
                shotTransform = self.getTransform(strShotTransform)

                if entity == 'asset': 
                    if assetTransform: 
                        mc.setAttr('%s.translate' % loc, assetTransform['translate'][0][0], assetTransform['translate'][0][1], assetTransform['translate'][0][2])
                        mc.setAttr('%s.rotate' % loc, assetTransform['rotate'][0][0], assetTransform['rotate'][0][1], assetTransform['rotate'][0][2])
                        mc.setAttr('%s.scale' % loc, assetTransform['scale'][0][0], assetTransform['scale'][0][1], assetTransform['scale'][0][2])
                        success = True
                        logger.info('move %s success' % loc)

                if entity == 'shot': 
                    if shotTransform: 
                        mc.setAttr('%s.translate' % loc, shotTransform['translate'][0][0], shotTransform['translate'][0][1], shotTransform['translate'][0][2])
                        mc.setAttr('%s.rotate' % loc, shotTransform['rotate'][0][0], shotTransform['rotate'][0][1], shotTransform['rotate'][0][2])
                        mc.setAttr('%s.scale' % loc, shotTransform['scale'][0][0], shotTransform['scale'][0][1], shotTransform['scale'][0][2])
                        success = True
                        logger.info('move %s success' % loc)

            if not success: 
                failed.append(loc)


        if failed: 
            logger.info('Failed to apply %s locs' % (len(failed)))

            for each in failed: 
                logger.info(each)

    def getTransform(self, data): 
        transform = eval(data)

        if transform.get('translate', False) and transform.get('rotate', False) and transform.get('scale', False): 
            return transform










def deleteUI(ui) : 
    if mc.window(ui, exists=True) : 
        mc.deleteUI(ui)
        deleteUI(ui)

        