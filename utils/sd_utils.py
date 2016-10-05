import maya.cmds as mc
import maya.mel as mm
import sys,shiboken, os
import traceback

import logging
# create logger with 'spam_application'
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('O:/studioTools/logs/asm/asm2.log' )
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
from tool.setDress.utils import asm
reload(asm)

tmpConstraint = []
grpSet = 'set'
removeName = ['_NS', '_AD', '_AR']

def exportAsmLocator(outputPath, bake=False) : 
    # root = createAsmLocator(bake)[0]
    asmLocator = asm.AsmLocator()
    root = asmLocator.create()[0]

    logger.info('--------- Exporting to Alembic ---------------')
    currentTime = mc.currentTime(q = True)
    start = currentTime
    end = currentTime + 1
    abcUtils.exportABC(['|'+root],outputPath, start, end)
    mc.delete(['|'+root])

    return outputPath

def exportShotAsmLocator(bake=False) : 
    """ export multiple sets from shot """
    currentObjs = mc.ls(assemblies=True)

    try : 
        # roots = createAsmLocator(bake)
        asmLocator = asm.AsmLocator()
        roots = asmLocator.create(bake)
        shot = entityInfo.info()
        exportFiles = []
        heroLocs = []

        if roots : 

            for i, root in enumerate(roots) : 
                refPath = mc.getAttr('%s.reference' % root)
                asset = entityInfo.info(refPath)
                assetName = asset.name()

                path = shot.animOutput('assemblies', True)
                hero = shot.animOutput('assemblies', True, False)

                path = path.replace('$', assetName)
                hero = hero.replace('$', assetName)

                logger.info('--------- Exporting to Alembic --------------')
                logger.info('%s/%s' % (i, len(roots)))
                currentTime = mc.currentTime(q = True)
                start = currentTime
                end = currentTime + 1
                versionLoc = abcUtils.exportABC(['|'+root], path, start, end)
                print 'Export %s' % versionLoc
                heroLoc = fileUtils.copy(path, hero)
                print 'Copy to hero %s' % heroLoc
                
                mc.delete(['|'+root])

                heroLocs.append(heroLoc)
                
            print 'Total %s set(s)' % len(roots)
            return heroLocs

    except Exception as e : 
        newObjs = mc.ls(assemblies=True)
        addObjs = list(set(newObjs) - set(currentObjs))
        logger.warning('Create locator failed. Remove left over objects %s' % addObjs)
        # mc.delete(addObjs)

        logger.error(e)
        traceback.print_exc()


def createAsmLocator(bake=False) : 
    # find root
    adRoots = findAssemblyRoot()
    currentTime = mc.currentTime(q = True)
    start = currentTime
    end = currentTime + 1
    roots = []

    if adRoots : 
        for adRoot in adRoots : 
            ad = adRoot
            asm_utils.setAllActiveRep(ad)
            cleanNamespace(ad)
            root = createAsmLocatorCmd(ad)
            childs = [a for a in mc.listRelatives(root, ad = True) if mc.objectType(a, isType='transform')]
            
            if bake : 
                start = mc.playbackOptions(q = True, min = True)
                end = mc.playbackOptions(q = True, max = True)
            
            bakeAnimation(childs, start, end)
            roots.append(root)
            removeConstraint(root)
        
        # mc.delete(tmpConstraint)

        return roots

def createAsmLocatorCmd(ad) : 
    childs = mc.listRelatives(ad, c = True, type = 'assemblyReference')
    loc = locatorCmd(ad)

    if childs : 
        for child in childs : 
            childLoc = createAsmLocatorCmd(child)
            snap(childLoc, child)

            if childLoc : 
                mc.parent(childLoc, loc)

        mc.setAttr('%s.parent' % loc, True)
        
    return loc

def locatorCmd(ad, parent=False) : 
    name = locatorName(ad)
    # name = '%s' % ad.replace(':', '_')
    logger.debug('ad name %s' % ad)
    logger.debug('locator name %s' % name)
    definitionAttr = '%s.definition' % ad
    ref = ''

    if mc.objExists(definitionAttr) : 
        ref = mc.getAttr('%s.definition' % ad)

    loc = mc.spaceLocator(n = name)[0]
    addLocAttr(loc, ref, parent)
    logger.debug('locator name %s' % loc)

    return loc


# def locatorName(ad) : 
#     for key in removeName : 
#         if key in ad : 
#             ad = ad.replace(key, '')

