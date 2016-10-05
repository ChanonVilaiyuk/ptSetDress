import os
import sys
import maya.cmds as mc
from functools import partial
import maya.mel as mm
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from tool.setDress.utils import asmAssetExport, sd_utils
reload(asmAssetExport)
reload(sd_utils)
from tool.utils import entityInfo, pipelineTools
reload(entityInfo)
reload(pipelineTools)

def run(arg=None) : 
    deleteUI('setTool_win')
    myApp = SetTool()
    myApp.mayaUI()

def deleteUI(ui) : 
    if mc.window(ui, exists = True) : 
        mc.deleteUI(ui)
        deleteUI(ui)

class SetTool() : 
    def __init__(self) : 
        self.win = 'setTool'
        self.ui = '%s_win' % self.win
        self.w = 300
        self.h = 800

    def mayaUI(self) : 
        mc.window(self.ui, t = 'Set Asm Tool v.1.0')
        mc.columnLayout(adj = 1, rs = 4)

        mc.frameLayout(borderStyle = 'etchedIn', l = 'Set Dress')
        mc.columnLayout(adj = 1, rs = 4)
        mc.button(l='Publish Set Locator', h=30, c=partial(self.exportAssetLocator), bgc=(0.4, 0.6, 1))
        mc.button(l='Show Ref', h=30, bgc=(0.5, 0.7, 1))
        mc.setParent('..')
        mc.setParent('..')

        mc.frameLayout(borderStyle = 'etchedIn', l = 'Build')
        mc.columnLayout(adj = 1, rs = 4)
        mc.button(l='Import Locator', h=30, c=partial(self.buildSetAsset), bgc=(0.4, 1, 0.6))
        mc.setParent('..')
        mc.setParent('..')

        mc.frameLayout(borderStyle='etchedIn', l='Shot')
        mc.columnLayout(adj=1, rs = 4)
        mc.button(l='Publish Shot Locator', h=30, c=partial(self.exportShotLocator), bgc=(1, 0.8, 0.4))
        mc.setParent('..')
        mc.setParent('..')

        mc.frameLayout(borderStyle='etchedIn', l='Tech Anim')
        mc.columnLayout(adj=1, rs = 4)
        mc.checkBox('%sBuild_CB' % self.win, l='Auto Build', v=True)
        mc.button(l='Import Asset Locator', h=30, c=partial(self.importAsmLocator, 'asset'), bgc=(1, 0.9, 0.3))
        mc.button(l='Import Shot Locator', h=30, c=partial(self.importAsmLocator, 'shot'), bgc=(1, 0.9, 0.4))
        
        mc.radioCollection('%s_RC' % self.win)
        mc.radioButton('Sync', label='Sync', sl=True)
        mc.radioButton('Position', label='Position')
        mc.button(l='Merge Asset Locator', h=30, c=partial(self.merge, 'asset'), bgc=(1, 0.9, 0.5))
        mc.button(l='Merge Shot Locator', h=30, c=partial(self.merge, 'shot'), bgc=(1, 0.9, 0.6))
        mc.setParent('..')
        mc.setParent('..')

        mc.frameLayout(borderStyle='etchedIn', l='Utils')
        mc.columnLayout(adj=1, rs = 4)
        mc.button(l='Connect Empty', h=30, c=partial(self.connectEmpty), bgc=(1, 0.6, 0.5))
        mc.button(l='Clean Hidden', h=30, c=partial(self.cleanHidden), bgc=(1, 0.5, 0.4))
        mc.checkBox('%sLoc_CB' % self.win, l='Remove Locator', v=True)
        mc.button(l='Remove Set', h=30, c=partial(self.removeSet), bgc=(1, 0.4, 0.3))
        mc.setParent('..')
        mc.setParent('..')

        mc.frameLayout(borderStyle='etchedIn', l='Set Utils')
        mc.columnLayout(adj=1, rs = 4)
        mc.radioCollection('%sCompare_RC' % self.win)
        mc.radioButton('Asset', label='Asset', sl=True)
        mc.radioButton('Shot', label='Shot')
        mc.button(l='What add/remove', h=30, c=partial(self.compareLoc), bgc=(0.2, 1, 0.5))
        mc.setParent('..')
        mc.setParent('..')

        mc.button(l='Refresh', h=30, c=partial(run), bgc=(0.2, 1, 0.6))

        mc.showWindow()
        mc.window(self.ui, e=True, wh=[self.w, self.h])


    def exportAssetLocator(self, arg=None) : 
        asset = entityInfo.info()
        sd_utils.publishWork(ar=True)
        sd_utils.publishAD()
        result = asmAssetExport.run(asset.thisScene())

        if result : 
            message = 'Export asset locator complete!' 
            mc.confirmDialog( title='Warning', message=message, button=['OK'])

    def buildSetAsset(self, arg=None) : 
        locs = sd_utils.importAssetAsmLocator()
        sd_utils.build(locs, level='vProxy', lod='md', forceReplace=False)


    def exportShotLocator(self, arg=None) : 
        pipelineTools.exportShotAsmSet()
        abcHeros = sd_utils.exportShotAsmLocator()

        if abcHeros : 
            if len(abcHeros) == len([a for a in abcHeros if os.path.exists(a)]) : 
                message = 'Export shot locator complete!' 
                mc.confirmDialog( title='Warning', message=message, button=['OK'])

    def removeSet(self, arg=None) : 
        removeLoc = mc.checkBox('%sLoc_CB' % self.win, q=True, v=True)
        sd_utils.removeSet(removeGrp = '|set', removeLoc=removeLoc)

        mc.confirmDialog( title='Complete', message='Remove set complete', button=['OK'])


    def importAsmLocator(self, target='asset', arg=None) : 
        build = mc.checkBox('%sBuild_CB' % self.win, q=True, v=True)
        shotLocs = sd_utils.getShotAsmLocator()
        assetLocs = sd_utils.getAssetAsmLocator()
        warning = [] 
        setGrp = '|set'
        message = 'Complete'

        if not mc.objExists(setGrp) : 
            setGrp = mc.group(em=True, n=setGrp)

        if target == 'asset' : 
            for assetName in assetLocs : 
                abcFile = assetLocs[assetName]
                rootLoc = sd_utils.readAbc(str(abcFile))[0].replace('|', '')

                if not mc.objExists(rootLoc) : 
                    currentObjs = mc.ls(assemblies=True, l=True)
                    locs = sd_utils.importAsmLocator(abcFile)
                    newObjs = mc.ls(assemblies=True, l=True)
                    grpObjs = list(set(newObjs) - set(currentObjs))

                    if build : 
                        sd_utils.build(locs)

                    mc.parent(grpObjs, setGrp)

                else : 
                    warning.append('%s already exists' % rootLoc)

        if target == 'shot' : 
            for assetName in shotLocs : 
                abcFile = shotLocs[assetName]['hero']
                rootLoc = sd_utils.readAbc(str(abcFile))[0].replace('|', '')

                if not mc.objExists(rootLoc) : 
                    currentObjs = mc.ls(assemblies=True, l=True)
                    locs = sd_utils.importAsmLocator(abcFile)
                    newObjs = mc.ls(assemblies=True, l=True)
                    grpObjs = list(set(newObjs) - set(currentObjs))

                    if build : 
                        sd_utils.build(locs)

                    mc.parent(grpObjs, setGrp)

                else : 
                    warning.append('%s already exists' % rootLoc)


        if warning : 
            warningStr = ('\n').join(warning)
            mc.confirmDialog( title='Warning', message=warningStr, button=['OK'])
            message = 'Complete with some warning'

        mc.confirmDialog( title='Complete', message=message, button=['OK'])

    def merge(self, target, arg=None) : 
        logger.debug('Merging ...')
        mode = mc.radioCollection('%s_RC' % self.win, q=True, sl=True)
        sets = sd_utils.getShotSetAsset()
        logger.debug('sets %s' % sets)

        if mode == 'Sync' : 
            logger.debug('Sync')
            removeAsset=True
            buildAsset=True
            mergeMode = 'merge-add'

        if mode == 'Position' : 
            logger.debug('Position')
            removeAsset=False
            buildAsset=False
            mergeMode = 'merge-only'

        for eachSet in sets : 
            logger.debug('set %s' % eachSet)
            add, remove = sd_utils.mergeAsmLocator(eachSet, target=target, removeAsset=removeAsset, buildAsset=buildAsset, mergeMode=mergeMode)

        mc.confirmDialog( title='Complete', message='Complete', button=['OK'])

    def connectEmpty(self, arg=None) : 
        rootLocs = sd_utils.getAllShotSetRootLoc()

        for rootLoc in rootLocs : 
            if mc.objExists(rootLoc) : 
                sd_utils.connectEmptyLocator(rootLoc)

        mc.confirmDialog( title='Complete', message='Complete', button=['OK'])


    def cleanHidden(self, arg=None) : 
        rootLocs = sd_utils.getAllShotSetRootLoc()
        paths = []
        for rootLoc in rootLocs : 
            locs = sd_utils.getLocator(rootLoc, all=True)

            for loc in locs : 
                hiddenAttr = '%s.hidden' % loc 
                visAttr = '%s.visibility' % loc 

                if mc.getAttr(hiddenAttr) or not mc.getAttr(visAttr) : 
                    objs = mc.listRelatives(loc, ad=True)

                    for obj in objs : 
                        if mc.referenceQuery(obj, isNodeReferenced = True) : 
                            path = mc.referenceQuery(obj, f = True)

                            if not path in paths : 
                                paths.append(path)

        if paths : 
            for path in paths : 
                mc.file(path, rr = True)
                print 'remove %s' % path

        mc.confirmDialog( title='Complete', message='Complete', button=['OK'])

    def compareLoc(self, arg=None) : 
        mode = mc.radioCollection('%sCompare_RC' % self.win, q=True, sl=True)
        selObj = mc.ls(sl=True)[0]
        ref = mc.getAttr('%s.reference' % selObj)
        asset = entityInfo.info(ref)
        assetName = asset.name()

        if mode == 'Asset' : 
            abcLoc = sd_utils.getShotAssetAsmLocator(assetName)

        if mode == 'Shot' : 
            abcLoc = sd_utils.getShotAsmHero(assetName)

        rootLoc = sd_utils.getShotSetRootLoc(assetName)

        add, remove = sd_utils.compareLoc(rootLoc, abcLoc)
