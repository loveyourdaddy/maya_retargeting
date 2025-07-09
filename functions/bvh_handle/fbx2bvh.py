""" 이게 뭐가 문제였지? """
import numpy as np
import math
from typing import List, Dict, Tuple, Optional
import struct
import os
import fbx

class BVHJoint:
    def __init__(self, name: str, parent=None):
        self.name = name
        self.parent = parent
        self.children = []
        self.offset = [0.0, 0.0, 0.0]  # Local position offset
        self.channels = []  # Animation channels (e.g., Xrotation, Yrotation, etc.)
        self.is_end_site = False
        
        if parent:
            parent.children.append(self)

class BVHData:
    def __init__(self):
        self.root = None
        self.joints = []
        self.frame_time = 1.0/30.0  # Default 30 FPS
        self.frames = []  # Animation data
        self.joint_index = {}  # Joint name to index mapping
        
    def add_joint(self, joint: BVHJoint):
        self.joints.append(joint)
        self.joint_index[joint.name] = len(self.joints) - 1

class FBXToBVHConverter:
    def __init__(self):
        self.bvh_data = BVHData()
        self.joint_mapping = {}
        
    def euler_from_quaternion(self, x, y, z, w):
        """Convert quaternion to euler angles (in degrees)"""
        # Roll (x-axis rotation)
        sinr_cosp = 2 * (w * x + y * z)
        cosr_cosp = 1 - 2 * (x * x + y * y)
        roll = math.atan2(sinr_cosp, cosr_cosp)
        
        # Pitch (y-axis rotation)
        sinp = 2 * (w * y - z * x)
        if abs(sinp) >= 1:
            pitch = math.copysign(math.pi / 2, sinp)
        else:
            pitch = math.asin(sinp)
            
        # Yaw (z-axis rotation)
        siny_cosp = 2 * (w * z + x * y)
        cosy_cosp = 1 - 2 * (y * y + z * z)
        yaw = math.atan2(siny_cosp, cosy_cosp)
        
        return [math.degrees(roll), math.degrees(pitch), math.degrees(yaw)]
    
    def matrix_to_euler(self, matrix):
        """Convert rotation matrix to euler angles (in degrees)"""
        sy = math.sqrt(matrix[0][0] * matrix[0][0] + matrix[1][0] * matrix[1][0])
        
        singular = sy < 1e-6
        
        if not singular:
            x = math.atan2(matrix[2][1], matrix[2][2])
            y = math.atan2(-matrix[2][0], sy)
            z = math.atan2(matrix[1][0], matrix[0][0])
        else:
            x = math.atan2(-matrix[1][2], matrix[1][1])
            y = math.atan2(-matrix[2][0], sy)
            z = 0
            
        return [math.degrees(x), math.degrees(y), math.degrees(z)]

    def convert_fbx_to_bvh_sdk(self, fbx_file_path: str, bvh_file_path: str):
        """Convert FBX to BVH using FBX SDK"""

        # Initialize FBX SDK
        manager = fbx.FbxManager.Create()
        scene = fbx.FbxScene.Create(manager, "")
        
        # Import FBX file
        importer = fbx.FbxImporter.Create(manager, "")
        if not importer.Initialize(fbx_file_path, -1, manager.GetIOSettings()):
            print(f"Failed to initialize importer: {importer.GetStatus().GetErrorString()}")
            return False
            
        importer.Import(scene)
        importer.Destroy()
        
        # Get root node
        root_node = scene.GetRootNode()
        
        # Find skeleton root
        skeleton_root = self.find_skeleton_root(root_node)
        if not skeleton_root:
            print("No skeleton found in FBX file")
            return False
            
        # Build BVH hierarchy
        self.build_bvh_hierarchy(skeleton_root, None)
        
        # Extract animation data
        self.extract_animation_data(scene)
        
        # Write BVH file
        self.write_bvh_file(bvh_file_path)
        
        manager.Destroy()
        return True
    
    def find_skeleton_root(self, node):
        """Find the root of the skeleton hierarchy"""
        if node.GetNodeAttribute():
            attribute_type = node.GetNodeAttribute().GetAttributeType()
            if attribute_type == fbx.FbxNodeAttribute.eSkeleton:
                return node
                
        for i in range(node.GetChildCount()):
            child_root = self.find_skeleton_root(node.GetChild(i))
            if child_root:
                return child_root
        return None
    
    def build_bvh_hierarchy(self, fbx_node, parent_joint):
        """Build BVH joint hierarchy from FBX nodes"""
        joint_name = fbx_node.GetName()
        
        # Create BVH joint
        bvh_joint = BVHJoint(joint_name, parent_joint)
        
        # Get local transform
        translation = fbx_node.LclTranslation.Get()
        bvh_joint.offset = [translation[0], translation[1], translation[2]]
        
        # Set up channels (BVH standard order)
        if parent_joint is None:  # Root joint
            # bvh_joint.channels = ["Xposition", "Yposition", "Zposition", 
            #                     "Zrotation", "Xrotation", "Yrotation"]
            bvh_joint.channels = ["Xposition", "Yposition", "Zposition", 
                                "Xrotation", "Yrotation", "Zrotation"]
        else:
            # bvh_joint.channels = ["Zrotation", "Xrotation", "Yrotation"]
            bvh_joint.channels = ["Xrotation", "Yrotation", "Zrotation"]
        
        self.bvh_data.add_joint(bvh_joint)
        self.joint_mapping[fbx_node] = bvh_joint
        
        if parent_joint is None:
            self.bvh_data.root = bvh_joint
        
        # Process children
        child_count = fbx_node.GetChildCount()
        has_skeleton_children = False
        
        for i in range(child_count):
            child = fbx_node.GetChild(i)
            if (child.GetNodeAttribute() and 
                child.GetNodeAttribute().GetAttributeType() == fbx.FbxNodeAttribute.eSkeleton):
                has_skeleton_children = True
                self.build_bvh_hierarchy(child, bvh_joint)
        
        # Add end site if no skeleton children
        if not has_skeleton_children and child_count == 0:
            end_site = BVHJoint("End Site", bvh_joint)
            end_site.is_end_site = True
            end_site.offset = [0.0, 5.0, 0.0]  # Default end site offset
            self.bvh_data.add_joint(end_site)
    
    def extract_animation_data(self, scene):
        """Extract animation data from FBX scene"""
        # Get animation stack
        anim_stack_count = scene.GetSrcObjectCount(fbx.FbxAnimStack.ClassId)
        if anim_stack_count == 0:
            print("No animation found")
            return
            
        anim_stack = scene.GetSrcObject(fbx.FbxAnimStack.ClassId, 0)
        scene.SetCurrentAnimationStack(anim_stack)
        
        # Get time span
        time_span = anim_stack.GetLocalTimeSpan()
        start_time = time_span.GetStart()
        end_time = time_span.GetStop()
        
        # Frame rate
        time_mode = fbx.FbxTime.eFrames30
        self.bvh_data.frame_time = 1.0 / 30.0
        
        # Extract frames
        current_time = start_time
        while current_time <= end_time:
            frame_data = []
            
            for joint in self.bvh_data.joints:
                if joint.is_end_site:
                    continue
                    
                # Find corresponding FBX node
                fbx_node = None
                for node, bvh_joint in self.joint_mapping.items():
                    if bvh_joint == joint:
                        fbx_node = node
                        break
                
                if fbx_node:
                    # Get transform at current time
                    global_transform = fbx_node.EvaluateGlobalTransform(current_time)
                    local_transform = fbx_node.EvaluateLocalTransform(current_time)
                    
                    translation = local_transform.GetT()
                    rotation = local_transform.GetR()
                    
                    # Add data based on channels
                    for channel in joint.channels:
                        if "position" in channel.lower():
                            if "X" in channel:
                                frame_data.append(translation[0])
                            elif "Y" in channel:
                                frame_data.append(translation[1])
                            elif "Z" in channel:
                                frame_data.append(translation[2])
                        elif "rotation" in channel.lower():
                            if "X" in channel:
                                frame_data.append(rotation[0])
                            elif "Y" in channel:
                                frame_data.append(rotation[1])
                            elif "Z" in channel:
                                frame_data.append(rotation[2])
            
            self.bvh_data.frames.append(frame_data)
            current_time += fbx.FbxTime.SetTime(0, 0, 0, 1, 0, time_mode)
    
    def write_bvh_file(self, file_path: str):
        """Write BVH data to file"""
        with open(file_path, 'w') as f:
            f.write("HIERARCHY\n")
            self.write_joint(f, self.bvh_data.root, 0)
            
            f.write("MOTION\n")
            f.write(f"Frames: {len(self.bvh_data.frames)}\n")
            f.write(f"Frame Time: {self.bvh_data.frame_time:.6f}\n")
            
            for frame in self.bvh_data.frames:
                f.write(" ".join(f"{val:.6f}" for val in frame) + "\n")
    
    def write_joint(self, f, joint: BVHJoint, indent_level: int):
        """Write joint hierarchy to BVH file"""
        indent = "\t" * indent_level
        
        if joint.is_end_site:
            f.write(f"{indent}End Site\n")
            f.write(f"{indent}{{\n")
            f.write(f"{indent}\tOFFSET {joint.offset[0]:.6f} {joint.offset[1]:.6f} {joint.offset[2]:.6f}\n")
            f.write(f"{indent}}}\n")
        else:
            joint_type = "ROOT" if joint.parent is None else "JOINT"
            f.write(f"{indent}{joint_type} {joint.name}\n")
            f.write(f"{indent}{{\n")
            f.write(f"{indent}\tOFFSET {joint.offset[0]:.6f} {joint.offset[1]:.6f} {joint.offset[2]:.6f}\n")
            
            if joint.channels:
                f.write(f"{indent}\tCHANNELS {len(joint.channels)} {' '.join(joint.channels)}\n")
            
            for child in joint.children:
                self.write_joint(f, child, indent_level + 1)
            
            f.write(f"{indent}}}\n")