#     return '%s_loc' % ad.replace(':', '_')


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

def locatorName(ad) : 
    if ad[-1].isdigit() : 
        ad = ad.replace(ad[-1], '_%s' % (ad[-1]))

    for key in removeName : 
        if key in ad : 
            ad = ad.replace(key, '')

    name = '%s_loc' % ad.replace(':', '_')
    return name

    # nss = ad.split(':')
    # ns1 = nss[0]
    # ns1removeDigit = ns1

    # if ns1[-1].isdigit() : 
    #     ns1removeDigit = ns1.replace(ns1[-1], '')

    # return '%s_loc' % ad.replace(':', '_').replace(ns1, ns1removeDigit)

def addLocAttr(loc, ref, parent) : 
    attr = 'reference'
    parentAttr = 'parent'
    hideAttr = 'hidden'

    mc.addAttr(loc, ln = attr, dt = 'string')
    mc.setAttr('%s.%s' % (loc, attr), e = True, keyable = False)

    mc.addAttr(loc, ln = parentAttr, at = 'bool')
    mc.setAttr('%s.%s.' % (loc, parentAttr), e = True, keyable = False, channelBox = True)

    # mc.addAttr(loc, ln = hideAttr, at = 'bool')
    # mc.setAttr('%s.%s.' % (loc, hideAttr), e = True, keyable = False, channelBox = True)

    mc.setAttr('%s.%s' % (loc, attr), ref, type = 'string')
    mc.setAttr('%s.%s' % (loc, parentAttr), parent)

    return loc

def addHiddenAttr(locs) : 
    hideAttr = 'hidden'

    for loc in locs : 
        if not mc.objExists('%s.%s' % (loc, hideAttr)) : 
            mc.addAttr(loc, ln = hideAttr, at = 'bool')
            mc.setAttr('%s.%s.' % (loc, hideAttr), e = True, keyable = False, channelBox = True)
            vis = mc.getAttr('%s.visibility' % loc)
            mc.setAttr('%s.%s' % (loc, hideAttr), not vis)

def syncVis(locs, vis='', hidden=''): 
    hideAttr = 'hidden'
    
    for loc in locs : 
        if mc.objExists('%s.%s' % (loc, hideAttr)) : 
            if vis == 'hidden': 
                vis = mc.getAttr('%s.hidden' % loc)
                mc.setAttr('%s.%s' % (loc, 'visibility'), not vis)

            elif hidden == 'vis': 
                vis = mc.getAttr('%s.visibility' % loc)
                mc.setAttr('%s.%s' % (loc, hideAttr), not vis)

def restoreHidden(locs) : 
    hideAttr = 'hidden'

    for loc in locs : 
        if mc.objExists('%s.%s' % (loc, hideAttr)) : 
            hiddenValue = mc.getAttr('%s.%s' % (loc, hideAttr))

            if hiddenValue : 
                print loc
                mc.setAttr('%s.visibility' % loc, 0)

def setHidden(objs, state): 
    for obj in objs: 
        setHiddenAttr(obj, state)

def setHiddenAttr(ad, state): 
    attr = 'hidden'
    if not mc.objExists('%s.%s' % (ad, attr)) : 
        mc.addAttr(ad, ln=attr, at='bool')
        mc.setAttr('%s.%s' % (ad, attr), e=True, keyable=True)

    mc.setAttr('%s.%s' % (ad, attr), state)
    mc.setAttr('%s.visibility' % ad, not state)


def snap(src, target, pos=True, size=True, vis=True) : 
    delNodes = []

    if pos : 
        node = mc.parentConstraint(target, src)
        tmpConstraint.append(node[0])
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


def removeConstraint(root) : 
    targetNodes = ['parentConstraint', 'scaleConstraint']
    mc.select(root, hi=True)
    objs = mc.ls(sl=True)

    targets = [a for a in objs if mc.objectType(a) in targetNodes]
    mc.delete(targets)

def findAssemblyRoot() : 
    setGrp = 'set'
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



def importAssetAsmLocator(asset=None):
    
    if not asset: 
        asset = entityInfo.info()

    refPath = asset.getPath('ref')
    locPath = asset.getRefNaming('loc')
    refAbcFile = '%s/%s' % (refPath, locPath)

    if os.path.exists(refAbcFile): 
        root = readAbc(str(refAbcFile))
        setLoc = root[0]

        if not mc.objExists(setLoc) : 
            abcUtils.importABC('',refAbcFile.replace('\\','/'))

        else: 
            logger.warning('%s already exists. Skip import abc' % setLoc)
        
        mc.select(setLoc, hi=True)
        locs = mc.ls(sl=True, l=True)
        locs = [a for a in locs if mc.objExists('%s.reference' % a)]

        return locs

