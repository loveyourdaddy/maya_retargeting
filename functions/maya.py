import os
import numpy as np
import maya.cmds as cmds
import maya.mel as mel
import maya.api.OpenMaya as om

def freeze_and_bake(top_joint):
    # freeze
    incoming_connections = {}
    for attr in ['rotateX', 'rotateY', 'rotateZ']:
        # top joint 
        full_attr = f"{top_joint}.{attr}"
        connections = cmds.listConnections(full_attr, s=True, d=False, p=True)
        if connections:
            incoming_connections[attr] = connections[0]
            cmds.disconnectAttr(connections[0], full_attr)

    # bake
    cmds.bakeResults("{}".format(top_joint), simulation=True, t=(cmds.playbackOptions(q=True, min=True), cmds.playbackOptions(q=True, max=True)), sampleBy=1, oversamplingRate=1, disableImplicitControl=True, preserveOutsideKeys=True, sparseAnimCurveBake=False, removeBakedAnimFromLayer=False, bakeOnOverrideLayer=False, minimizeRotation=True, controlPoints=False, shape=True)

# export
def export(args, target_char, targetMotion):
    output_dir = args.tgt_motion_path + target_char
    os.makedirs(output_dir, exist_ok=True)

    # export 
    export_file = output_dir+'/'+targetMotion+'.fbx'
    cmds.FBXResetExport()
    mel.eval('FBXExportSmoothingGroups -v true')
    mel.eval('FBXExportEmbeddedTextures -v true')
    mel.eval('FBXExport -f"{}"'.format(export_file))
    print(">> File export to ", export_file)

""" matrix """
def matrix_to_mmatrix(matrix):
    # For 3x3 rotation matrix
    if matrix.shape == (3, 3):
        # Convert 3x3 to 4x4 by adding translation and perspective components
        matrix_4x4 = np.eye(4, dtype=np.float32)
        matrix_4x4[:3, :3] = matrix
    else:
        matrix_4x4 = matrix

    # Flatten the matrix and convert to list for MMatrix constructor
    matrix_list = matrix_4x4.flatten().tolist()
    
    return om.MMatrix(matrix_list)