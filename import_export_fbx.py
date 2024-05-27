import maya.standalone
maya.standalone.initialize(name='python')

import maya.cmds as cmds
import maya.mel as mel
import argparse

"""
usage 
1. window cmd 
mayapy D:\2024_KAI_Retargeting\import_export_fbx.py 
--SrcMotionDir ""
--TgtCharDir ""
--TgtMotionDir ""
"""
# Load the FBX plugin
if not cmds.pluginInfo('fbxmaya', query=True, loaded=True):
    cmds.loadPlugin('fbxmaya')

def get_parser():
    parser = argparse.ArgumentParser(description='Import an FBX file into Maya')
    parser.add_argument('--src_motion_path', type=str, default="D:/2024_KAI_Retargeting/Adori/animation/0055_Freestyle002_03_RT0214.fbx")
    parser.add_argument('--tgt_char_path', type=str, default="D:/2024_KAI_Retargeting/Adori/SKM_ADORI_0229.fbx")
    parser.add_argument('--tgt_motion_path', type=str, default="D:/2024_KAI_Retargeting/Adori/exported.fbx")
    return parser

def get_args():
    parser = get_parser()
    return parser.parse_args()


# load source
args = get_args() # get_args.parse_args
print(args)

strDir = args.SrcMotionDir
mel.eval('FBXImport -f"{}"'.format(strDir))

# load target 
targetDir = args.TgtCharDir
mel.eval('FBXImport -f"{}"'.format(targetDir))

# todo: export fbx
exportDir = args.TgtMotionDir 
mel.eval('FBXExport  -f"{}"'.format(exportDir))
# Adori

maya.standalone.uninitialize()
