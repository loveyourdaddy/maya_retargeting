"""
python bvh_scale.py ./motions/SMPL/IAM.bvh ./motions/SMPL/IAM_scaled.bvh 0.01
python bvh_scale.py ./motions/SMPL/120fps/IAM.bvh ./motions/SMPL/IAM_scaled.bvh --target_fps 24
"""

def scale_bvh_root_translation(input_file, output_file, skel_scale=0.01, pos_scale=0.01):
    """
    Scale the root translation values in a BVH file by a given factor.
    
    Args:
        input_file (str): Path to the input BVH file
        output_file (str): Path to the output BVH file
        pos_scale (float): Factor to scale the root translation values (default: 0.01 for 1/100)
    """
    # Read the input BVH file
    with open(input_file, 'r') as f:
        lines = f.readlines()

    # Find where the HIERARCHY and MOTION sections start
    hierarchy_index = -1
    motion_index = -1
    frames_index = -1
    
    for i, line in enumerate(lines):
        if line.strip() == 'HIERARCHY':
            hierarchy_index = i
        elif line.strip() == 'MOTION':
            motion_index = i
        if motion_index != -1 and line.strip().startswith('Frames:'):
            frames_index = i + 2  # +2 to skip the 'Frames:' and 'Frame Time:' lines
            break
    
    if hierarchy_index == -1 or motion_index == -1 or frames_index == -1:
        raise ValueError("Could not find HIERARCHY or MOTION section in the BVH file")
    
    # Process the HIERARCHY section to scale joint offsets
    for i in range(hierarchy_index, motion_index):
        line = lines[i]
        line_stripped = line.strip()
        if line_stripped.startswith('OFFSET'):
            # Preserve the indentation
            indent = line[:line.find('OFFSET')]
            parts = line_stripped.split()
            if len(parts) == 4:  # OFFSET x y z
                scaled_x = float(parts[1]) * skel_scale
                scaled_y = float(parts[2]) * skel_scale
                scaled_z = float(parts[3]) * skel_scale
                lines[i] = f"{indent}OFFSET {scaled_x} {scaled_y} {scaled_z}\n"
    
    # Process each frame's data
    for i in range(frames_index, len(lines)):
        if not lines[i].strip():  # Skip empty lines
            continue
        
        data = lines[i].split()
        # Scale the first 3 values (root translation)
        data[0] = str(float(data[0]) * pos_scale)
        data[1] = str(float(data[1]) * pos_scale)
        data[2] = str(float(data[2]) * pos_scale)
        
        # Reconstruct the line
        lines[i] = ' '.join(data) + '\n'
    
    # Write the modified BVH to the output file
    with open(output_file, 'w') as f:
        f.writelines(lines)
    
    print(f"Successfully scaled root translation in {input_file} by {pos_scale} and saved to {output_file}")

# Example usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python scale_bvh.py input_file output_file [skeleton scale] [position scale]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    if len(sys.argv) > 3:
        skeleton_scale = float(sys.argv[3])
        position_scale = float(sys.argv[4])
    else:
        skeleton_scale = 0.01
        position_scale = 0.01
        
    
    scale_bvh_root_translation(input_file, output_file, skeleton_scale, position_scale)