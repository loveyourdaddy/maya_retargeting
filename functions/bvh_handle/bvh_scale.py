"""
python functions/bvh_handle/bvh_scale.py
"""

def scale_and_resample_bvh(input_file, output_file, skel_scale=0.01, pos_scale=0.01, target_fps=None, resample=False):
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
    # frames
    frame_time_index = -1
    num_frames = 0
    frame_time = 0

    for i, line in enumerate(lines):
        if line.strip() == 'HIERARCHY':
            hierarchy_index = i
        elif line.strip() == 'MOTION':
            motion_index = i
        elif motion_index != -1 and line.strip().startswith('Frames:'):
            frames_line = line.strip()
            num_frames = int(frames_line.split(':')[1].strip())
            frames_index = i + 2  # +2 to skip the 'Frames:' and 'Frame Time:' lines
            frame_time_index = i + 1
        elif motion_index != -1 and line.strip().startswith('Frame Time:'):
            frame_time = float(line.strip().split(':')[1].strip())
    
    
    if hierarchy_index == -1 or motion_index == -1 or frames_index == -1:
        raise ValueError("Could not find HIERARCHY or MOTION section in the BVH file")
    
    if frame_time > 0:
        source_fps = 1.0 / frame_time
    
    # Process the HIERARCHY section to scale joint offsets
    for i in range(hierarchy_index, motion_index):
        line = lines[i]
        line_stripped = line.strip()
        if line_stripped.startswith('OFFSET'):
            # Preserve the indentation
            indent = line[:line.find('OFFSET')]
            parts = line_stripped.split()
            if len(parts) == 4:  # OFFSET x y z
                # Scale skeleton 
                scaled_x = float(parts[1]) * skel_scale
                scaled_y = float(parts[2]) * skel_scale
                scaled_z = float(parts[3]) * skel_scale
                lines[i] = f"{indent}OFFSET {scaled_x} {scaled_y} {scaled_z}\n"
    
    # Process each frame's data
    motion_frames = []
    for i in range(frames_index, len(lines)):
        if not lines[i].strip():  # Skip empty lines
            continue
        
        # Preserve any indentation that might exist
        indent = lines[i][:len(lines[i]) - len(lines[i].lstrip())]
        data = lines[i].strip().split()
        if not data:  # Skip empty lines that might have been split
            continue

        # Scale root: the first 3 values (root translation)
        data[0] = str(float(data[0]) * pos_scale)
        data[1] = str(float(data[1]) * pos_scale)
        data[2] = str(float(data[2]) * pos_scale)
        
        # Update the original line with scaled data for consistency
        lines[i] = indent + " ".join(data) + "\n"
        
        # Store the frame with original indentation
        motion_frames.append((indent, data))
    

    # Resample frames if target_fps is provided
    if resample:
        if target_fps is not None and source_fps is not None and target_fps != source_fps:
            # Calculate frame sampling interval
            sample_interval = source_fps / target_fps
            resampled_frames = []
            
            for i in range(int(len(motion_frames) / sample_interval) + 1):
                frame_index = int(i * sample_interval)
                if frame_index < len(motion_frames):
                    resampled_frames.append(motion_frames[frame_index])
            
            # Update the number of frames and frame time in the file
            new_num_frames = len(resampled_frames)
            new_frame_time = 1.0 / target_fps
            
            frames_line_indent = lines[frame_time_index - 1][:len(lines[frame_time_index - 1]) - len(lines[frame_time_index - 1].lstrip())]
            frame_time_indent = lines[frame_time_index][:len(lines[frame_time_index]) - len(lines[frame_time_index].lstrip())]
            
            lines[frame_time_index - 1] = f"{frames_line_indent}Frames: {new_num_frames}\n"
            lines[frame_time_index] = f"{frame_time_indent}Frame Time: {new_frame_time}\n"
    else:
        resampled_frames = motion_frames
    
    # Create new file content
    new_lines = lines[:frames_index]
    for indent, data in resampled_frames:
        new_lines.append(indent + " ".join(data) + "\n")

    # Write the modified BVH to the output file
    with open(output_file, 'w') as f:
        f.writelines(new_lines)
    
    print(f"Successfully scaled root translation in {input_file} by {pos_scale} and saved to {output_file}")

# Example usage
if __name__ == "__main__":
    import os
    import glob
    
    input_folder  = "./motions/Asooni/250630_sticky"
    output_folder = "./motions/Asooni/250630_sticky"
    skel_scale = 0.01
    pos_scale = 0.01
    target_fps = 24

    os.makedirs(output_folder, exist_ok=True)
    
    # Find all BVH files in the input folder
    bvh_files = glob.glob(os.path.join(input_folder, "*.bvh"))

    for input_file in bvh_files:
        # input_file = os.path.join(input_folder, "IAM.bvh")
        filename = os.path.basename(input_file)
        base, ext = os.path.splitext(filename)
        output_file = os.path.join(output_folder, f"{base}_{ext}") # {target_fps}fps
        
        print(f"Processing {filename}...")
        scale_and_resample_bvh(
            input_file, 
            output_file, 
            skel_scale, 
            pos_scale, 
            target_fps=None, 
            resample=False
        )

    print("All files processed successfully!")