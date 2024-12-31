source_path = "/Users/jungeunyoo/Documents/Github/maya_retargeting/motions/Asooni_2"
dest_path = "/Users/jungeunyoo/Documents/Github/maya_retargeting/motions/zepeto"

import glob, os
source_character = "/Users/jungeunyoo/Documents/Github/maya_retargeting/motions/Asooni/T-Pose.fbx"
source_motions = glob.glob(os.path.join(source_path, "*.fbx"))
target_character = "character/Zepeto/Zepeto_wNamespace.fbx"
print(source_motions)

import subprocess
for source_motion in source_motions:
    head,tail = os.path.split(source_motion)
    output_path = os.path.join(dest_path, tail)
    if os.path.exists(output_path):
        continue
    print(tail)
    subprocess.run([
        "bash",
        "run.sh",
        source_character,
        source_motion,
        target_character,
        output_path
        ])