def importAsmLocator(abcFile) : 
    """ import aby abcFile """ 
    if os.path.exists(abcFile) : 
        root = readAbc(str(abcFile))
        setLoc = root[0]

        if not mc.objExists(setLoc) : 
            abcUtils.importABC('new', abcFile)

        else : 
            logger.warning('%s already exists. Skip import abc' % setLoc)

        mc.select(setLoc, hi=True)
        locs = mc.ls(sl=True, l=True)
        locs = [a for a in locs if mc.objExists('%s.reference' % a)]
        mc.select(cl=True)

        return locs

def importShotAsmLocator(mode='loc') : 
    data = pipelineTools.readShotAsmSet()
    setGrp = '|set'

    if data : 
        locs = [data['set'][a]['loc'] for a in data['set']]
        builds = [data['set'][a]['build'] for a in data['set']]
        roots = []
        
        if mode == 'loc' : 
            for loc in locs : 
                if os.path.exists(loc) : 
                    root = readAbc(loc)[0]
                    roots.append(root.replace('|', ''))

                    if not mc.objExists(root) : 
                        if not mc.objExists(setGrp) : 
                            setGrp = mc.group(em = True, n = setGrp)

                        abcUtils.importABC('',loc)
                        mc.parent(root, setGrp)

                    else : 
                        topGrp = mc.listRelatives(root, p = True, f = True)

                        if not topGrp == setGrp : 
                            mc.parent(root, setGrp)

                        logger.debug('%s already exists! %s Skip!' % (root, loc))

            return roots

        if mode == 'build' : 
            objs = []
            rootObjs = mc.ls(assemblies=True)
            for build in builds : 
                if os.path.exists(build) : 
                    result = mc.file(build,  i = True, type = 'mayaAscii', options = 'v=0', pr = True)
                    rootObjs2 = mc.ls(assemblies=True)

                    if not mc.objExists(setGrp) : 
                        setGrp = mc.group(em = True, n = setGrp)
                    
                    newObjs = list(set(rootObjs2) - set(rootObjs))
                    objs = objs + newObjs

                    mc.parent(newObjs, setGrp)

            return objs

def getShotAsmLocator() : 
    """ running in animClean and get anim export locator """ 
    assetNames = getShotSetAsset()
    info = dict()

    for assetName in assetNames : 
        heroFile = getShotAsmHero(assetName)
        versionFiles = getShotAsmVersion(assetName)

        info.update({assetName: {'hero': heroFile, 'version': versionFiles}})

    return info

def getAssetAsmLocator() : 
    data = pipelineTools.readShotAsmSet()
    setGrp = '|set'
    info = dict()

    if data : 
        locs = [data['set'][a]['loc'] for a in data['set']]
        for assetName in data['set'] : 
            loc = data['set'][assetName]['loc']
            info.update({assetName: loc})
        
        return info

def getAsmLocator(assetName, mode='asset') : 
    """ in shot """ 
    if mode == 'asset' : 
        data = pipelineTools.readShotAsmSet()

        if data : 
            if assetName in data['set'].keys() : 
                return data['set'][assetName]['loc']

    if mode == 'shot' : 
        return getShotAsmHero(assetName)


