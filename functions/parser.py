import argparse

def get_parser():
    parser = argparse.ArgumentParser(description='Import an FBX file into Maya')
    
    parser.add_argument('--sourceChar', type=str, default="")
    parser.add_argument('--sourceMotion', type=str, default="") # ./motions/Adori/animation/0055_Freestyle002_03_RT0214.fbx
    parser.add_argument('--targetChar', type=str, default="") # ./models/Dancstruct/SKM_ADORI_0229.fbx
    parser.add_argument('--tgt_motion_path', type=str, default="./output/")
    return parser

def get_args():
    parser = get_parser()
    return parser.parse_args()
