import maya.cmds as mc

def showWholeMesh(*arg):
    setVrayAttr(1)

def showVraymesh(*arg):
    setVrayAttr(0)

def setVrayAttr(value):
    for sel in mc.ls(sl=True):
        shapeName = '%sShape' %sel

        if mc.objExists(shapeName) and 'proxy' in shapeName:
            lists = mc.listConnections('%s.inMesh' %(shapeName),source=True )
            vraymesh = lists[0]
            if mc.objExists(vraymesh):
                mc.setAttr('%s.showWholeMesh' %vraymesh, value)

def deleteUI():
    if mc.window('VrayMeshShowUI', exists=True):
        mc.deleteUI('VrayMeshShowUI')

def run():
    deleteUI()
    vraymeshWindow = mc.window( 'VrayMeshShowUI' , title="Vraymesh", w=200 )
    mc.columnLayout( adjustableColumn=True )
    mc.button( label='Show Whole Mesh', command= showWholeMesh , h = 40 )
    mc.button( label='Show Vray Mesh', command= showVraymesh , h = 40 )
    mc.setParent('..')
    
    mc.showWindow( vraymeshWindow )