def build(locs=[], level='vProxy', lod='md', forceReplace=False, returnValue='normal') : 
    report = []
    report2 = []
    # locs = importAssetAsmLocator()
    count = len(locs)
    i = 0 
    
    if locs: 
        for loc in locs:
            # get ref path
            refAttr = '%s.reference' % loc

            if mc.objExists(refAttr): 
                # get level and lod
                refPath = mc.getAttr(refAttr)
                refPath = getRef(refPath, level, lod)
                asset = entityInfo.info(refPath)

                # check if it is a parent, then we don't connect
                parentAttr = '%s.parent' % loc
                isParent = False
                
                if mc.objExists(parentAttr) : 
                    isParent = mc.getAttr('%s.parent' % loc)

                # if path exists and not parent 
                if os.path.exists(refPath) and not isParent :
                    # check if it free to connect
                    if forceReplace: 
                        removeSet(removeGrp=loc, removeLoc=False)

                    if checkFreeLocator(loc) : 
                        try:
                            # set refPath back to locator
                            mc.setAttr(refAttr, refPath, type='string')

                            # bring in asset
                            namespaceRef = asset.name()
                            # commented this to remove shared shading network when referencing
                            # newFileRef = mc.file(refPath,r=True,type="mayaAscii",gl=True,shd="shadingNetworks",namespace=namespaceRef ,options="v=0")
                            newFileRef = mc.file(refPath,r=True,type="mayaAscii",gl=True,namespace=namespaceRef ,options="v=0")
                            namespaceRef = mc.referenceQuery(newFileRef,ns=True)
                            topGrp = mc.listRelatives('%s:*' % namespaceRef,parent=True,f=True)[0].split('|')[1]
                            
                            # move to snap locator
                            conNode = mc.parentConstraint(loc, topGrp)
                            mc.delete(conNode)
                            mc.parent(topGrp,loc)
                            # reset scale
                            mc.setAttr('%s.scale' % topGrp, 1, 1, 1)

                            i+=1

                        except Exception as e :
                            report.append(refPath)
                            report2.append((refPath, loc))
                            print e
                            pass

                    else : 
                        print 'Skip %s is already connected' % loc

                else:
                    if not isParent : 
                        print 'Skip %s is missing' % refPath
                        report.append(refPath)
                        report2.append((refPath, loc))

    if count == i : 
        print 'Total %s locators' % count
        print 'Complete!' 

    else : 
        print 'Skip %s locators' % (count - i)
        print 'Total %s locators' % count

    if returnValue == 'normal' : 
        return report

    if returnValue == 'loc' : 
        return report2

def compareLoc(rootLoc, abcLoc) : 
    if mc.objExists(rootLoc) and os.path.exists(abcLoc) : 
        mc.select(rootLoc, hi=True)
        rootLocs = mc.ls(sl=True, l=True)
        mc.select(cl=True)
        parentNode = mayaTools.findTopNode(rootLoc)
        rootLocs = [a.replace(parentNode, '') for a in rootLocs if not mc.referenceQuery(a, isNodeReferenced = True)]

        abcLocs = readAbc(str(abcLoc))

        add = list(set(abcLocs) - set(rootLocs))
        remove = list(set(rootLocs) - set(abcLocs))

        if add : 
            print add
            add = ['%s%s' % (parentNode, a) for a in add if not 'Shape' in a.split('|')[-1]]
            logger.info(add)
            logger.info('%s add objects' % len(add))

        if remove : 
            remove = ['%s%s' % (parentNode, a) for a in remove if mc.objectType('%s%s' % (parentNode, a), isType = 'transform')]
            logger.info(remove)
            logger.info('%s remove objects' % len(remove))

        if not add and not remove : 
            logger.info('sync')

        return (add, remove)


def compareAbc(abcLoc1, abcLoc2) : 
    abcLoc1 = readAbc(str(abcLoc1))
    abcLoc2 = readAbc(str(abcLoc2))

    add = list(set(abcLoc2) - set(abcLoc1))
    remove = list(set(abcLoc1) - set(abcLoc2))

    if add : 
        add = [a for a in add if not 'Shape' in a.split('|')[-1]]

    if remove : 
        remove = [a for a in remove if not 'Shape' in a.split('|')[-1]]

    return (add, remove)

def getLocator(rootLoc, all=False) : 
    rootLocs = mc.listRelatives(rootLoc, ad=True, type='transform')
    rootLocs = [a for a in rootLocs if not mc.referenceQuery(a, isNodeReferenced = True)]
    validLocs = []

    for each in rootLocs : 
        parentAttr = '%s.parent' % each 
        hiddenAttr = '%s.hidden' % each 
        hidden = False
        parent = False

        if mc.objExists(parentAttr) : 
            parent = mc.getAttr(parentAttr)

        if mc.objExists(hiddenAttr) : 
            hidden = mc.getAttr(hiddenAttr)

        if not all : 
            if not parent and not hidden : 
                validLocs.append(each)

        else : 
            validLocs.append(each)

    return rootLocs


def getSceneLocator(rootLoc) : 
    mc.select(rootLoc, hi=True)
    locs = mc.ls(sl=True, l=True)
    locs = [a for a in locs if mc.objExists('%s.reference' % a)]
    mc.select(cl=True)
    return locs


