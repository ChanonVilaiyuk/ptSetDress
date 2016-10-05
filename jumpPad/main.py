import maya.cmds as mc
import maya.OpenMayaUI as mui
from PySide import QtCore, QtGui
from qtshim import wrapinstance

from tool.setDress.jumpPad import ui
reload(ui)

def getMayaWindow():
    ptr = mui.MQtUtil.mainWindow()
    if ptr is None:
        raise RuntimeError('No Maya window found.')
    window = wrapinstance(long(ptr))
    assert isinstance(window, QtGui.QMainWindow)
    return window

preset = {'FRD_unit':360, 'CTY_unit':48}
	
class MyDialog(ui.Ui_DlgGridJump, QtGui.QWidget):
	def __init__(self, parent=None):
		super(MyDialog, self).__init__(parent)
		self.setupUi(self)
		self.setObjectName('gridJump') 
		self.setWindowFlags(QtCore.Qt.Window)
		
		self.initConnect()
		self.initUi()
		
	def initUi(self):
		self.cmbPresetSel.addItem('FRD_unit')
		self.cmbPresetSel.addItem('CTY_unit')
		self.cmbPresetSel.setCurrentIndex(0)
		
	def initConnect(self):
		self.cmbPresetSel.currentIndexChanged.connect(self.changePreset)
		
		self.btnZPlus.clicked.connect(self.jumpZPlus)
		self.btnZMinus.clicked.connect(self.jumpZMinus)
		self.btnXPlus.clicked.connect(self.jumpXPlus)
		self.btnXMinus.clicked.connect(self.jumpXMinus)
		self.btnCCW.clicked.connect(self.rotateYPlus)
		self.btnCW.clicked.connect(self.rotateYMinus)
		
	def changePreset(self):
		self.txtUnitValue.setPlainText(str(preset[self.cmbPresetSel.currentText()]))
	
	def jumpZPlus(self):
		if self.rdbMoveMode.isChecked():
			mc.move(float(self.txtUnitValue.toPlainText()), r=True, z=True)
			
		elif self.rdbAttachMode.isChecked():
			sel = mc.ls(selection=True)		
			
			for i in range(len(sel)-1):
				mainPos = mc.xform(sel[i], q=True, translation=True)
				mainBBMax  = mc.getAttr(sel[i]+'.boundingBoxMax')[0]
				nextPos = mc.xform(sel[i+1], q=True, translation=True)
				nextBBMin = mc.getAttr(sel[i+1]+'.boundingBoxMin')[0]
				
				mc.move(mainPos[0], mainPos[1], mainBBMax[2]+(nextPos[2]-nextBBMin[2]), sel[i+1])
	
	def jumpZMinus(self):
		if self.rdbMoveMode.isChecked():
			mc.move(-float(self.txtUnitValue.toPlainText()), r=True, z=True)
			
		elif self.rdbAttachMode.isChecked():
			sel = mc.ls(selection=True)		
			
			for i in range(len(sel)-1):
				mainPos = mc.xform(sel[i], q=True, translation=True)
				mainBBMin  = mc.getAttr(sel[i]+'.boundingBoxMin')[0]
				nextPos = mc.xform(sel[i+1], q=True, translation=True)
				nextBBMax = mc.getAttr(sel[i+1]+'.boundingBoxMax')[0]
				
				mc.move(mainPos[0], mainPos[1], mainBBMin[2]+(nextPos[2]-nextBBMax[2]), sel[i+1])
		
	def jumpXPlus(self):
		if self.rdbMoveMode.isChecked():
			mc.move(float(self.txtUnitValue.toPlainText()), r=True, x=True)
			
		elif self.rdbAttachMode.isChecked():
			sel = mc.ls(selection=True)		
			
			for i in range(len(sel)-1):
				mainPos = mc.xform(sel[i], q=True, translation=True)
				mainBBMax  = mc.getAttr(sel[i]+'.boundingBoxMax')[0]
				nextPos = mc.xform(sel[i+1], q=True, translation=True)
				nextBBMin = mc.getAttr(sel[i+1]+'.boundingBoxMin')[0]
				
				mc.move(mainBBMax[0]+(nextPos[0]-nextBBMin[0]), mainPos[1], mainPos[2], sel[i+1])
		
	def jumpXMinus(self):
		if self.rdbMoveMode.isChecked():
			mc.move(-float(self.txtUnitValue.toPlainText()), r=True, x=True)
			
		elif self.rdbAttachMode.isChecked():
			sel = mc.ls(selection=True)		
			
			for i in range(len(sel)-1):
				mainPos = mc.xform(sel[i], q=True, translation=True)
				mainBBMin  = mc.getAttr(sel[i]+'.boundingBoxMin')[0]
				nextPos = mc.xform(sel[i+1], q=True, translation=True)
				nextBBMax = mc.getAttr(sel[i+1]+'.boundingBoxMax')[0]
				
				mc.move(mainBBMin[0]+(nextPos[0]-nextBBMax[0]), mainPos[1], mainPos[2], sel[i+1])
		
	def rotateYPlus(self):
		sel = mc.ls(selection=True)
		mc.rotate(90, r=True, y=True)
		
	def rotateYMinus(self):
		sel = mc.ls(selection=True)
		mc.rotate(-90, r=True, y=True)