# Written by TA
# ta@picturethisanimation.com
# this module read transform of the assets and write into a json data. 
# from json data, create/update asset position according to transform store in data file. 
# modify at your own risk. 

# v.0.0.1 - support build locator
# v.0.0.2 - update asm and loc mode 
# v.0.0.3 - switchable between asm and loc
# v.0.0.4 - update function work 

# dependency need 
# asm_utils.py / sd_utils.py


import sys
import os 
from collections import OrderedDict
import yaml
import logging 
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
logger.setLevel(logging.INFO)

import yaml
import maya.cmds as mc 

from tool.sceneAssembly import asm_utils
from tool.setDress.utils import sd_utils

# this should be config
attrDescription = 'description'
outputDescription = 'output'
outputList = ['asm', 'loc']


def export(root, path): 
    """ export transform data to file 
    root is top Grp
    path is export path """ 
    data = OrderedDict()
    currentSels = mc.ls(sl=True)

    if mc.objExists(root): 
        rootLongName = mc.ls(root, l=True)[0]
        rootShortName = mc.ls(root)[0]
        replaceRoot = rootLongName.replace(rootShortName, '')
        childs = [rootLongName]


        # list through hierarchy
        mc.select(root, hi=True)
        childs += mc.ls(sl=True, l=True)
        # childs += mc.listRelatives(root, ad=True, f=True)
        
        for child in childs:
            # filter node 
            isRoot = False
            if node_filter(child): 
                # name = child.replace('%s' % replaceRoot, '')
                name = remove_root(child, replaceRoot)
                nodeType = mc.objectType(child)
                parent = mc.listRelatives(child, p=True, f=True)
                shortName = mc.ls(child)[0]
                shape = mc.listRelatives(child, s=True, f=True)
                topRootLong = rootLongName
                topRoot = root
                position = mc.xform(child, q=True, ws=True, m=True)
                
                if shape: 
                    # shape = shape[0].replace('%s' % replaceRoot, '')
                    shape = remove_root(shape[0], replaceRoot)

                if parent: 
                    # parent = parent[0].replace('%s' % replaceRoot, '')
                    parent = remove_root(parent[0], replaceRoot)

                    # this is root 
                    # if '%s|' % parent == replaceRoot: 
                    if root == name: 
                        parent = None
                        isRoot = True

                else: 
                    parent = None 
                    isRoot = True

                asset, namespace = get_asset(child, nodeType)

                valueDict = OrderedDict()

                # data.update({str(name): {'shortName': str(shortName), 'nodeType': str(nodeType), 
                #                     'parent': str(parent), 'shape': str(shape), 'topRootLong': str(topRootLong), 
                #                     'topRoot': str(root), 'position': position, 'asset': str(asset), 'namespace': namespace}})

                valueDict['shortName'] = str(shortName)
                valueDict['nodeType'] = str(nodeType)
                valueDict['parent'] = str(parent)
                valueDict['shape'] = str(shape)
                valueDict['topRootLong'] = str(topRootLong)
                valueDict['topRoot'] = str(topRoot)
                valueDict['position'] = position
                valueDict['asset'] = str(asset)
                valueDict['namespace'] = str(namespace)
                valueDict['root'] = isRoot
                data[str(name)] = valueDict

        if data: 
            if not os.path.exists(os.path.dirname(path)): 
                os.makedirs(os.path.dirname(path))

            ymlDumper(path, data)

    else: 
        logger.warning('"%s" does not exists' % root)

    mc.select(currentSels)


def node_filter(node): 
    """ filter node """ 
    nodeFilter = ['transform', 'assemblyReference', 'locator']

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
    namespace = None 
    if nodeType == 'assemblyReference': 
        path = mc.getAttr('%s.definition' % nodeName)
        namespace = asm_utils.getARNamespace(nodeName)

    return path, namespace

def create(path, root=None, sync=True, position=True, output='asm', refType='rsProxy'): 
    """ create asset from data """ 
    data = ymlLoader(path)

    if root: 
        data = change_root(root, data)

    # remove here 
    if sync: 
        targetRoot = root 
        if not root: 
            targetRoot = find_root(data)

        sceneList = list_hierarchy(targetRoot, listType=output)
        dataList = data.keys()
        addList, removeList = compare_list(sceneList, dataList)

        # clean remove or future add asset first 
        remove_assets(removeList, output)
        remove_assets(addList, output)

    # create process only 
    for key, value in data.iteritems(): 
        isRoot = value.get('root')
        node = create_node(key, data, position=position, output=output, refType=refType)

        if isRoot: 
            attr = attrDescription
            nodeAttr = '%s.%s' % (node, attr)
            outputAttr = '%s.%s' % (node, outputDescription)

            if not mc.objExists(nodeAttr): 
                mc.addAttr(node, ln=attr, dt='string')
                mc.setAttr(nodeAttr, e=True, keyable=True)

                mc.addAttr(node, ln=outputDescription, at='enum', en='%s:%s:' % (outputList[0], outputList[1]))
                mc.setAttr(outputAttr, e=True, keyable=True)

            mc.setAttr(nodeAttr, path, type='string')
            logger.info('attr %s set' % path)
            value = [index for index, a in enumerate(outputList) if output==a][0]
            mc.setAttr(outputAttr, value)