def mergeAsmLocator(assetName='', target='shot', abcFile=None, removeAsset=False, buildAsset=False, mergeMode='merge-add') : 
    abcHero = abcFile
    if not abcFile : 
        if target == 'shot' : 
            logger.debug('shot abcLoc')
            abcHero = getShotAsmHero(assetName)
            logger.debug(abcHero)

        if target == 'asset' : 
            logger.debug('asset abcLoc')
            abcHero = getShotAssetAsmLocator(assetName)
            logger.debug(abcHero)

    if os.path.exists(abcHero) : 
        logger.debug('reading merge root ...')
        rootLoc = readAbc(str(abcHero))[0].replace('|', '')
        logger.debug('root is %s' % rootLoc)

        if mc.objExists(rootLoc) : 
            logger.debug('comparing change %s to %s...' % (rootLoc, abcHero))
            add, remove = compareLoc(rootLoc, abcHero)
            logger.debug('additional assets %s' % add)
            logger.debug('remove assets %s' % remove)

            logger.debug('merging abc...')
            abcUtils.importABC(rootLoc, abcHero, mergeMode)
            logger.debug('merge complete')

            if removeAsset : 
                logger.info('removing excessive assets...')
                tmpGrp = 'tmpRemoveGrp'
                if remove : 
                    logger.debug('remove -> %s' % remove)
                    if not mc.objExists(tmpGrp) : 
                        tmpGrp = mc.group(em=True, n=tmpGrp)
                    
                    for each in remove : 
                        if mc.objExists(each): 
                            mc.parent(each, tmpGrp)
                            logger.debug('removed %s' % each)

                    removeSet(tmpGrp)
                    logger.debug('remove complete')

            if buildAsset : 
                logger.info('build ...')
                if add : 
                    logger.debug('add -> %s' % add)
                    build(add)
                    logger.debug('build success')

            return add, remove

        else : 
            logger.warning('root not exists in the scene %s' % rootLoc)

    else : 
        logger.warning('%s not exists' % abcHero)


def checkFreeLocator(loc) : 
    childs = mc.listRelatives(loc, c=True, f=True)
    childs = [a for a in childs if not mc.objectType(a, isType = 'locator')]

    if childs : 
        return False

    else : 
        return True

def getShotAsmHero(assetName) : 
    """ run at shot """
    shot = entityInfo.info()
    abcHero = shot.animOutput('assemblies', fileVersion=False).replace('$', assetName)

    return abcHero

def getShotSetAsset() : 
    data = pipelineTools.readShotAsmSet()

    if data : 
        sets = [a for a in data['set']]
        return sets

    else : 
        shot = entityInfo.info()
        desFileHero = shot.animOutput(data='description', fileVersion=False)
        logger.warning('No data file exported %s' % desFileHero)

def getAllShotSetRootLoc() : 
    assetNames = getShotSetAsset()
    rootLocs = ['%s_loc' % a for a in assetNames]
    return rootLocs

def getShotSetRootLoc(assetName) : 
    rootLocs = getAllShotSetRootLoc()

    if rootLocs : 
        for rootLoc in rootLocs : 
            if assetName in rootLoc : 
                return rootLoc

def getShotAsmVersion(assetName) : 
    abcHero = getShotAsmHero(assetName)
    abcDir = os.path.dirname(abcHero)

    abcVersions = fileUtils.listFile(abcDir)
    abcVersions = ['%s/%s' % (abcDir, a) for a in abcVersions]

    if abcHero in abcVersions : 
        abcVersion = abcVersions.remove(abcHero)

    return abcVersions


def getShotAssetAsmLocator(assetName) : 
    data = pipelineTools.readShotAsmSet()

    if assetName in data['set'].keys() : 
        abcHero = data['set'][assetName]['loc']

        return abcHero 

def getRef(refPath, level='vProxy', lod='md'): 
    asset = entityInfo.info(refPath)
    return '%s/%s' % (asset.getPath('ref'), asset.getRefNaming(level, lod=lod))

def connectEmptyLocator(rootLoc):
    locs = getLocator(rootLoc)
    build(locs)


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


def readAbc(abcFile): 
    iarch = Abc.IArchive(abcFile)
    root = iarch.getTop().children
    abcList = readAbcCmd(root)

    return abcList
    
def readAbcCmd(root):
    get = []
    for r in root:
        if not str(r) == '/set':      
            get.append(str(r).replace('/','|'))
        get += readAbcCmd(r.children)

    return get

