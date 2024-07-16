import maya.cmds as cmds
import os
import maya.cmds as cmds
import maya.mel as mel
import maya.standalone

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
    mel.eval('FBXExport -f"{}"'.format(export_file))
    print("File export to ", export_file)
