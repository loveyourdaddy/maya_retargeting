
import maya.cmds as cmds
import numpy as np

def get_keyframe_data(joint):
    # keyframe 
    trans_data = {'translateX': [], 'translateY': [], 'translateZ': []}
    for attr in trans_data.keys():
        keyframe_count = cmds.keyframe(f'{joint}.{attr}', query=True, keyframeCount=True)
        if keyframe_count > 0:
            times = cmds.keyframe(f'{joint}.{attr}', query=True, timeChange=True)
            values = cmds.keyframe(f'{joint}.{attr}', query=True, valueChange=True)
            trans_data[attr] = list(zip(times, values))
            
    # rot 
    rot_data = {'rotateX': [], 'rotateY': [], 'rotateZ': []}
    for attr in rot_data.keys():
        keyframe_count = cmds.keyframe(f'{joint}.{attr}', query=True, keyframeCount=True)
        if keyframe_count > 0:
            times = cmds.keyframe(f'{joint}.{attr}', query=True, timeChange=True)
            values = cmds.keyframe(f'{joint}.{attr}', query=True, valueChange=True)
            rot_data[attr] = list(zip(times, values))
    
    return trans_data, rot_data

def get_array_from_keyframe_data(keyframe_data, rot_attr):
    min_time = 0
    max_time = 0
    # first_data = np.array([None, None, None])
    for attr_idx, attr in enumerate(rot_attr.keys()):
        data = keyframe_data[attr]
        
        # time 
        if len(data)==0:
            print("no data for", attr)
            continue
        time = int(data[-1][0])
        if max_time < time:
            max_time = time
        if min_time > time:
            min_time = time
    rot_data = np.full((max_time+1-min_time, 3), None, dtype=np.float32)
    
    len_frame = len(rot_data)
    for attr_idx, attr in enumerate(rot_attr.keys()):
        for fid, data_perframe in enumerate(keyframe_data[attr]):
            frame = int(data_perframe[0])
            data = data_perframe[1]
            rot_data[frame, attr_idx] = data
        
        # if first first is nan
        if np.isnan(rot_data[0][attr_idx]):
            len_frame = len(rot_data)
            for i in range(len_frame):
                if np.isnan(rot_data[i][attr_idx])==False:
                    rot_data[0][attr_idx] = rot_data[i][attr_idx]
                    break
        
        # interpolation TODO: 뒤에 값과 함께 interpolation
        for fid in range(len_frame):
            condition = np.isnan(rot_data[fid][attr_idx])
            if condition:
                rot_data[fid][attr_idx] = rot_data[fid-1][attr_idx]

    return rot_data # [frames, attr 3]

def get_delta_rotation(rot_data):
    src_Tpose = rot_data[0]
    delta_data = rot_data - src_Tpose[None, :]
    
    return delta_data # [attr 3, frames]

def set_translate_keyframe(joint, keyframe_data):
    for attr, keyframes in keyframe_data.items():
        # set only translate
        for tid, (time, value) in enumerate(keyframes):
            cmds.setKeyframe(joint, attribute=attr, time=time, value=value)

def set_keyframe(joint, keyframe_data, rot_attr):
    for attr_idx, attr in enumerate(rot_attr.keys()):
        for tid, perframe_data in enumerate(keyframe_data):
            value = float(perframe_data[attr_idx])
            if np.isnan(value):
                continue
            cmds.setKeyframe(joint, attribute=attr, time=tid, value=value) # world 로 가능?