def removeSet(removeGrp = '|set', removeLoc=True) : 
    objs = mc.listRelatives(removeGrp,ad=True, f = True)
    paths = []

    for obj in objs : 
        if mc.referenceQuery(obj, isNodeReferenced = True) : 
            path = mc.referenceQuery(obj, f = True)

            if not path in paths : 
                paths.append(path)

    if paths : 
        for path in paths : 
            mc.file(path, rr = True)
            print 'remove %s' % path

    if removeLoc: 
        mc.delete(removeGrp)

def findShotAsmSetAds() : 
    setGrp = '|set'
    ads = []
    validAds = []
    assetNames = []
    locs = []
    assets = []

    if mc.objExists(setGrp) : 
        nodes = mc.listRelatives(setGrp, c=True)

        if nodes : 
            ads = ads + nodes
    
    ads = ads + [a for a in mc.ls(assemblies=True) if mc.objectType(a, isType = 'assemblyReference')]

    for ad in ads : 
        path = mc.getAttr('%s.definition' % ad)
        asset = entityInfo.info(path)

        if asset.type() == 'set' : 
            validAds.append(ad)
            assetNames.append(asset.name())
            locs.append(asset.getRefNaming('loc'))
            assets.append(asset)

    return validAds


def publishWork(ar=True) : 
    """ publish dress work """
    logger.info('Publishing work ...')
    saveFile = mc.file(save=True, type='mayaAscii')
    logger.debug('file saved %s' % saveFile)
    asset = entityInfo.info()
    publishDir = asset.publishDir()
    publishFile = '%s/%s' % (publishDir, os.path.basename(saveFile))

    logger.debug('copying file from %s to %s' % (saveFile, publishFile))
    result = fileUtils.copy(saveFile, publishFile)
    logger.debug('publish complete')

    if ar : 
        logger.debug('prepare to publihs AR from %s' % result)
        publishAR(result)

def publishAR(source) : 
    """ publish AR from dress work """
    logger.info('Publishing AR file ...')

    if os.path.exists(source) : 
        asset = entityInfo.info()
        arFile = '%s/%s' % (asset.getPath('ref'), asset.getRefNaming('ar'))


        if os.path.exists(arFile) : 
            logger.debug('File exists. Backing up %s' % arFile)
            backupResult = pipelineTools.backupRef(arFile)
            logger.debug('Backup complete %s' % backupResult)

        logger.debug('Copying %s to %s' % (source, arFile))
        result = fileUtils.copy(source, arFile)
        logger.info('Publish complete')

        return result

    else : 
        logger.warning('%s not exists. Publihsing stop.' % source)

def publishAD() : 
    """ publish ad file from dress work """
    logger.info('Publishing AD file ...')
    asset = entityInfo.info()
    arFile = '%s/%s' % (asset.getPath('ref'), asset.getRefNaming('ar'))
    adFile = '%s/%s' % (asset.getPath('ref'), asset.getRefNaming('ad'))
    adName = '%s_ad' % (asset.name())

    createAD.SCENEPATH = asset.thisScene()
    createAD.ARPATH = arFile
    createAD.ADPATH = adFile
    createAD.ADNAME = adName
    createAD.ASSETNAME = asset.name()

    logger.debug('setting param ... ')
    logger.debug('param createAD.SCENEPATH : %s' % createAD.SCENEPATH)
    logger.debug('param createAD.ARPATH : %s' % createAD.ARPATH)
    logger.debug('param createAD.ADPATH : %s' % createAD.ADPATH)
    logger.debug('param createAD.ADNAME : %s' % createAD.ADNAME)
    logger.debug('param createAD.ASSETNAME : %s' % createAD.ASSETNAME)
    mtime = None
    
    if os.path.exists(adFile):
        mtime = os.path.getmtime(adFile)
        logger.debug('File exists. Backing up %s' % arFile)
        backupResult = pipelineTools.backupRef(adFile) 
        logger.debug('Backup complete %s' % backupResult)

    try:
        # pipelineTools.backupRef(self.adPath)
        logger.debug('Running batch create AD ...')
        logPath = createAD.run()
        logger.debug('Batch complete %s' % logPath)

    except Exception as e : 
        logger.error('Error %s' % e)

    if os.path.exists(adFile) : 
        if mtime : 
            newMtime = os.path.getmtime(adFile)
            logger.debug('mtime %s, newMTime %s' % (mtime, newMtime))

            if not newMtime == mtime : 
                logger.info('Publish AD complete %s' % adFile)
                return adFile

            else : 
                logger.error('Batch publish AD failed. File maybe locked. %s' % adFile)

        else : 
            logger.info('Publish AD complete %s' % adFile)
            return adFile


