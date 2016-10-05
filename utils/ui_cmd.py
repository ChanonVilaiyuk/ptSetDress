from tool.setDress.utils import asmAssetExport, sd_utils
reload(asmAssetExport)
reload(sd_utils)
from tool.utils import fileUtils, entityInfo, pipelineTools 
reload(entityInfo)
reload(pipelineTools)

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

import maya.cmds as mc 

def exportAssetAsmLocator() : 
	asset = entityInfo.info()
	asset.thisScene()
	asmAssetExport.run(asset.thisScene())


def exportShotAsmLocator() : 
    try : 
        # freeze viewport
        mc.refresh(suspend = True)
        sd_utils.exportShotAsmLocator()

    except Exception as e : 
        print e

    mc.refresh(suspend = False)
    mc.refresh(force = True)
