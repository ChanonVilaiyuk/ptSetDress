
import maya.cmds as mc
from functools import partial
import maya.mel as mm
from tool.utils import mayaTools

def run() : 
    if mc.window('AD_Utils_win', exists = True) : 
        mc.deleteUI('AD_Utils_win')

    myApp = mainClass()
    myApp.mayaUI()

class mainClass():
    """docstring for ClassName"""
    def __init__(self):
        self.win = 'AD_Utils'
        self.ui = '%s_win' % self.win

    def mayaUI(self):
        AD_Win = mc.window(self.ui, title='AD Utils',w=300,h=400)
        mc.columnLayout(adj=1, rs=4)
        mc.frameLayout(l='Move Gpu')
        mc.columnLayout(adj=1, rs=4)
        mc.button(l = 'Add Locator', bgc=(0.5,0.2,0.5),h=30, c=partial(self.addButton))
        mc.button(l = 'Select Locator', bgc=(0.5,0.3,0.5),h=30, c=partial(self.selectionLoc))
        mc.button(l = 'Remove Locator', bgc=(0.5,0.4,0.5),h=30, c=partial(self.removeButton))
        mc.setParent('..')
        mc.setParent('..')
        
        mc.frameLayout(l='Transfer Key')
        mc.columnLayout(adj=1, rs=4)
        mc.button(l = 'Select Gpu With Key', bgc=(0.1,0.5,0.5),h=30, c=partial(self.selectGpuKey))
        mc.button(l = 'Auto Transfer', bgc=(0.2,0.5,0.5),h=30, c=partial(self.autoTranfer))
        mc.separator (h= 5, st= "none")

        mc.text(l='Manual transfer', al='left')
        mc.button(l = 'Transfer Key', bgc=(0.3,0.5,0.5),h=30, c=partial(self.tranferKey))
        mc.button(l = 'Connect Locator', bgc=(0.4,0.5,0.5),h=30, c=partial(self.connectLoc))
        mc.setParent('..')
        mc.setParent('..')
        mc.showWindow(AD_Win)

    def selectGpuKey(self,arg):
        self.animArs = []
        if mc.ls(sl=True): 
            for self.ar in mc.listRelatives(mc.ls(sl=True)[0], c=True): 
                if mc.listConnections(self.ar, type='animCurve'): 
                    self.animArs.append(self.ar)
        else:
            mm.eval('warning "Select Asset_AD_AR";')   
        mc.select(self.animArs)

    def addButton (self,arg):
        self.listSel = mc.ls(selection = True)

        if not mc.objExists('ARLoc_Grp'):
            mc.group( em=True, name='ARLoc_Grp')
            
        for self.sel in self.listSel:
            animNodes = mc.listConnections(self.sel, t="animCurve")
            print animNodes
            #self.locName = self.sel+"_loc"
            self.locName = self.sel.replace(':','_')+"_loc" #060117 edit because namespace AD_AR are change
            
            if not animNodes:
                if self.locName:
                    self.loc = mc.spaceLocator(p=(0,0,0),name = self.locName )
                    self.parentLoc = mc.parentConstraint(self.sel,self.loc,maintainOffset = False)
                    self.scaleLoc = mc.scaleConstraint(self.sel,self.loc,maintainOffset = False)
                    mc.delete(self.parentLoc)
                    mc.delete(self.scaleLoc)
                    self.parentCon = mc.parentConstraint(self.loc,self.sel,maintainOffset = True)
                    self.scaleCon = mc.scaleConstraint(self.loc,self.sel,maintainOffset = True)
                    mc.parent(self.loc,'ARLoc_Grp')
                else:
                    mm.eval('warning "Locator is existed already";')

            else:
                mm.eval('warning "This Object have animation. Please Use Tranfer Key";')


    def selectionLoc (self,arg):        
        self.listSel = mc.ls(selection = True) 

        for self.sel in self.listSel:   
            self.listCon = mc.parentConstraint(self.sel,query=True, targetList=True )
            if self.listCon:
                mc.select(self.listCon)
            else: 
                mm.eval('warning "This Object not have locator. Please Add Locator or Transfer Key";')

    def removeButton (self,arg):
        self.listSel = mc.ls(selection = True) 
        for self.sel in self.listSel:
            print self.sel
            self.locType = mc.listRelatives(self.sel)
            if mc.objectType(self.locType[0],isType ='locator'):


                self.listLoc = self.sel
                print 1

            else:

                print 2
                self.listLoc = mc.parentConstraint(self.sel,query=True, targetList=True )
            
            self.constraints = []
            for self.each in mc.listConnections(self.sel): 
                if mc.objectType(self.each, isType='parentConstraint') or mc.objectType(self.each, isType='scaleConstraint') : 
                    if not self.each in self.constraints: 
                        self.constraints.append(self.each)                
            print self.listLoc            
            mc.delete(self.constraints)
            mc.delete(self.listLoc)

    def autoTranfer (self,arg):
        self.listSel = mc.ls(selection = True) 

        if not mc.objExists('ARLoc_Grp'):
                mc.group( em=True, name='ARLoc_Grp')
        self.bakeLoc = []
        self.delPar = []
        self.delScale = []
        self.selList = []
        for self.sel in self.listSel:
            #self.locName = self.sel+"_loc"
            self.locName = self.sel.replace(':','_')+"_loc" #060117 edit because namespace AD_AR are change
            self.loc = mc.spaceLocator(p=(0,0,0),name = self.locName )
            self.parentLoc = mc.parentConstraint(self.sel,self.loc,maintainOffset = False)
            self.scaleLoc = mc.scaleConstraint(self.sel,self.loc,maintainOffset = False) #
            self.bakeLoc.append(self.loc[0]) #because loc is list
            self.delPar.append(self.parentLoc[0]) #because delPar is list
            self.selList.append(self.sel)
            #mc.bakeResults(self.loc,simulation=True,time = (self.timeSliderMin,self.timeSliderMax))
            #mc.delete(self.parentLoc)
            #mc.cutKey(self.sel, option='keys')
            #self.parentCon = mc.parentConstraint(self.loc,self.sel,maintainOffset = True)
            #self.scaleCon = mc.scaleConstraint(self.loc,self.sel,maintainOffset = True)
            #mc.parent(self.loc,'ARLoc_Grp')
            #mc.cutKey(self.loc,time=((self.timeSliderMin+1), (self.timeSliderMax-1)), option='keys')
        
        print self.delPar
        self.animNodes = mc.ls (type='animCurve')
        self.firstKey = mc.findKeyframe(self.animNodes,which='first')
        self.lastKey = mc.findKeyframe(self.animNodes,which='last')

        if self.firstKey < 101:
            self.firstKey = 101

        # isolate viewport for faster baking 
        mayaTools.isolateObj(True) 

        # bake locator 
        mc.bakeResults(self.bakeLoc,simulation=True,time = (self.firstKey,self.lastKey))

        # restore viewport back
        mayaTools.isolateObj(False)

        mc.delete(self.delPar)
        mc.delete(self.delScale)
        mc.cutKey(self.selList, option='keys')
        #return
        for self.sel in self.listSel:
            #self.locName = self.sel+"_loc"
            self.locName = self.sel.replace(':','_')+"_loc" #060117 edit because namespace AD_AR are change
            #mc.cutKey(self.sel, option='keys')
            self.parentCon = mc.parentConstraint(self.locName,self.sel,maintainOffset = False) #True
            self.scaleCon = mc.scaleConstraint(self.locName,self.sel,maintainOffset = False)
            mc.parent(self.locName,'ARLoc_Grp')
            for shotSq in mc.sequenceManager(listShots = True):
                self.currentShotStart = mc.shot( shotSq,q=True,st=True)
                self.currentShotEnd = mc.shot (shotSq,q=True,et=True )

                mc.cutKey(self.locName,time=((self.currentShotStart+1), (self.currentShotEnd-1)), option='keys')



    def tranferKey (self,arg):
        
        self.listSel = mc.ls(selection = True) 

        if not mc.objExists('ARLoc_Grp'):
                mc.group( em=True, name='ARLoc_Grp')

        self.bakeLoc = []
        self.delPar = []
        self.delScale = []
        self.selList = []

        for self.sel in self.listSel:
            #self.locName = self.sel+"_loc"
            self.locName = self.sel.replace(':','_')+"_loc" #060117 edit because namespace AD_AR are change
            self.loc = mc.spaceLocator(p=(0,0,0),name = self.locName )
            self.parentLoc = mc.parentConstraint(self.sel,self.loc,maintainOffset = False)
            self.scaleLoc = mc.scaleConstraint(self.sel,self.loc,maintainOffset = False) #
            self.bakeLoc.append(self.loc[0]) #because loc is list
            self.delPar.append(self.parentLoc[0]) #because delPar is list
            self.delScale.append(self.scaleLoc[0])
            self.selList.append(self.sel)
        
        print self.delPar
        self.animNodes = mc.ls (type='animCurve')
        self.firstKey = mc.findKeyframe(self.animNodes,which='first')
        self.lastKey = mc.findKeyframe(self.animNodes,which='last')

        if self.firstKey < 101:
            self.firstKey = 101

        # isolate viewport for faster baking 
        mayaTools.isolateObj(True) 

        # bake locator 
        mc.bakeResults(self.bakeLoc,simulation=True,time = (self.firstKey,self.lastKey))

        # restore viewport back
        mayaTools.isolateObj(False)

        mc.delete(self.delPar)
        mc.delete(self.delScale)
        mc.cutKey(self.selList, option='keys')

        mm.eval('warning "Delete List Edit and Connect Locator 2/2 ";')
        mc.confirmDialog(title='Warning', message='Remove Assembly List Edit first', button=['OK'])
        

    def connectLoc (self,arg):
        locName = mc.ls(sl=True)
        self.listSel = []
        for loc in locName:
            print loc
            #gpu_name = loc.split('_loc')
            gpuNameSpace = loc.rsplit('_',5)[0] #060117 edit because namespace AD_AR are change
            nameSplit = loc.split(gpuNameSpace)[1].split('_',1)[1].split('_loc')[0]
            gpu_name = '%s:%s'%(gpuNameSpace,nameSplit)
            self.listSel.append(gpu_name)

        #self.listSel = mc.ls(selection = True)

        mc.select(clear=True)
        for self.sel in self.listSel:
            #self.locName = self.sel+"_loc"

            self.locName = self.sel.replace(':','_')+"_loc" #060117 edit because namespace AD_AR are change
            #mc.cutKey(self.sel, option='keys')
            self.parentCon = mc.parentConstraint(self.locName,self.sel,maintainOffset = False) #True
            self.scaleCon = mc.scaleConstraint(self.locName,self.sel,maintainOffset = False)
            mc.parent(self.locName,'ARLoc_Grp')
            for shotSq in mc.sequenceManager(listShots = True):
                self.currentShotStart = mc.shot( shotSq,q=True,st=True)
                self.currentShotEnd = mc.shot (shotSq,q=True,et=True )

                mc.cutKey(self.locName,time=((self.currentShotStart+1), (self.currentShotEnd-1)), option='keys')
       
       