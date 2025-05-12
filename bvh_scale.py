def scale_bvh_root_translation(input_file, output_file, scale_factor=0.01):
    """
    Scale the root translation values in a BVH file by a given factor.
    
    Args:
        input_file (str): Path to the input BVH file
        output_file (str): Path to the output BVH file
        scale_factor (float): Factor to scale the root translation values (default: 0.01 for 1/100)
    """
    # Read the input BVH file
    with open(input_file, 'r') as f:
        lines = f.readlines()
    
    # Find where the MOTION section starts
    motion_index = -1
    frames_index = -1
    for i, line in enumerate(lines):
        if line.strip() == 'MOTION':
            motion_index = i
        if motion_index != -1 and line.strip().startswith('Frames:'):
            frames_index = i + 2  # +2 to skip the 'Frames:' and 'Frame Time:' lines
            break
    
    if motion_index == -1 or frames_index == -1:
        raise ValueError("Could not find MOTION section in the BVH file")
    
    # Process each frame's data
    for i in range(frames_index, len(lines)):
        if not lines[i].strip():  # Skip empty lines
            continue
        
        data = lines[i].split()
        # Scale the first 3 values (root translation)
        data[0] = str(float(data[0]) * scale_factor)
        data[1] = str(float(data[1]) * scale_factor)
        data[2] = str(float(data[2]) * scale_factor)
        
        # Reconstruct the line
        lines[i] = ' '.join(data) + '\n'
    
    # Write the modified BVH to the output file
    with open(output_file, 'w') as f:
        f.writelines(lines)
    
    print(f"Successfully scaled root translation in {input_file} by {scale_factor} and saved to {output_file}")

# Example usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python scale_bvh.py input_file output_file [scale_factor]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    if len(sys.argv) > 3:
        scale_factor = float(sys.argv[3])
    else:
        scale_factor = 0.01  # Default to 1/100
    
    scale_bvh_root_translation(input_file, output_file, scale_factor)