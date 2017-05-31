import maya.cmds as mc
import maya.mel as mm
import sys,shiboken, os

import logging
# create logger with 'spam_application'
logger = logging.getLogger(__name__)

# create file handler which logs even debug messages
# fh = logging.FileHandler('O:/studioTools/logs/asm/asm3.log')
# fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
# ch = logging.StreamHandler()
# ch.setLevel(logging.ERROR)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# fh.setFormatter(formatter)
# ch.setFormatter(formatter)
# add the handlers to the logger
# logger.addHandler(fh)
# logger.addHandler(ch)


from alembic import Abc

sys.path.append('O:/studioTools/maya/python')
from tool.utils import abcUtils,pipelineTools, fileUtils, mayaTools
reload(abcUtils)
reload(pipelineTools)
reload(mayaTools)

from tool.sceneAssembly import asm_utils 
reload(asm_utils)

from tool.publish.setDress import selectionSet as ss
reload(ss)
from tool.utils import entityInfo
reload(entityInfo)
from tool.utils.batch import createAD
reload(createAD)

class AsmLocator(object):
    """docstring for AsmLocator"""
    def __init__(self):
        super(AsmLocator, self).__init__()
        self.tmpConstraint = []
        self.grpSet = 'set'
        self.removeName = ['_NS', '_AD', '_AR']
        self.assetRoot = str()
        self.assetRootReplace = str()

    def create(self, bake=False) : 
        return self.createAsmLocator(bake)

    def createAsmLocator(self, bake=False) : 
        # find root
        adRoots = findAssemblyRoot()
        currentTime = mc.currentTime(q = True)
        start = currentTime
        end = currentTime + 1
        roots = []

        if adRoots : 
            for adRoot in adRoots : 
                ad = adRoot
                self.assetRoot = ad
                asm_utils.setAllActiveRep(ad)
                # cleanNamespace(ad)
                root = self.createAsmLocatorCmd(ad)
                childs = [a for a in mc.listRelatives(root, ad=True, f=True) if mc.objectType(a, isType='transform')]
                
                if bake : 
                    start = mc.playbackOptions(q = True, min = True)
                    end = mc.playbackOptions(q = True, max = True)
                
                logger.info('------ bake animation --------')
                logger.info('%s-%s' % (start, end))
                bakeAnimation(childs, start, end)
                roots.append(root)
                removeConstraint(root)
            
            # mc.delete(tmpConstraint)

            return roots

    def createAsmLocatorCmd(self, ad) : 
        childs = mc.listRelatives(ad, c = True, type = 'assemblyReference')
        loc = self.locatorCmd(ad)

        if childs : 
            for child in childs : 
                childLoc = self.createAsmLocatorCmd(child)
                snap(childLoc, child)

                if childLoc : 
                    mc.parent(childLoc, loc)

            mc.setAttr('%s.parent' % loc, True)
            
        return loc

    def locatorCmd(self, ad, parent=False) : 
        name = self.locatorName(ad)
        # name = '%s' % ad.replace(':', '_')
        logger.debug('ad name %s' % ad)
        logger.debug('locator name %s' % name)
        definitionAttr = '%s.definition' % ad
        ref = ''

        if mc.objExists(definitionAttr) : 
            ref = mc.getAttr('%s.definition' % ad)

        loc = mc.spaceLocator(n = name)[0]
        loc = '|%s' % loc
        self.addLocAttr(loc, ref, parent)
        logger.debug('locator name %s' % loc)

        return loc

    def cleanNamespace(ad) : 
        definition = mc.getAttr('%s.definition' % ad)
        namespace = mc.getAttr('%s.repNamespace' % ad)
        asset = entityInfo.info(definition)
        assetName = asset.name()
        currName = namespace

        for key in removeName : 
            if key in currName : 
                currName = currName.replace(key, '')

        if not currName == assetName : 
            arName = ad
            adNamespace = ad.replace(currName, assetName)
            asm_utils.setARNamespace(arName, adNamespace)
            logger.info('Clean namespace %s -> %s' % (namespace, adNamespace))

    def locatorName(self, ad) : 
        if self.assetRoot == ad : 
            assetDefinition = mc.getAttr('%s.definition' % ad)
            asset = entityInfo.info(assetDefinition)
            assetName = asset.name()

            return '%s_loc' % assetName
                
        adName = ad
        elements = ad.split(':')

        if len(elements) >= 2 : 
            adName = (':').join(elements[1:])
        
        if adName[-1].isdigit() : 
            adName = adName.replace(adName[-1], '_%s' % (adName[-1]))
            
        for key in self.removeName : 
            if key in adName : 
                adName = adName.replace(key, '')

        name = '%s_loc' % adName.replace(':', '_')

        return name

        # nss = ad.split(':')
        # ns1 = nss[0]
        # ns1removeDigit = ns1

        # if ns1[-1].isdigit() : 
        #     ns1removeDigit = ns1.replace(ns1[-1], '')

        # return '%s_loc' % ad.replace(':', '_').replace(ns1, ns1removeDigit)

    def addLocAttr(self, loc, ref, parent) : 
        attr = 'reference'
        parentAttr = 'parent'
        hideAttr = 'hidden'

        mc.addAttr(loc, ln = attr, dt = 'string')
        mc.setAttr('%s.%s' % (loc, attr), e = True, keyable = False)

        mc.addAttr(loc, ln = parentAttr, at = 'bool')
        mc.setAttr('%s.%s.' % (loc, parentAttr), e = True, keyable = False, channelBox = True)

        mc.setAttr('%s.%s' % (loc, attr), ref, type = 'string')
        mc.setAttr('%s.%s' % (loc, parentAttr), parent)

        return loc


def removeConstraint(root) : 
    targetNodes = ['parentConstraint', 'scaleConstraint']
    mc.select(root, hi=True)
    objs = mc.ls(sl=True)

    targets = [a for a in objs if mc.objectType(a) in targetNodes]
    mc.delete(targets)

def snap(src, target, pos=True, size=True, vis=True) : 
        delNodes = []

        if pos : 
            node = mc.parentConstraint(target, src)
            # tmpConstraint.append(node[0])
        if size : 
            mc.delete(mc.scaleConstraint(target, src))
        if vis : 
            vis = mc.getAttr('%s.visibility' % target)
            mc.setAttr('%s.visibility' % src, vis)

        return delNodes

def bakeAnimation(objs, start, end) : 
        mc.bakeResults(objs,simulation=True,t=(start,end),sampleBy=1,disableImplicitControl=True,
                        preserveOutsideKeys=True ,sparseAnimCurveBake=False,removeBakedAttributeFromLayer=False,
                        removeBakedAnimFromLayer=False, bakeOnOverrideLayer=False, minimizeRotation=True,
                        controlPoints=False ,shape=True )


def findAssemblyRoot() : 
    setGrp = '|set'
    topNodes = mc.ls(assemblies = True)
    topNodes = [a for a in topNodes if mc.objectType(a, isType = 'assemblyReference')]
    adNodes = topNodes
    setNodes = []

    if mc.objExists(setGrp) : 
        setMembers = mc.listRelatives(setGrp, c = True)
        setMembers = [a for a in setMembers if mc.objectType(a, isType = 'assemblyReference')]

        if setMembers : 
            adNodes = adNodes + setMembers

    for eachNode in adNodes : 
        definition = mc.getAttr('%s.definition' % eachNode)
        asset = entityInfo.info(definition)

        if asset.type() in ['set', 'subSet', 'setDress'] : 
            setNodes.append(eachNode)

    return setNodes