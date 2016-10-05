import os,sys,time

import maya.cmds as mc
import maya.mel as mm
import pymel.core as pm

sys.path.append('O:/studioTools/maya/python')

def createLocAbc():

    scenePath = sys.argv[1]
    assetPath = sys.argv[2]
    assetName = sys.argv[3]
    # openFile = sys.argv[4]

    from tool.utils import pipelineTools, fileUtils
    from tool.sceneAssembly import asm_utils as asmUtils

    reload(pipelineTools)
    reload(asmUtils)

    mc.file(f=True,new=True)

    adName = assetName + '_AD'
    adPath = assetPath + '/ref/' + adName + '.ma'
    locPath = adPath.replace('_AD.ma','_Loc.abc')

    arName = asmUtils.createARNode(adName)
    asmUtils.setARDefinitionPath(arName,adPath)
    asmUtils.setARNamespace(arName, adName)
    # asmUtils.setActiveRep(arName,'AR')
    asmUtils.setAllActiveRep(arName)

    locAD = os.path.split(scenePath)[0] + '/_buildLoc.ma'

    mc.file(rename=locAD)
    
    pipelineTools.doExportAssetAssemblyLocator(locPath)

    mc.file(f=True,save=True)


createLocAbc()

time.sleep(10)