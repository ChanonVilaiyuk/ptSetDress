import maya.cmds as mc
import maya.mel as mm
import sys,shiboken, os

import logging
# create logger with 'spam_application'
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('O:/studioTools/logs/asm/setDress_utils.log')
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)


from alembic import Abc

sys.path.append('O:/studioTools/maya/python')
from tool.utils import abcUtils,pipelineTools
reload(abcUtils)
reload(pipelineTools)

from tool.publish.setDress import selectionSet as ss
reload(ss)
from tool.utils import entityInfo

tmpConstraint = []

def exportAsmLocator(outputPath, bake=False) : 
    grpSet = 'set'
    root = createAsmLocator(bake, rootGrp=False)

    if not mc.objExists(grpSet) : 
        grpSet = mc.group(em = True, n = grpSet)
        mc.parent(root, grpSet)

    abcUtils.exportABC(['|'+grpSet],outputPath)
    mc.delete(['|'+grpSet])

    return outputPath

def exportAsmLocatorLegacy(outputPath, bake=False) : 
    grpSet = 'set'
    root = createAsmLocator(bake, rootGrp=True)

    if not mc.objExists(grpSet) : 
        grpSet = mc.group(em = True, n = grpSet)
        mc.parent(root, grpSet)

    abcUtils.exportABC(['|'+grpSet],outputPath)
    mc.delete(['|'+grpSet])

    return outputPath

def createAsmLocator(bake=False, rootGrp=True) : 
    adRoot = findAssemblyRoot()
    currentTime = mc.currentTime(q = True)
    start = currentTime
    end = currentTime + 1

    if adRoot : 
        ad = adRoot[0]
        root = createAsmLocatorCmd(ad, rootGrp=rootGrp)
        childs = [a for a in mc.listRelatives(root, ad = True) if mc.objectType(a, isType='transform')]
        
        if bake : 
            start = mc.playbackOptions(q = True, min = True)
            end = mc.playbackOptions(q = True, max = True)
            bakeAnimation(childs, start, end)

        mc.delete(tmpConstraint)
        return root

def createAsmLocatorCmd(ad, rootGrp=False) : 
    childs = mc.listRelatives(ad, c = True, type = 'assemblyReference')
    if rootGrp : 
        loc = rootGrpCmd(ad)
    else : 
        loc = locatorCmd(ad)

    if childs : 
        for child in childs : 
            childLoc = createAsmLocatorCmd(child)
            snap(childLoc, child)

            if childLoc : 
                mc.parent(childLoc, loc)

        mc.setAttr('%s.parent' % loc, True)
        
    return loc

def rootGrpCmd(ad) : 
    definitionAttr = '%s.definition' % ad
    ref = ''

    if mc.objExists(definitionAttr) : 
        ref = mc.getAttr('%s.definition' % ad)
        ref = ref.replace('AD', 'vProxyMd')
        
    grp = mc.group(em = True, n = 'set')
    addLocAttr(grp, ref, parent=True)

    return grp

def locatorCmd(ad, parent=False) : 
    name = '%s_loc' % ad.replace(':', '_')
    # name = '%s' % ad.replace(':', '_')
    logger.debug('ad name %s' % ad)
    logger.debug('locator name %s' % name)
    definitionAttr = '%s.definition' % ad
    ref = ''

    if mc.objExists(definitionAttr) : 
        ref = mc.getAttr('%s.definition' % ad)
        ref = ref.replace('AD', 'vProxyMd')

    loc = mc.spaceLocator(n = name)[0]
    addLocAttr(loc, ref, parent)
    logger.debug('locator name %s' % loc)

    return loc


def addLocAttr(loc, ref, parent) : 
    attr = 'reference'
    parentAttr = 'parent'
    hideAttr = 'hidden'

    mc.addAttr(loc, ln = attr, dt = 'string')
    mc.setAttr('%s.%s' % (loc, attr), e = True, keyable = False)

    mc.addAttr(loc, ln = parentAttr, at = 'bool')
    mc.setAttr('%s.%s.' % (loc, parentAttr), e = True, keyable = False, channelBox = True)

    mc.addAttr(loc, ln = hideAttr, at = 'bool')
    mc.setAttr('%s.%s.' % (loc, hideAttr), e = True, keyable = False, channelBox = True)

    mc.setAttr('%s.%s' % (loc, attr), ref, type = 'string')
    mc.setAttr('%s.%s' % (loc, parentAttr), parent)

    return loc


def snap(src, target, pos=True, size=True, vis=True) : 
    if pos : 
        node = mc.parentConstraint(target, src)
        tmpConstraint.append(node[0])
    if size : 
        mc.delete(mc.scaleConstraint(target, src))
    if vis : 
        vis = mc.getAttr('%s.visibility' % target)
        mc.setAttr('%s.visibility' % src, vis)


def bakeAnimation(objs, start, end) : 
    mc.bakeResults(objs,simulation=True,t=(start,end),sampleBy=1,disableImplicitControl=True,
                    preserveOutsideKeys=True ,sparseAnimCurveBake=False,removeBakedAttributeFromLayer=False,
                    removeBakedAnimFromLayer=False, bakeOnOverrideLayer=False, minimizeRotation=True,
                    controlPoints=False ,shape=True )



