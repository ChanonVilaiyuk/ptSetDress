# this module read transform of the assets and write into a json data. 
# from json data, create/update asset position according to transform store in data file. 

import sys
import os 
import logging 
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
logger.setLevel(logging.DEBUG)

import yaml
import maya.cmds as mc 

from tool.sceneAssembly import asm_utils


def export(root, path): 
    """ export transform data to file 
    root is top Grp
    path is export path """ 
    data = dict()

    if mc.objExists(root): 
        rootLongName = mc.ls(root, l=True)[0]
        rootShortName = mc.ls(root)[0]
        childs = [rootLongName]

        # list through hierarchy
        childs += mc.listRelatives(root, ad=True, f=True)
        
        for child in childs:
            # filter node 
            if node_filter(child): 
                name = child.replace('%s|' % rootLongName, '')
                nodeType = mc.objectType(child)
                parent = mc.listRelatives(child, p=True, f=True)
                shortName = mc.ls(child)[0]
                shape = mc.listRelatives(child, s=True, f=True)
                topRootLong = rootLongName
                topRoot = root
                position = mc.xform(child, q=True, ws=True, m=True)
                
                if shape: 
                    shape = shape[0].replace('%s|' % rootLongName, '')
                if parent: 
                    parent = parent[0].replace('%s|' % rootLongName, '')
                    if not parent: 
                        parent = rootShortName

                # if this is root 
                if rootLongName == child: 
                    removeParent = child.replace(shortName, '')
                    name = child.replace(removeParent, '')
                    parent = None
                    if shape: 
                        shape = shape[0]

                asset = get_asset(child, nodeType)

                data.update({str(name): {'shortName': str(shortName), 'nodeType': str(nodeType), 
                                    'parent': str(parent), 'shape': str(shape), 'topRootLong': str(topRootLong), 
                                    'topRoot': str(root), 'position': position, 'asset': str(asset)}})

        if data: 
            if not os.path.exists(os.path.dirname(path)): 
                os.makedirs(os.path.dirname(path))

            ymlDumper(path, data)

    else: 
        logger.warning('"%s" does not exists' % root)


def node_filter(node): 
    """ filter node """ 
    nodeFilter = ['transform', 'assemblyReference']

    if mc.objectType(node) in nodeFilter: 
        shape = mc.listRelatives(node, s=True)

        if mc.objectType(node) == 'transform': 
            if shape: 
                if shape[0] in nodeFilter: 
                    return True
                else: 
                    return False
            return True
        return True

def get_asset(nodeName, nodeType): 
    """ get asset depend on node """ 
    path = None 

    if nodeType == 'assemblyReference': 
        path = mc.getAttr('%s.definition' % nodeName)

    return path 

def create(path, root=None): 
    """ create asset from data """ 
    data = ymlLoader(path)

    for key, value in data.iteritems(): 
        create_node(key, data)


def create_node(nodeKey, nodeData): 
    """ create node from given data """ 
    shortName = nodeData.get('shortName')
    nodeType = nodeData.get('nodeType')
    parent = nodeData.get('parent')
    shape = nodeData.get('shape')
    topRootLong = nodeData.get('topRootLong')
    topRoot = nodeData.get('topRoot')
    position = nodeData.get('position')
    asset = nodeData.get('asset')

    nodeName = None

    # this is group 
    if nodeType == 'transform': 
        if not shape: 
            nodeName = mc.group(em=True, n=shortName)


    # this is assemblyReference 
    if nodeType == 'assemblyReference': 
        nodeName = asm_utils.createARNode()
        asm_utils.setARDefinitionPath(nodeName, asset)
        lists = asm_utils.listRepIndex(nodeName, listType ='name')

        if lists: 
            name = 'Grp'
            if name in lists: 
                asm_utils.setActiveRep(nodeName, name)

    if nodeName: 
        # set xform 
        mc.xform(nodeName, ws=True, m=position)

        # set parent 


def ymlDumper(filePath, dictData) : 
    data = yaml.dump(dictData, default_flow_style=False)
    result = writeFile(filePath, data)
    logger.info('Write yml file success %s' % filePath)
    return result


def ymlLoader(filePath) : 
    data = readFile(filePath)
    dictData = yaml.load(data)
    return dictData


def writeFile(file, data) : 
    f = open(file, 'w')
    f.write(data)
    f.close()
    return True
    

def readFile(file) : 
    f = open(file, 'r')
    data = f.read()
    f.close()
    return data