import os, sys
sys.path.append('C:\Program Files\Autodesk\Maya2016\Python\Lib\site-packages')
currPath = os.path.dirname(os.path.realpath(__file__))
print currPath

import pysideuic
pysideuic.compileUiDir(currPath)
