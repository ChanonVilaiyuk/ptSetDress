import os,sys,time

import maya.cmds as mc
import maya.mel as mm
import pymel.core as pm

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

sys.path.append('O:/studioTools/maya/python')

def main():
    logger.info('Running asmShotExportCmd.py in batch mode ...')
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

    mc.file(scenePath, f=True, ignoreVersion=True, o=True) 
    
    logger.debug('setting all active representation ...')
    adRoots = sd_utils.findAssemblyRoot()
    for adRoot in adRoots : 
        asmUtils.setAllActiveRep(adRoot) 
    logger.debug('set complete')


    logger.info('Exporting abc locator')
    sd_utils.exportShotAsmLocator()
    logger.debug('Export abc locator finish')
    

main()