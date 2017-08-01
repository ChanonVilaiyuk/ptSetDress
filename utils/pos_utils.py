# this module read transform of the assets and write into a json data. 
# from json data, create/update asset position according to transform store in data file. 

import sys
import os 
from collections import OrderedDict
import yaml
import logging 
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
logger.setLevel(logging.DEBUG)

import yaml
import maya.cmds as mc 

from tool.sceneAssembly import asm_utils
reload(asm_utils)


def export(root, path): 
    """ export transform data to file 
    root is top Grp
    path is export path """ 
    data = OrderedDict()

    if mc.objExists(root): 
        rootLongName = mc.ls(root, l=True)[0]
        rootShortName = mc.ls(root)[0]
        replaceRoot = rootLongName.replace(rootShortName, '')
        childs = [rootLongName]

        # list through hierarchy
        childs += mc.listRelatives(root, ad=True, f=True)
        
        for child in childs:
            # filter node 
            if node_filter(child): 
                name = child.replace('%s' % replaceRoot, '')
                nodeType = mc.objectType(child)
                parent = mc.listRelatives(child, p=True, f=True)
                shortName = mc.ls(child)[0]
                shape = mc.listRelatives(child, s=True, f=True)
                topRootLong = rootLongName
                topRoot = root
                position = mc.xform(child, q=True, ws=True, m=True)
                
                if shape: 
                    shape = shape[0].replace('%s' % replaceRoot, '')
                if parent: 
                    parent = parent[0].replace('%s' % replaceRoot, '')

                    # this is root 
                    if '%s|' % parent == replaceRoot: 
                        parent = None

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
                data[str(name)] = valueDict

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
    namespace = None 
    if nodeType == 'assemblyReference': 
        path = mc.getAttr('%s.definition' % nodeName)
        namespace = asm_utils.getARNamespace(nodeName)

    return path, namespace

def create(path, root=None): 
    """ create asset from data """ 
    data = ymlLoader(path)

    for key, value in data.iteritems(): 
        create_node(key, data)


def create_node(nodeKey, nodeData): 
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
            nodeName = asm_utils.createARNode()
            asm_utils.setARDefinitionPath(nodeName, asset)
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

            logger.info('create assemblyReference %s' % nodeName)

    else: 
        logger.warning('%s already exists, skip' % nodeName)
        nodeName = nodeKey

    if nodeName: 
        # set xform 
        mc.xform(nodeName, ws=True, m=position)
        logger.info('set xform')

        # set parent 
        if not mc.objExists(parent): 
            if not parent == 'None': 
                parent = create_node(parent, nodeData)
            
        if not parent == 'None': 
            currentParent = mc.listRelatives(nodeName, p=True)
            if currentParent: 
                if not currentParent[0] == parent.split('|')[-1]: 
                    mc.parent(nodeName, parent)
            else: 
                mc.parent(nodeName, parent)

        logger.info('finish creation process')

        return nodeName


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

# usage example:
# ordered_load(stream, yaml.SafeLoader)
# usage:
# ordered_dump(data, Dumper=yaml.SafeDumper)