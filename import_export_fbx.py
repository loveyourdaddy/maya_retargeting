import maya.standalone
maya.standalone.initialize(name='python')
import maya.cmds as cmds
import maya.mel as mel
import argparse
import os 

"""
usage
- mayapy import_export_fbx.py --src_motion_path "" --tgt_char_path "" --tgt_motion_path ""
"""
# mayapy import_export_fbx.py --sourceMotion "./motions/Adori/animation/0055_Freestyle002_03_RT0214.fbx" --targetChar "./models/Dancstruct/SKM_ADORI_0229.fbx"
# D:\_Program\AutoDesk\Maya2023\Maya2023\bin\mayapy mayapy import_export_fbx.py --sourceMotion "./motions/Adori/animation/0055_Freestyle002_03_RT0214.fbx" --targetChar "./models/Dancstruct/SKM_ADORI_0229.fbx"

# dynamic dict 

# Load the FBX plugin
if not cmds.pluginInfo('fbxmaya', query=True, loaded=True):
    cmds.loadPlugin('fbxmaya')

def get_parser():
    parser = argparse.ArgumentParser(description='Import an FBX file into Maya')
    parser.add_argument('--sourceMotion', type=str, default="./motions/Adori/animation/0055_Freestyle002_03_RT0214.fbx")
    parser.add_argument('--targetChar', type=str, default="./models/Dancstruct/SKM_ADORI_0229.fbx")
    parser.add_argument('--tgt_motion_path', type=str, default="./output/")
    return parser

def get_args():
    parser = get_parser()
    return parser.parse_args()


# load source
args = get_args()

"""
order :
load target char -> load motion 
"""
# load target 
targetChar = args.targetChar
mel.eval('FBXImport -f"{}"'.format(targetChar))
# target char
target_char = targetChar.split('/')[-1].split('.')[0]

# load motion 
sourceMotion = args.sourceMotion
mel.eval('FBXImport -f"{}"'.format(sourceMotion))
target_motion = sourceMotion.split('/')[-1].split('.')[0]

# export
output_dir = args.tgt_motion_path + target_char
os.makedirs(output_dir, exist_ok=True)
export_file = output_dir+'/'+target_motion+'.fbx'
mel.eval('FBXExport -f"{}"'.format(export_file))

maya.standalone.uninitialize()

print("File export to ", export_file)
