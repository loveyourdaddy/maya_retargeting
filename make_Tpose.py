# mayapy make_Tpose.py --sourceMotion "./motions/Adori/Supershy_wMesh.fbx" --targetChar "./models/Asooni/Asooni.fbx"

import maya.standalone

# 이후 다른 maya 모듈 import
import maya.cmds as cmds
import maya.mel as mel

import math 
import numpy as np

# def add_namespaceInfo_and_add_namespace_for_all_joints(joints, namespace):
#     # rename joints
#     existing_namespaces = cmds.namespaceInfo(listOnlyNamespaces=True)
#     print("현재 존재하는 네임스페이스:", existing_namespaces)
#     if 'src' not in existing_namespaces:
#         print("add src namespace")
#         cmds.namespace(add='src')
    
#     for joint in joints:
#         # 조인트의 짧은 이름만 가져오기 (경로 제외)
#         short_name = joint.split('|')[-1]
        
#         # 이미 네임스페이스가 있는지 확인
#         if ':' in short_name:
#             base_name = short_name.split(':')[-1]
#         else:
#             base_name = short_name
        
#         # 새 이름 생성
#         new_name = f"src:{base_name}"
        
#         # 조인트를 src 네임스페이스로 이동
#         renamed = cmds.rename(joint, new_name)

def make_Tpose():
    # 타임라인 범위를 0 프레임으로 설정
    cmds.currentTime(0)
    cmds.playbackOptions(minTime=0, maxTime=0)

    # BindPose 복원
    mesh_exists = cmds.ls(type="mesh")
    if not mesh_exists:
        raise Exception("씬에 메시가 존재하지 않습니다.")
    
    cmds.select("Hips")
    cmds.dagPose(restore=True, bindPose=True)

    # 0 프레임에 키프레임 설정(현재 포즈를 키프레임으로 저장)
    all_joints = cmds.ls(type="joint")
    all_joints = [joint for joint in all_joints if not joint.startswith("tgt:")]
    for joint in all_joints:
        cmds.setKeyframe(joint, attribute=["rotateX", "rotateY", "rotateZ", "translateX", "translateY", "translateZ"], time=0)

    # 팔 관련 조인트 필터링 TODO: 자동얻기 
    right_arms = ["LeftArm", "LeftForeArm"]
    left_arms = ["RightArm", "RightForeArm"]

    arm_joints = []
    for joint in all_joints:
        if any(keyword in joint for keyword in right_arms) or any(keyword in joint for keyword in left_arms):
            arm_joints.append(joint)

    # 팔 관련 조인트의 회전값을 0으로 설정
    for joint in arm_joints:
        cmds.setAttr(joint + ".rotateX", 0)
        cmds.setAttr(joint + ".rotateY", 0)
        cmds.setAttr(joint + ".rotateZ", 0)
        cmds.setKeyframe(joint, attribute=["rotateX", "rotateY", "rotateZ"], time=0)

    # shoulder IK
    def update_shoulder(joint_name, is_left=True):
        children = cmds.listRelatives(joint_name, children=True, type="joint")
        if not children:
            raise Exception("자식 조인트가 없습니다")

        arm = children[0]

        # 조인트 간 거리 계산
        shoulder_pos = cmds.xform(joint_name, query=True, worldSpace=True, translation=True)
        arm_pos = cmds.xform(arm, query=True, worldSpace=True, translation=True)
        bone_vector = [arm_pos[0] - shoulder_pos[0], 
                    arm_pos[1] - shoulder_pos[1], 
                    arm_pos[2] - shoulder_pos[2]]

        # target pos
        bone_length = math.sqrt(bone_vector[0]**2 + bone_vector[1]**2 + bone_vector[2]**2)
        bone_length = math.sqrt(bone_vector[0]**2 + bone_vector[1]**2 + bone_vector[2]**2)
        is_left = True
        if is_left:
            target_pos = [shoulder_pos[0] + bone_length, shoulder_pos[1], shoulder_pos[2]]
        else:
            target_pos = [shoulder_pos[0] - bone_length, shoulder_pos[1], shoulder_pos[2]]

        # IK
        ik_target = cmds.spaceLocator(name="IK_target")[0]
        cmds.xform(ik_target, worldSpace=True, translation=target_pos)

        parent_worldrot = cmds.xform(joint_name, query=True, matrix=True, worldSpace=True)
        parent_worldrot = np.array(parent_worldrot).reshape(4,4)[:3,:3]

        aimVec = parent_worldrot[:, 0]
        upVec = parent_worldrot[:, 1]
        aimVec = np.round(aimVec, 0) # [0,1,0] 
        upVec = np.round(upVec, 0) # [0,0,-1]
        # print("arm_pos: ", arm_pos)
        # print("ik_target: ",target_pos)
        # print("aimVec: ",aimVec)
        # print("upVec: ",upVec)

        cmds.aimConstraint(ik_target, joint_name, 
                        aimVector= aimVec,
                        upVector = upVec,
                        )
        
        # 프레임 업데이트 강제 실행
        cmds.dgdirty(allPlugs=True)
        cmds.refresh(force=True)
        
        # 회전값 저장
        rotation_values = [
            cmds.getAttr(joint_name + ".rotateX"),
            cmds.getAttr(joint_name + ".rotateY"),
            cmds.getAttr(joint_name + ".rotateZ")
        ]
        
        # 저장했던 회전값 적용
        # import pdb; pdb.set_trace()
        cmds.setAttr(joint_name + ".rotateX", rotation_values[0])
        cmds.setAttr(joint_name + ".rotateY", rotation_values[1])
        cmds.setAttr(joint_name + ".rotateZ", rotation_values[2])
        cmds.setKeyframe(joint_name, attribute=["rotateX", "rotateY", "rotateZ"], time=0)

        # 제약조건 및 locator 삭제
        cmds.delete(ik_target)

    # left: TODO: 자동얻기
    left_shoulder = "LeftShoulder"
    update_shoulder(left_shoulder, is_left=True)
    right_shoulder = "RightShoulder"
    update_shoulder(right_shoulder, is_left=False)

    # set key
    # import pdb; pdb.set_trace()
    for joint in all_joints:
        cmds.setKeyframe(joint, attribute=["rotateX", "rotateY", "rotateZ", "translateX", "translateY", "translateZ"], time=0)

    # remove meshes
    # mesh_transforms = cmds.ls(type='mesh', long=True)
    # transform_nodes = [cmds.listRelatives(mesh, parent=True, fullPath=True)[0] for mesh in mesh_transforms]
    # cmds.delete(transform_nodes)

    # joints = cmds.ls(type='joint')
    # add_namespaceInfo_and_add_namespace_for_all_joints(joints, "src")
    
if __name__=="__main__":
    # Load the FBX plugin
    maya.standalone.initialize(name='python')
    if not cmds.pluginInfo('fbxmaya', query=True, loaded=True):
        cmds.loadPlugin('fbxmaya')
    
    from functions.parser import get_args, get_name
    args = get_args()

    from retargeting_different_axis import *
    import_motion_file(args.sourceMotion)
    make_Tpose()
    
    targetChar = get_name(args.targetChar)
    targetMotion = get_name(args.sourceMotion)
    export(args, targetChar, targetMotion)
