import sys, os 
import subprocess
import logging
from datetime import datetime
import maya.cmds as mc
from tool.utils import entityInfo, pipelineTools
reload(entityInfo)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
version = mc.about(version=True) 

if '2016' in version:
    MAYA_PYTHON = 'C:/Program Files/Autodesk/Maya2016/bin/mayapy.exe'

MAYACMD = 'O:/studioTools/maya/python/tool/setDress/utils/asmShotExportCmd.py'
LOG = 'O:/log.txt'

def run(SCENEPATH) : 
    # print MAYA_PYTHON, MAYACMD, ARPATH, ADPATH, ADNAME, ASSETNAME
    logger.info('Start exporting asmAssetLocator ...')
    asset = entityInfo.info(SCENEPATH)
    locPath = '%s/%s' % (asset.getPath('ref'), asset.getRefNaming('loc'))

    mtime = None

    if os.path.exists(locPath) : 
        logger.debug('File exists. Backing up ...')
        backupResult = pipelineTools.backupRef(locPath)
        logger.debug('Backup complete %s' % locPath)

        mtime = os.path.getmtime(locPath)
        logger.debug('mtime %s' % mtime)

    logFile = 'asmExportLoc_%s.log' % str(datetime.now()).replace(' ', '_').replace(':', '-').split('.')[0]
    logPath = '%s/%s/%s' % (asset.getPath('log'), 'asmLocator', logFile)
    # logPath = LOG

    logger.info('running batch ...')
    chk = subprocess.call([MAYA_PYTHON, MAYACMD, SCENEPATH])
    logger.debug('batch complete')
    chk = ''

    # return logPath
