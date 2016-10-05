import sys
from functools import partial
import maya.cmds as mc

from tool.setDress.utils import sd_utils
reload(sd_utils)

from tool.utils import entityInfo 
reload(entityInfo)

# buildSet.checkEmptyLocator()
def build(arg=None) : 
	asset = entityInfo.info()
	locs = sd_utils.importAssetAsmLocator(asset)
	setGrp = mc.group(em=True, n='|set')
	objs = sd_utils.build(locs)
	rootLoc = locs[0]
	mc.parent(rootLoc, setGrp)
	strObjs = ('\n').join(objs)

	if objs : 
		mc.confirmDialog( title='Warning', message='%s missing assets\n----------------\n%s' % (len(objs), strObjs), button=['OK'])

	else : 
		mc.confirmDialog(title='Success', message='Build complete', button=['OK'])


def removeSet(arg=None) : 
	if mc.objExists('|set') : 
		sd_utils.removeSet('|set')


def run() : 
	if mc.window('buildSetUI',exists=True):
		mc.deleteUI('buildSetUI', window=True)

	window = mc.window('buildSetUI' ,width=200,title='Build Set')
	mc.columnLayout(adj=1, rs=4)

	mc.button(label='Build',height=40, command=partial(build))
	mc.button(label='Remove Set',height=40, command=partial(removeSet))

	mc.showWindow()
	mc.window('buildSetUI', e = True, wh = [200, 100])
