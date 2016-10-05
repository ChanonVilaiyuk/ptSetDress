import maya.cmds as mc
import os
from tool.utils import fileUtils
reload(fileUtils)


def exportData(*arg):

    path      = mc.file(q=True,sn=True)
    sceneName = path.split('/')[-1].split('_v')[0]
    cachePath = path.split('scenes/')[0] + 'cache/'

    transform = dict()
    sets      = dict()

    setNames = mc.ls(sl=True)

    for sel in mc.listRelatives(setNames[0],c=True):
        transform[sel] = { 's' : list(mc.getAttr('%s.s' %(sel))[0]) }

    scalePath = cachePath + '_assemblyScale.yml'

    fileUtils.ymlDumper(scalePath,transform)
    print 'Save as ' + scalePath

def importData(*arg):

    path      = mc.file(q=True,sn=True)
    scalePath = path.split('animClean/')[0] + 'anim/cache/_assemblyScale.yml'

    if os.path.exists(scalePath):

        data = fileUtils.ymlLoader(scalePath)
        
        for i,v in data.iteritems():
            if mc.objExists('%s' %(i.split(':')[-1]) ):
                sels = mc.ls('%s' %(i.split(':')[-1]))
                #print sels
                for child in mc.listRelatives(sels[0], c=True):
                    if 'Rig_Grp' in child:
                        mc.setAttr('%s.s' %(child), v['s'][0],  v['s'][1], v['s'][2])

    else:
        print 'File is not found. ' + scalePath