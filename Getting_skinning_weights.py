import maya.standalone
import maya.cmds as cmds
import maya.mel as mel
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma
import argparse
import os 
import numpy as np
import utils

maya.standalone.initialize(name='python')

# Load the FBX plugin
if not cmds.pluginInfo('fbxmaya', query=True, loaded=True):
    cmds.loadPlugin('fbxmaya')
args = utils.get_args()



### Main Process ###
def main():
    
    # Source Loading

    Tpose_char = './TruelyTruelyUsing/Asooni.fbx'
    mel.eval('FBXImport -f"{}"'.format(Tpose_char))
    char_name = Tpose_char.split('/')[-1].split('.')[0]
        
    meshes = cmds.ls(type='mesh')
    joints = cmds.ls(type='joint')
    Data_mesh = []
    Data_mesh_orig = []
    Data_joint = []

    # Source Mesh Loading

    for mesh in meshes :
        if mesh[-4:] != "Orig" :
            weights, joints = utils.get_skin_weights(mesh)
            print(weights.shape)


if __name__ == "__main__":
    main()