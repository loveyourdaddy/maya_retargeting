import maya.cmds as cmds
import maya.standalone
import maya.api.OpenMaya as om
import math
import argparse
from typing import Dict, Tuple

class MotionRetargeter:
    def __init__(self, source_tpose_file, source_motion_file, target_tpose_file):
        self.source_tpose_file = source_tpose_file
        self.source_motion_file = source_motion_file
        self.target_tpose_file = target_tpose_file
        self.joint_mapping = {
            'ACHID:Hips': 'zepeto:hips',
            'ACHID:Spine': 'zepeto:spine',
            'ACHID:Spine1': 'zepeto:chest',
            'ACHID:Spine2': 'zepeto:chestUpper',
            'ACHID:Neck': 'zepeto:neck',
            'ACHID:Head': 'zepeto:head',
            'ACHID:LeftShoulder' : "zepeto:shoulder_L",
            'ACHID:LeftArm' : "zepeto:upperArm_L",
            'ACHID:LeftForeArm' : "zepeto:lowerArm_L",
            'ACHID:RightShoulder' : "zepeto:shoulder_R",
            'ACHID:RightArm' : "zepeto:upperArm_R",
            'ACHID:RightForeArm' : "zepeto:lowerArm_R",
            'ACHID:LeftUpLeg' : "zepeto:upperLeg_L",
            'ACHID:RightUpLeg' : "zepeto:upperReg_R",
            'ACHID:LeftLeg' : "zepeto:lowerLeg_L",
            'ACHID:RightLeg' : "zepeto:lowerReg_R",

        }
        self.source_tpose_rotations = {}
        self.target_tpose_rotations = {}

    def load_and_setup(self):
        # Import source T-pose
        cmds.file(self.source_tpose_file, i=True, namespace="ACHID")
        
        # Store source T-pose rotations
        for source_joint in self.joint_mapping.keys():
            rot = cmds.getAttr(f"{source_joint}.rotate")[0]
            self.source_tpose_rotations[source_joint] = rot

        # Import target T-pose
        cmds.file(self.target_tpose_file, i=True, namespace="zepeto")
        
        # Store target T-pose rotations
        for target_joint in self.joint_mapping.values():
            rot = cmds.getAttr(f"{target_joint}.rotate")[0]
            self.target_tpose_rotations[target_joint] = rot

        # Import source motion
        cmds.file(self.source_motion_file, i=True, namespace="ACHID")

    def convert_rotation_space(self, source_rot, source_joint, target_joint):
    """
    Convert rotation from source joint space to target joint space accounting for different local axis orientations
    """
    # Create rotation matrices for source rotation
    source_matrix = om.MEulerRotation(
        math.radians(source_rot[0]),
        math.radians(source_rot[1]),
        math.radians(source_rot[2]),
        om.MEulerRotation.kXYZ
    ).asMatrix()

    # Get source T-pose pre-rotation
    source_tpose_rot = self.source_tpose_rotations[source_joint]
    source_tpose_matrix = om.MEulerRotation(
        math.radians(source_tpose_rot[0]),
        math.radians(source_tpose_rot[1]),
        math.radians(source_tpose_rot[2]),
        om.MEulerRotation.kXYZ
    ).asMatrix()

    # Get target T-pose pre-rotation
    target_tpose_rot = self.target_tpose_rotations[target_joint]
    target_tpose_matrix = om.MEulerRotation(
        math.radians(target_tpose_rot[0]),
        math.radians(target_tpose_rot[1]),
        math.radians(target_tpose_rot[2]),
        om.MEulerRotation.kXYZ
    ).asMatrix()

    # Get joint orientation matrices
    source_joint_orient = cmds.getAttr(f"{source_joint}.jointOrient")[0]
    target_joint_orient = cmds.getAttr(f"{target_joint}.jointOrient")[0]
    
    source_orient_matrix = om.MEulerRotation(
        math.radians(source_joint_orient[0]),
        math.radians(source_joint_orient[1]),
        math.radians(source_joint_orient[2]),
        om.MEulerRotation.kXYZ
    ).asMatrix()
    
    target_orient_matrix = om.MEulerRotation(
        math.radians(target_joint_orient[0]),
        math.radians(target_joint_orient[1]),
        math.radians(target_joint_orient[2]),
        om.MEulerRotation.kXYZ
    ).asMatrix()

    # Calculate the relative rotation in source joint space
    source_local = source_orient_matrix.inverse() * source_matrix * source_orient_matrix
    source_offset = source_local * source_tpose_matrix.inverse()

    # Transform to target joint space
    target_local = target_orient_matrix * source_offset * target_orient_matrix.inverse()
    final_matrix = target_local * target_tpose_matrix

    # Convert back to euler angles
    final_rotation = om.MEulerRotation.decompose(final_matrix, om.MEulerRotation.kXYZ)
    return [math.degrees(angle) for angle in final_rotation]

    def retarget_motion(self):
        # Get timeline range
        start_time = cmds.playbackOptions(query=True, minTime=True)
        end_time = cmds.playbackOptions(query=True, maxTime=True)

        # Process each frame
        for frame in range(int(start_time), int(end_time) + 1):
            cmds.currentTime(frame)
            
            # Process each joint
            for source_joint, target_joint in self.joint_mapping.items():
                # Get source rotation at current frame
                source_rot = cmds.getAttr(f"{source_joint}.rotate")[0]
                
                # Convert rotation
                target_rot = self.convert_rotation_space(source_rot, source_joint, target_joint)
                
                # Set target rotation
                cmds.setKeyframe(target_joint, attribute='rotateX', value=target_rot[0], time=frame)
                cmds.setKeyframe(target_joint, attribute='rotateY', value=target_rot[1], time=frame)
                cmds.setKeyframe(target_joint, attribute='rotateZ', value=target_rot[2], time=frame)

    def cleanup(self):
        # Delete imported namespaces
        cmds.namespace(setNamespace=':')
        cmds.namespace(removeNamespace='ACHID', force=True)

        cmds.namespace(removeNamespace='zepeto', force=True)

