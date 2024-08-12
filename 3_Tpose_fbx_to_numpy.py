import maya.standalone
import maya.cmds as cmds
import maya.mel as mel
import maya.api.OpenMaya as om
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
    Tpose_char = './TruelyTruelyUsing/PeasantMan.fbx'
    mel.eval('FBXImport -f"{}"'.format(Tpose_char))
    char_name = Tpose_char.split('/')[-1].split('.')[0]
        
    meshes = cmds.ls(type='mesh')
    joints = cmds.ls(type='joint')
    Data_mesh = []
    Data_mesh_orig = []
    Data_joint = []

    # Source joint Loading
    for joint in joints :
            Dat = utils.get_frame_range_joint_data(joint, 0, 0)
            Data_joint.append(Dat.reshape(-1).tolist())

    # Source Mesh Loading
    for mesh in meshes :
        Dat = utils.get_frame_range_mesh_data(mesh, 0, 0).reshape(-1,3)
        if mesh[-4:]!='Orig' :
            for j in range(len(Dat)) :
                Data_mesh.append(Dat[j])
        else :
            for j in range(len(Dat)) :
                Data_mesh_orig.append(Dat[j])

    Data_joint = np.array(Data_joint)
    Data_mesh_orig = np.array(Data_mesh_orig)
    Data_mesh = np.array(Data_mesh)
    # position + rotation is for joints
    np.save("TruelyTruelyUsing/" + char_name + "_joint" + ".fbx", Data_joint)
    np.save("TruelyTruelyUsing/" + char_name + "_mesh" + ".fbx", Data_mesh)
    np.save("TruelyTruelyUsing/" + char_name + "_mesh_orig" + ".fbx", Data_mesh_orig)



if __name__ == "__main__":
    main()



"""
usage
- mayapy Tpose_fbx_to_numpy.py --Tpose_char 'path/Tpose.fbx'

Window 
D:\_Program\AutoDesk\Maya2023\Maya2023\bin\mayapy Tpose_fbx_to_numpy.py --Tpose_char 'path/Tpose.fbx'

Mac
/Applications/Autodesk/maya2024/Maya.app/Contents/MacOS/mayapy Tpose_fbx_to_numpy.py --Tpose_char 'path/Tpose.fbx'
'./models/Adori/Adori.fbx'

/Applications/Autodesk/maya2024/Maya.app/Contents/MacOS/mayapy Tpose_fbx_to_numpy.py
"""
