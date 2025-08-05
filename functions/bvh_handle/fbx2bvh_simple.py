"""
This should be done in bpy conda env 
This code comes from https://github.com/rubenvillegas/cvpr2018nkn/blob/master/datasets/fbx2bvh.py

conda activate bpy
blender --background --python functions/bvh_handle/fbx2bvh.py

"""
import bpy
import numpy as np
import os
from os import listdir

data_path = './motions/Asooni/'
save_path = './motions/Asooni/'
os.makedirs(save_path, exist_ok=True)
files = sorted([f for f in listdir(data_path) if not f.startswith(".")])
files = [f for f in files if os.path.isfile(os.path.join(data_path, f))]
for f in files:
    # for f in files: 
    sourcepath = data_path + f
    dumppath = save_path + f.split(".fbx")[0].strip('0000_') + ".bvh"
    dumppath = dumppath.replace(' ',"_").replace('(1)','')
    
    if os.path.exists(dumppath):
        continue

    bpy.ops.import_scene.fbx(filepath=sourcepath)

    frame_start = 9999
    frame_end = -9999
    action = bpy.data.actions[-1]
    if action.frame_range[1] > frame_end:
        frame_end = action.frame_range[1]
    if action.frame_range[0] < frame_start:
        frame_start = action.frame_range[0]

    frame_start = int(frame_start)
    frame_end = int(frame_end)
    bpy.ops.export_anim.bvh(filepath=dumppath,
                            frame_start=frame_start,
                            frame_end=frame_end, root_transform_only=True)
    bpy.data.actions.remove(bpy.data.actions[-1])

    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    print(data_path + f + "/" + f + " processed.")