def findParent(obj, type='locator') : 
    objShape = mc.listRelatives(obj, s=True, f=True)

    if objShape : 
        if mc.objectType(objShape[0], isType=type) : 
            return obj 

    parent = mc.listRelatives(obj, p=True, f=True)
    
    if parent : 
        shape = mc.listRelatives(parent[0], s=True, f=True)
        
        if shape : 
            if mc.objectType(shape, isType=type) : 
                return parent[0]
                
            else : 
                return findParent(parent, type)
                
        else : 
            return findParent(parent, type)
            
    else : 
        return parent

def findReferenceChild(obj) : 
    currSelection = mc.ls(sl=True, l=True)
    mc.select(obj, hi=True)
    childs = mc.ls(sl=True, l=True)
    pathInfo = dict()

    if childs : 
        for child in childs : 
            if mc.referenceQuery(child, isNodeReferenced = True) : 
                path = mc.referenceQuery(child, f = True)

                if not path in pathInfo.keys() : 
                    rnNode = mc.referenceQuery(child, referenceNode=True)
                    pathInfo.update({path: rnNode})

    mc.select(currSelection)
    return pathInfo


def getHiddenAd(hiddenState=True) : 
    ads = mc.ls(type='assemblyReference', l=True)
    hiddenAds = []
    for ad in ads : 
        attr = '%s.%s' % (ad, 'hidden')
        if mc.objExists(attr) : 
            state = mc.getAttr(attr)
            
            if state == hiddenState : 
                hiddenAds.append(ad)

    return hiddenAds


def syncHiddenAd(syncOff=True, syncOn=False): 
    if syncOff : 
        hiddenAds = getHiddenAd(True)
        if hiddenAds : 
            for ad in hiddenAds : 
                mc.setAttr('%s.visibility' % ad, 0)

    if syncOn : 
        visAds = getHiddenAd(False)
        if visAds : 
            for ad in visAds : 
                mc.setAttr('%s.visibility' % ad, 1)

def checkHiddenSync(syncOff=True, syncOn=True) : 
    missSyncOff = []
    missSyncOn = []

    # asset that should be hidden but still visible
    if syncOff : 
        hiddenAds = getHiddenAd(True)
        if hiddenAds : 
            for ad in hiddenAds : 
                currentVis = mc.getAttr('%s.visibility' % ad)

                if currentVis : 
                    missSyncOff.append(ad)

    # asset that should be visible but still hidden 
    if syncOn : 
        visAds = getHiddenAd(False)
        if visAds : 
            for ad in visAds : 
                currentVis = mc.getAttr('%s.visibility' % ad)

                if currentVis == 0 : 
                    missSyncOn.append(ad)

    return missSyncOff, missSyncOn

def checkLostLinkADRig(confirm=True) : 
    switchGrp = 'adSwitch_grp'
    rigGrp = 'Rig_Grp'
    if mc.objExists(switchGrp) : 
        if mc.listRelatives(switchGrp, c=True): 
            assets = [a for a in mc.listRelatives(switchGrp, c=True) if rigGrp in a]
            missing = dict()

            for asset in assets : 
                geoGrp = '%s:Geo_Grp.%s' % (asset.split(':')[0], 'adname')
                if mc.objExists(geoGrp) : 
                    ad = mc.getAttr(geoGrp)

                    if not mc.objExists(ad) : 
                        if confirm: 
                            if not checkConfirm(geoGrp.split('.')[0]): 
                                missing.update({ad: geoGrp})

                        else: 
                            missing.update({ad: geoGrp})                            

            return missing

def checkConfirm(geoGrp): 
    shot = entityInfo.info()
    step = shot.department()
    attr = '%s.%s_confirm' % (geoGrp, step)

    if not step in ['layout', 'anim']: 
        return True

    if not mc.objExists(attr): 
        mc.addAttr(geoGrp, ln='%s_confirm' % step, at='bool')
        mc.setAttr(attr, e=True, keyable=True)

    stepConfirm = mc.getAttr(attr)

    if stepConfirm: 
        return True 