def update(root, path=None, sync=True): 
    """ update input root and create from output attr on root """
    attr = attrDescription
    nodeAttr = '%s.%s' % (root, attr)
    outputAttr = '%s.%s' % (root, outputDescription)

    if mc.objExists(nodeAttr) and mc.objExists(outputAttr): 
        if path: 
            mc.setAttr('%s.%s' % (root, attr), path, type='string')

        path = mc.getAttr(nodeAttr)
        output = mc.getAttr(outputAttr, asString=True)
        create(path, root=root, sync=True, position=True, output=output, refType='rsProxy')

    else: 
        logger.error('Attr %s not found' % nodeAttr)


def create_node(nodeKey, nodeData, position=True, output='asm', refType='rsProxy'): 
    """ create node from given data """ 
    shortName = nodeData.get(nodeKey).get('shortName')
    nodeType = nodeData.get(nodeKey).get('nodeType')
    parent = nodeData.get(nodeKey).get('parent')
    shape = nodeData.get(nodeKey).get('shape')
    topRootLong = nodeData.get(nodeKey).get('topRootLong')
    topRoot = nodeData.get(nodeKey).get('topRoot')
    position = nodeData.get(nodeKey).get('position')
    asset = nodeData.get(nodeKey).get('asset')
    namespace = nodeData.get(nodeKey).get('namespace')


    nodeName = None
    logger.debug('key %s' % nodeKey)

    # this is group 
    if not mc.objExists(nodeKey): 
        logger.info('%s not exists, create node' % nodeKey)
        if nodeType == 'transform': 
            if shape == 'None': 
                nodeName = mc.group(em=True, n=shortName)
                logger.info('create group %s' % nodeName)

        # this is assemblyReference 
        if nodeType == 'assemblyReference': 
            # print 'nodeName after rename', nodeName
            if output == 'asm': 
                nodeName = create_assembly(asset, shortName, namespace)
            if output == 'loc': 
                nodeName = create_loc(asset, nodeKey, shortName, namespace)
                # continue to build 
                sd_utils.build(locs=[nodeName], level=refType, lod='md', forceReplace=False, returnValue='normal', instance=False)
                logger.info('build asset to loc')

            logger.info('create assemblyReference %s' % nodeName)

    else: 
        logger.warning('%s already exists, skip' % nodeName)
        nodeName = nodeKey

    if nodeName: 
        # set xform 
        if position: 
            mc.xform(nodeName, ws=True, m=position)
            logger.info('set xform')

        # set parent 
        if not mc.objExists(parent): 
            if not parent == 'None': 
                parent = create_node(parent, nodeData, position=position, output=output, refType=refType)
            
        if not parent == 'None': 
            currentParent = mc.listRelatives(nodeName, p=True)
            if currentParent: 
                if not currentParent[0] == parent.split('|')[-1]: 
                    mc.parent(nodeName, parent)
            else: 
                # after parent, nodeName will change its longname. Assigned new long name after parent
                nodeName = mc.parent(nodeName, parent)

        logger.info('Finish creation process')

        return nodeName


def create_assembly(assetPath, shortName, namespace): 
    """ create AR node """ 
    nodeName = asm_utils.createARNode()
    asm_utils.setARDefinitionPath(nodeName, assetPath)
    asm_utils.setARNamespace(nodeName, namespace)
    lists = asm_utils.listRepIndex(nodeName, listType ='name')
    nodeName = mc.rename(nodeName, shortName)

    if lists: 
        name = 'Gpu'
        if name in lists: 
            asm_utils.setActiveRep(nodeName, name)
            logger.info('set active rep %s' % name)
        
        else: 
            logger.error('Failed to set active rep. %s is not in active rep' % name)

    return nodeName


def create_loc(assetPath, nodeKey, shortName, namespace): 
    """ create Loc node """ 
    nodeName = '%s' % shortName
    # make this long name 
    loc = '|%s' % mc.spaceLocator(n=nodeName)[0]
    
    sd_utils.addLocAttr(loc, assetPath, parent=False)
    return loc



