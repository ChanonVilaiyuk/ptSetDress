from tool.setDress.utils import asmAssetExport, sd_utils
reload(asmAssetExport)
reload(sd_utils)
from tool.utils import fileUtils, entityInfo, pipelineTools 
reload(entityInfo)
reload(pipelineTools)

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

import maya.cmds as mc 

""" export asset assembly locator """
asset = entityInfo.info()
asset.thisScene()
asmAssetExport.run(asset.thisScene())

""" export shot assembly locator """ 
mc.refresh(suspend = True)
sd_utils.exportShotAsmLocator()
mc.refresh(suspend = False)
mc.refresh(force = True)


""" import locator + build """
locs = sd_utils.importAssetAsmLocator()
sd_utils.build(locs)

""" rebuilt """
sd_utils.build(locs, level='vProxy', lod='md', forceReplace=True)

""" anim export asm description """
pipelineTools.exportAsmSet()

""" anim import asset locator """
sd_utils.importShotAsmLocator()

""" merge locator to shot """
sd_utils.mergeAsmLocator('lpl_lab', target='asset')
sd_utils.mergeAsmLocator('lpl_lab', target='shot')

""" get hero abc """
abcFile = sd_utils.getShotAsmHero('lpl_lab')
abcFile = sd_utils.getShotAssetAsmLocator('lpl_lab')

""" compare file """
add, remove = sd_utils.compareLoc('lpl_lab_loc', abcFile)

""" merge asm locator """
sd_utils.mergeAsmLocator('lpl_lab', target='shot', sync=True)

""" connect empty locator """
sd_utils.connectEmptyLocator('lpl_lab_loc')

""" remove set """
sd_utils.removeSet('lpl_lab_frd_bdgCityH1_loc', removeLoc=False)

from tool.setDress.utils import sd_utils
reload(sd_utils)
""" publish work and create AR """ 
sd_utils.publishWork(ar=True)
""" publish AD """ 
sd_utils.publishAD()

""" create Locator from ref AD and AR """
from tool.setDress.utils import asmAssetExport
reload(asmAssetExport)
from tool.utils import entityInfo
reload(entityInfo)
asset = entityInfo.info()
asset.thisScene()
asmAssetExport.run(asset.thisScene())

""" publish set dress work module """
sd_utils.publishWork(ar=True)
sd_utils.publishAD()

asset = entityInfo.info()
asmAssetExport.run(asset.thisScene())

""" build asset loc """
locs = sd_utils.importAssetAsmLocator()
sd_utils.build(locs)
sd_utils.build(locs, level='vProxy', lod='md', forceReplace=True)

""" animation export loc """
sd_utils.exportShotAsmLocator()

""" anim clean """
# import all sets locator @anim clean
locs = sd_utils.importShotAsmLocator()
# connect loc
sd_utils.connectEmptyLocator('lpl_lab_loc')

""" Merge """ 
# compare current with asset locator 
# target : compare shot/asset
# removeAsset : True -> excessive asset, remove 
# buildAsset : True -> build new asset locator 
# removeAsset=True, buildAsset=True -> this mean sync exactly the same with target
# removeAsset=False, buildAsset=False -> this mean merge only position
sd_utils.mergeAsmLocator('lpl_lab', target='asset', removeAsset=True, buildAsset=True)
sd_utils.mergeAsmLocator('lpl_lab', target='shot', removeAsset=False, buildAsset=True, mergeMode='merge-only')

""" get shot locator information """ 
sd_utils.getShotAsmLocator()
# Result: {'lpl_lab': {'version': [u'P:/Lego_Pipeline/film/episode/q0010/s0010/anim/data/assembly/lpl_lab/ppl_ep_q0010_s0010_anim_v003_lpl_lab.abc'], 'hero': u'P:/Lego_Pipeline/film/episode/q0010/s0010/anim/data/assembly/lpl_lab/ppl_ep_q0010_s0010_anim_lpl_lab.abc'}} # 

""" get all sets associated with this shot """
sets = sd_utils.getShotSetAsset()

heroFile = sd_utils.getShotAsmHero(assetName)
versionFiles = sd_utils.getShotAsmVersion(assetName)

""" merge with file """
sd_utils.mergeAsmLocator(abcFile=abcHero, removeAsset=False, buildAsset=False, mergeMode='merge-add')