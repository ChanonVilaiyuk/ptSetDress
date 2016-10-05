import maya.cmds as mc
import sys

from functools import partial

sys.path.append('O:/studioTools/lib')
from module import buildSet
reload(buildSet)


# buildSet.checkEmptyLocator()
def build(arg=None) : 
	from tool.setDress.utils import setDress_utils
	reload(setDress_utils)

	setDress_utils.build()


if mc.window('buildSetUI',exists=True):
	mc.deleteUI( 'buildSetUI', window=True )

window = mc.window('buildSetUI' ,width=200,title='Build Set' )
mc.rowColumnLayout( numberOfColumns=2,columnWidth=[(1, 100), (2, 100)] )
# mc.button( label='Build',height=50, command='from module import buildSet\nreload(buildSet)\nbuildSet.connectEmptyLocator()\nmc.showHidden(all=True)\n'+
# 			'mc.confirmDialog( title="Report", message="Done!!", button=["Ok"], defaultButton="Ok" )'
# 		 )
mc.button( label='Build',height=50, command=partial(build))
mc.button( label='Publish',height=50, command='from module import buildSet\nreload(buildSet)\nbuildSet.publishRefBuild()\n'+
			'mc.confirmDialog( title="Report", message="Done!!", button=["Ok"], defaultButton="Ok" )'
		 )

mc.showWindow()
mc.window('buildSetUI', e = True, wh = [200, 60])