def list_hierarchy(root, listType): 
    """ list hierarchy relative long name """ 
    assetList = []
    currentSels = mc.ls(sl=True)

    if mc.objExists(root): 
        rootLongName = mc.ls(root, l=True)[0]
        rootShortName = mc.ls(root)[0]
        replaceRoot = rootLongName.replace(rootShortName, '')

        mc.select(root, hi=True)
        childs = mc.ls(sl=True, l=True)

        if listType == 'asm': 
            for child in childs: 
                if node_filter(child): 
                    name = remove_root(child, replaceRoot)
                    assetList.append(name)

        if listType == 'loc': 
            for child in childs: 
                if mc.objectType(child, isType='transform'): 
                    if not mc.referenceQuery(child, isNodeReferenced=True): 
                        shape = mc.listRelatives(child, s=True, f=True)
                        name = remove_root(child, replaceRoot)
                        # this is locator 
                        if shape: 
                            if mc.objectType(shape[0], isType='locator'): 
                                assetList.append(name)
                        # this is group 
                        else: 
                            assetList.append(name)
                    else: 
                        continue

    mc.select(currentSels)

    return assetList


def compare_list(originalList, newList): 
    """ compare 2 list and return add, remove list """
    remove = [a for a in originalList if not a in newList]
    add = [a for a in newList if not a in originalList]

    return add, remove


def remove_assets(removeList, output): 
    """ remove asset and check if they are references or non-references """ 
    removeGrp = 'remove_if_found'
    if not mc.objExists(removeGrp): 
        mc.group(em=True, n=removeGrp)

    for each in removeList: 
        try: 
            mc.parent(each, removeGrp)
        except Exception as e: 
            logger.error('Cannot parent %s to %s' % (each, removeGrp))
            logger.error(e)

    # mc.delete(removeList)
    if mc.listRelatives(removeGrp, c=True): 
        sd_utils.removeSet(removeGrp=removeGrp, removeLoc=True)

    if mc.objExists(removeGrp): 
        mc.delete(removeGrp)


def change_root(root, data): 
    """ change root name on memory """ 
    oldRoot = find_root(data)
    newRoot = root
    newDict = OrderedDict()
    keyFilters = ['shortName', 'parent', 'shape', 'topRoot']

    for name, infoDict in data.iteritems(): 
        newName = name 

        if oldRoot in name: 
            newName = name.replace(oldRoot, newRoot)

        newDict[newName] = OrderedDict()

        for key, value in infoDict.iteritems(): 
            newValue = value 
            if key in keyFilters: 
                if oldRoot in value: 
                    newValue = value.replace(oldRoot, newRoot)
            newDict[newName][key] = newValue

    return newDict

def find_root(data): 
    for key, infoDict in data.iteritems(): 
        root = infoDict.get('root')

        if root: 
            return key

def remove_root(name, root): 
    """ remove root from name 
    |root| |root|group1 -> group1 
    | |group1 -> group1 """

    # root = '|root|c'
    # name = '|root|c|a|b|root|c'

    rootList = [a for a in root.split('|') if a]
    nameList = [a for a in name.split('|') if a]
    removeIndex = []

    # find remove index
    for i, v in enumerate(rootList): 
        if v == nameList[i]: 
            removeIndex.append(i)
            
    # reverse remove 
    for i in removeIndex[::-1]: 
        del nameList[i]
            
    newName = '|'.join(nameList)
    return newName


def check_update(): 
    """ check current root for newer version of shotDress definition and update if user agree """ 
    # find root in the scene 
    pass 


def refresh(node): 
    """ reapply description to this root """ 
    attr = '%s.%s' % (node, attrDescription)
    outputAttr = '%s.%s' % (node, outputDescription)

    if mc.objExists(attr) and mc.objExists(outputAttr): 
        path = mc.getAttr(attr)
        output = outputList[mc.getAttr(outputAttr)]
        create(path, root=node, sync=True, position=True, output=output, refType='rsProxy')
        logger.info('refresh success')


def ymlDumper(filePath, dictData) : 
    data = ordered_dump(dictData, Dumper=yaml.SafeDumper)
    # data = yaml.dump(dictData, default_flow_style=False)
    result = writeFile(filePath, data)
    logger.info('Write yml file success %s' % filePath)
    return result


def ymlLoader(filePath) : 
    stream = readFile(filePath)
    dictData = ordered_load(stream, yaml.SafeLoader)
    # dictData = yaml.load(data)
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


def ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=OrderedDict):
    class OrderedLoader(Loader):
        pass
    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))
    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)
    return yaml.load(stream, OrderedLoader)



def ordered_dump(data, stream=None, Dumper=yaml.Dumper, **kwds):
    class OrderedDumper(Dumper):
        pass
    def _dict_representer(dumper, data):
        return dumper.represent_mapping(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
            data.items())
    OrderedDumper.add_representer(OrderedDict, _dict_representer)
    return yaml.dump(data, stream, OrderedDumper, **kwds)


# example
# export 
# path = 'C:/Users/Ta/Documents/temp/asset.yml'
# pos_utils.export(root='shotDress', path=path)

# create 
# path = 'C:/Users/Ta/Documents/temp/asset.yml'
# pos_utils.create(path, root='shotDress', sync=True, position=True, output='loc', refType='rsProxy')