# Alternative method using bvhtoolbox or similar libraries
class SimpleFBXToBVHConverter:
    """Simplified converter that works with parsed FBX data"""
    def __init__(self):
        self.joints = []
        self.animation_data = []
        self.frame_time = 1.0/30.0
    
    def convert_from_data(self, joint_hierarchy: Dict, animation_frames: List, output_path: str):
        """
        Convert from pre-parsed FBX data to BVH
        
        Args:
            joint_hierarchy: Dictionary containing joint hierarchy
            animation_frames: List of animation frame data
            output_path: Output BVH file path
        """
        self.build_hierarchy_from_dict(joint_hierarchy)
        self.animation_data = animation_frames
        self.write_bvh(output_path)
    
    def build_hierarchy_from_dict(self, hierarchy: Dict, parent=None):
        """Build joint hierarchy from dictionary"""
        name = hierarchy.get('name', 'Joint')
        offset = hierarchy.get('offset', [0, 0, 0])
        channels = hierarchy.get('channels', ['Zrotation', 'Xrotation', 'Yrotation'])
        
        joint = {
            'name': name,
            'parent': parent,
            'offset': offset,
            'channels': channels,
            'children': []
        }
        
        if parent:
            parent['children'].append(joint)
        else:
            self.root = joint
        
        for child_dict in hierarchy.get('children', []):
            self.build_hierarchy_from_dict(child_dict, joint)
    
    def write_bvh(self, file_path: str):
        """Write BVH file"""
        with open(file_path, 'w') as f:
            f.write("HIERARCHY\n")
            self.write_joint_recursive(f, self.root, 0)
            
            f.write("MOTION\n")
            f.write(f"Frames: {len(self.animation_data)}\n")
            f.write(f"Frame Time: {self.frame_time:.6f}\n")
            
            for frame in self.animation_data:
                f.write(" ".join(f"{val:.6f}" for val in frame) + "\n")
    
    def write_joint_recursive(self, f, joint: Dict, indent: int):
        """Recursively write joint hierarchy"""
        tab = "\t" * indent
        
        if joint['name'] == 'End Site':
            f.write(f"{tab}End Site\n")
            f.write(f"{tab}{{\n")
            offset = joint['offset']
            f.write(f"{tab}\tOFFSET {offset[0]:.6f} {offset[1]:.6f} {offset[2]:.6f}\n")
            f.write(f"{tab}}}\n")
        else:
            joint_type = "ROOT" if joint['parent'] is None else "JOINT"
            f.write(f"{tab}{joint_type} {joint['name']}\n")
            f.write(f"{tab}{{\n")
            
            offset = joint['offset']
            f.write(f"{tab}\tOFFSET {offset[0]:.6f} {offset[1]:.6f} {offset[2]:.6f}\n")
            
            if joint['channels']:
                channels_str = ' '.join(joint['channels'])
                f.write(f"{tab}\tCHANNELS {len(joint['channels'])} {channels_str}\n")
            
            for child in joint['children']:
                self.write_joint_recursive(f, child, indent + 1)
            
            f.write(f"{tab}}}\n")


# Usage examples
def main():
    """Example usage of the FBX to BVH converter"""
    # input_fbx  = "./motions/Adori/SuperShy.fbx"
    # output_bvh = "./motions/Adori/SuperShy.bvh"
    name = "./motions/SMPL/Supershy"
    input_fbx  = name + ".fbx" 
    output_bvh = name + ".bvh" 

    # Method 1: Using FBX SDK (if available)
    converter = FBXToBVHConverter()
    success = converter.convert_fbx_to_bvh_sdk(input_fbx, output_bvh)

    if success:
        print("FBX successfully converted to BVH using FBX SDK")
    else:
        print("Failed to convert FBX to BVH")
    
    # # Method 2: Using pre-parsed data
    # simple_converter = SimpleFBXToBVHConverter()
    
    # # Example animation data (one frame)
    # sample_animation = [
    #     [0, 0, 0, 0, 0, 0, 0, 0, 0]  # Position and rotation values for all channels
    # ]
    
    # simple_converter.convert_from_data(sample_hierarchy, sample_animation, "sample_output.bvh")
    # print("Sample BVH file created")


if __name__ == "__main__":
    main()