def findAssemblyRoot() : 
    setGrp = 'set'
    topNodes = mc.ls(assemblies = True)
    topNodes = [a for a in topNodes if mc.objectType(a, isType = 'assemblyReference')]

    if not topNodes : 
        if mc.objExists(setGrp) : 
            setMembers = mc.listRelatives(setGrp, c = True)
            setMembers = [a for a in setMembers if mc.objectType(a, isType = 'assemblyReference')]

            if setMembers : 
                return setMembers

    else : 
        return topNodes


def importAssetAsmLocator(locs=[]):
    setGrp = '|set'
    if not locs:
        dirFile = mc.file(q=True,loc=True)
        print 'Dir File:',dirFile
        assetName = dirFile.split('/')[6]
        # print assetName
        dirRef= os.path.join(('\\').join(dirFile.split('/')[:7]),'ref')
        # print dirRef
        refAbcFile = os.path.join(dirRef,'%s_Loc.abc'%assetName)
        refAbcFile = os.path.normpath(refAbcFile)
        print 'Ref Abc:',refAbcFile

        if os.path.exists(refAbcFile):
            if not mc.objExists(setGrp) : 
                abcUtils.importABC('',refAbcFile.replace('\\','/'))
            
            locs = mc.listRelatives(mc.ls(type='locator'),parent=True,f=True)
            locs = [a for a in locs if mc.objExists('%s.reference' % a)]

    else:
        locs = mc.ls(sl=True)

    return locs

def build(locs=[], level='') : 
    report = []
    locs = importAssetAsmLocator()
    print 'BUILD LOC:',locs
    count = len(locs)
    i = 0 
    
    for loc in locs:
        # get ref path
        refpath = mc.getAttr(loc+'.reference')
        refpath = pipelineTools.overLoadLevelVProxy(refpath)
        parentAttr = '%s.parent' % loc
        isParent = False
        
        if mc.objExists(parentAttr) : 
            isParent = mc.getAttr('%s.parent' % loc)

        mc.setAttr(loc+'.reference',refpath,type='string')
        # print refpath
        if os.path.exists(refpath) and not isParent :
            if checkFreeLocator(loc) : 
                try:
                    namespaceRef = ('_').join(os.path.basename(refpath).split('_')[:-1])
                    newFileRef = mc.file(refpath,r=True,type="mayaAscii",gl=True,shd="shadingNetworks",namespace=namespaceRef ,options="v=0")
                    namespaceRef = mc.referenceQuery(newFileRef,ns=True)
                    topGrp = mc.listRelatives('%s:*' % namespaceRef,parent=True,f=True)[0].split('|')[1]
                    conNode = mc.parentConstraint( loc, topGrp,mo=0 )
                    mc.delete(conNode)
                    mc.parent(topGrp,loc)
                    # reset scale
                    mc.setAttr('%s.scale' % topGrp, 1, 1, 1)
                    i+=1

                except:
                    report.append(refpath)
                    pass

            else : 
                print 'Skip %s is already connected' % loc

        else:
            report.append(refpath)

    if count == i : 
        print 'Total %s locators' % count
        print 'Complete!' 

    else : 
        print 'Skip %s locators' % (count - i)
        print 'Total %s locators' % count

    return report


def checkFreeLocator(loc) : 
    childs = mc.listRelatives(loc, c = True)
    childs = [a for a in childs if not mc.objectType(a, isType = 'locator')]

    if childs : 
        return False

    else : 
        return True



def connectEmptyLocator():
    print 'connect'
    emptyLoc = checkEmptyLocator()

    missigAsset = build(emptyLoc)
    print '---------MISSING ASSET-----------\n'  
    print ('\n').join(missigAsset)
    print 'Complete..'
    if emptyLoc:
        mc.select(emptyLoc)
    if missigAsset:
        mc.confirmDialog( title="Warning", message="Have Missing %s Asset!!!\nPlease check in Script Editor." % len(missigAsset), button=["Ok"], defaultButton="Ok")


def checkEmptyLocator(updateExist=0):
    print 'check'
    locEmpty = []
    if mc.ls(type='locator'):
        loc = mc.listRelatives(mc.ls(type='locator'),parent=True,f=True)
        for l in loc:
            child = mc.listRelatives(l,c=True,type='transform',f=True)
            refpath = mc.getAttr(l+'.reference')
            if child:
                for c in child:
                    if not mc.referenceQuery(c,inr=True):
                        if not mc.nodeType(mc.listRelatives(c,s=True,f=True)[0]) == 'locator':
                            print l
                            locEmpty.append(l)

            else:
                locEmpty.append(l)

    mc.select(locEmpty)

    return locEmpty

# def updateAssetChange(loc,assetpath):
#     print 'updateAssetChange:',assetpath
#     child = mc.listRelatives(loc,c=True,type='transform',f=True)
#     if child:
#         refNode = ''
#         if mc.referenceQuery(child[0],inr=True):
#             refNode = mc.referenceQuery(child[0],rfn=True)
#             mc.file(assetpath.replace('\\','/'),loadReference=refNode,options = "v=0")



def publishRefBuild():
    ss.exportCmd()


    dirFile = mc.file(q=True,loc=True)
    # print dirFile
    assetName = dirFile.split('/')[6]
    # print assetName
    dirRef= os.path.join(('\\').join(dirFile.split('/')[:7]),'ref')
    # print dirRef
    refFile = os.path.join(dirRef,'%s_Build.ma'%assetName)
    refFile = os.path.normpath(refFile)

    mc.file(refFile,force=True,options="v=0",typ="mayaAscii",pr=True,ea=1)
    print 'Result:%s'%refFile
    return refFile
