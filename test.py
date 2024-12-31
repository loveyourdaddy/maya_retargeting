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
            'ACHID:LeftShoulder': 'zepeto:shoulder_L',
            'ACHID:LeftArm': 'zepeto:upperArm_L',
            'ACHID:LeftForeArm': 'zepeto:lowerArm_L',
            'ACHID:RightShoulder': 'zepeto:shoulder_R',
            'ACHID:RightArm': 'zepeto:upperArm_R',
            'ACHID:RightForeArm': 'zepeto:lowerArm_R',
            'ACHID:LeftUpLeg': 'zepeto:upperLeg_L',
            'ACHID:RightUpLeg': 'zepeto:upperReg_R',  # Fixed typo
            'ACHID:LeftLeg': 'zepeto:lowerLeg_L',
            'ACHID:RightLeg': 'zepeto:lowerReg_R'     # Fixed typo
        }
        self.source_tpose_rotations = {}
        self.target_tpose_rotations = {}
        
        # Define right-side joints
        self.right_upper_joints = {
            'ACHID:RightShoulder', 'ACHID:RightArm', 'ACHID:RightForeArm',
        }

        self.right_lower_joints = {
            'ACHID:RightUpLeg', 'ACHID:RightLeg'
        }

        self.left_upper_joints = {
            'ACHID:LeftShoulder', 'ACHID:LeftArm', 'ACHID:LeftForeArm',
        }

        self.left_lower_joints = {
            'ACHID:LeftUpLeg', 'ACHID:LeftLeg'
        }
        
        # Define spine chain joints
        self.spine_chain = {
            'ACHID:Hips', 'ACHID:Spine', 'ACHID:Spine1', 'ACHID:Spine2',
            'ACHID:Neck', 'ACHID:Head'
        }

    def get_conversion_matrix(self, source_joint):
        """
        Get the appropriate conversion matrix based on joint type
        """
        if source_joint in self.left_upper_joints:
            # For right side: Y-up to -X-up, maintain handedness
            return om.MMatrix([
                [0, 1, 0, 0],  # Y axis becomes X axis
                [0, 0, -1, 0],   # Z axis becomes -Y axis
                [-1, 0, 0, 0],  # X axis becomes -Z axis
                [0, 0, 0, 1]
            ])
        elif source_joint in self.right_upper_joints:
            # For right side: Y-up to -X-up, maintain handedness
            return om.MMatrix([
                [0, -1, 0, 0],  # Y axis becomes -X axis
                [0, 0, 1, 0],   # Z axis becomes Y axis
                [-1, 0, 0, 0],  # X axis becomes -Z axis
                [0, 0, 0, 1]
            ])
        elif source_joint in self.left_lower_joints:
            # For right side: Y-up to -X-up, maintain handedness
            return om.MMatrix([
                [0, 1, 0, 0],  # Y axis becomes X axis
                [-1, 0, 0, 0],   # X axis becomes -Y axis
                [0, 0, 1, 0],  # Z axis becomes Z axis
                [0, 0, 0, 1]
            ])
        elif source_joint in self.right_lower_joints:
            # For right side: Y-up to -X-up, maintain handedness
            return om.MMatrix([
                [0, -1, 0, 0],  # Y axis becomes -X axis
                [-1, 0, 0, 0],   # X axis becomes Y axis
                [0, 0, -1, 0],  # Z axis becomes -Z axis
                [0, 0, 0, 1]
            ])
        else:
            # For spine chain and left side: Y-up to X-up
            return om.MMatrix([
                [0, 1, 0, 0],   # Y axis becomes X axis
                [-1, 0, 0, 0],  # X axis becomes -Y axis
                [0, 0, 1, 0],   # Z axis remains Z axis
                [0, 0, 0, 1]
            ])

    def convert_rotation_space(self, source_rot, source_joint, target_joint):
        """
        Convert rotation from source coordinate system to target coordinate system
        """
        # Create rotation matrices
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

        # Get appropriate conversion matrix
        conversion_matrix = self.get_conversion_matrix(source_joint)

        # Calculate final rotation
        source_offset = source_matrix * source_tpose_matrix.inverse()
        converted_offset = conversion_matrix * source_offset * conversion_matrix.inverse()
        final_matrix = converted_offset * target_tpose_matrix

        # Convert back to euler angles
        final_rotation = om.MEulerRotation.decompose(final_matrix, om.MEulerRotation.kXYZ)
        return [math.degrees(angle) for angle in final_rotation]

    def get_source_animation_range(self):
        """Get the actual animation range from the source joints"""
        all_keyframes = []
        for source_joint in self.joint_mapping.keys():
            # Get keyframes for all rotation attributes
            for attr in ['rotateX', 'rotateY', 'rotateZ']:
                keyframes = cmds.keyframe(f"{source_joint}.{attr}", query=True, timeChange=True)
                if keyframes:
                    all_keyframes.extend(keyframes)
        
        if all_keyframes:
            return min(all_keyframes), max(all_keyframes)
        else:
            # Fallback to timeline if no keyframes found
            return (cmds.playbackOptions(query=True, minTime=True),
                   cmds.playbackOptions(query=True, maxTime=True))

    def get_source_animation_range(self):
        """Get the actual animation range from the source joints"""
        all_keyframes = []
        for source_joint in self.joint_mapping.keys():
            # Get keyframes for all rotation attributes
            for attr in ['rotateX', 'rotateY', 'rotateZ']:
                keyframes = cmds.keyframe(f"{source_joint}.{attr}", query=True, timeChange=True)
                if keyframes:
                    all_keyframes.extend(keyframes)
        
        if all_keyframes:
            return min(all_keyframes), max(all_keyframes)
        else:
            # Fallback to timeline if no keyframes found
            return (cmds.playbackOptions(query=True, minTime=True),
                   cmds.playbackOptions(query=True, maxTime=True))

    def load_and_setup(self):
        # Clear the scene first
        cmds.file(new=True, force=True)
        
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

    def retarget_motion(self):
        # Get actual animation range from source
        start_time, end_time = self.get_source_animation_range()
        print(f"Retargeting frames from {start_time} to {end_time}")

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

        # Set timeline to match the animation range
        cmds.playbackOptions(minTime=start_time, maxTime=end_time)

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