def parse_args():
    parser = argparse.ArgumentParser(description='Motion Retargeting Tool')
    parser.add_argument('--source-tpose', required=True, help='Source character T-pose file')
    parser.add_argument('--source-motion', required=True, help='Source motion file')
    parser.add_argument('--target-tpose', required=True, help='Target character T-pose file')
    parser.add_argument('--output', required=True, help='Output FBX file path')
    parser.add_argument('--save-scene', required=True, help='Save Maya scene path')
    return parser.parse_args()

def main():
    # Initialize Maya Standalone
    maya.standalone.initialize(name='python')
    
    # Parse arguments
    args = parse_args()
    
    # Initialize FBX plugin
    try:
        cmds.loadPlugin('fbxmaya')
        print("FBX plugin loaded successfully")
    except:
        print("Error: Failed to load FBX plugin")
        return
    
    print(f"Source T-pose: {args.source_tpose}")
    print(f"Source Motion: {args.source_motion}")
    print(f"Target T-pose: {args.target_tpose}")
    print(f"Output file: {args.output}")
    
    try:
        # Create retargeter
        retargeter = MotionRetargeter(
            source_tpose_file=args.source_tpose,
            source_motion_file=args.source_motion,
            target_tpose_file=args.target_tpose
        )
        
        # Load and setup
        retargeter.load_and_setup()
        
        # Perform retargeting
        print("Starting retargeting process...")
        retargeter.retarget_motion()
        print("Retargeting completed")
        
        # Select target hierarchy for export
        cmds.select(clear=True)
        cmds.select("zepeto:*", hierarchy=True)
        print("Selected target hierarchy")
        
        # Export FBX
        if cmds.ls(selection=True):
            cmds.file(args.output, force=True, options="v=0;", typ="FBX export", pr=True, es=True)
            print(f"Successfully exported to: {args.output}")
            
            # Save Maya scene
            cmds.file(rename=args.save_scene)
            cmds.file(save=True, type='mayaBinary')
            print(f"Successfully saved Maya scene to: {args.save_scene}")
        else:
            print("Error: No objects selected for export")
            
    except Exception as e:
        print(f"Error during retargeting: {str(e)}")
    finally:
        # Cleanup
        maya.standalone.uninitialize()

if __name__ == "__main__":
    main()