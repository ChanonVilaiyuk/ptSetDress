import os,sys,time

import maya.cmds as mc
import maya.mel as mm
import pymel.core as pm

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

sys.path.append('O:/studioTools/maya/python')

def main():
    logger.info('Running asmAssetExportCmd.py in batch mode ...')
    scenePath = sys.argv[1]
    logger.debug('Input argv[1], scenePath %s' % scenePath)
    # scenePath = 'P:/Lego_Pipeline/asset/3D/set/town/lpl_lab/setDress/dress/scenes/lpl_lab_dress_v025_TA.ma'

    logger.debug('Loading pipeline module ...')
    from tool.utils import entityInfo, fileUtils
    from tool.sceneAssembly import asm_utils as asmUtils
    from tool.setDress.utils import sd_utils
    reload(asmUtils)
    reload(sd_utils)
    reload(entityInfo)
    logger.debug('Loaded')

    asset = entityInfo.info(scenePath)

    mc.file(f=True,new=True)
    logger.debug('Start new scene')

    adName = '%s_AR' % asset.getRefNaming('ad', showExt = False)
    adNamespace = asset.getRefNaming('ad', showExt = False)
    adPath = '%s/%s' % (asset.getPath('ref'), asset.getRefNaming('ad'))
    locPath = '%s/%s' % (asset.getPath('ref'), asset.getRefNaming('loc'))
    publishDir = '%s/%s' % (asset.getPath('setDress'), 'publish')
    fileName = asset.fileName()
    publishMaya = '%s/%s.ma' % (publishDir, fileName)
    publishLoc = '%s/%s.abc' % (publishDir, fileName)

    if not os.path.exists(publishDir) : 
        os.makedirs(publishDir)
        logger.debug('%s created' % publishDir)

    logger.debug('adName : %s' % adName)
    logger.debug('adPath : %s' % adPath)
    logger.debug('adNamespace : %s' % adNamespace)

    logger.debug('creating ARNode %s ...' % adName)
    arName = asmUtils.createARNode(adName)

    logger.debug('setting ad path %s %s ...' % (arName, adPath))
    asmUtils.setARDefinitionPath(arName, adPath)

    logger.debug('setting namespace %s ...' % adNamespace)
    asmUtils.setARNamespace(arName, adNamespace)

    logger.debug('setting all active representation ...')
    asmUtils.setAllActiveRep(arName)
    logger.debug('set complete')

    mc.file(rename=publishMaya)
    logger.debug('rename scene to %s' % publishMaya)

    result = mc.file(f=True,save=True, type = 'mayaAscii')
    logger.debug('Virtual AR scene saved %s' % result)
    
    logger.info('Exporting abc locator %s ...' % locPath)
    sd_utils.exportAsmLocator(locPath, bake=False)
    logger.debug('Export abc locator finish')

    logger.info('Copying abc hero ...')
    fileUtils.copy(locPath, publishLoc)
    logger.debug('Copy success %s' % publishLoc)

    

main()