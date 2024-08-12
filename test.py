import torch
import torch.nn as nn
import numpy as np
from torch.utils.data import DataLoader
import os
from PointNet_Pytorch.dataloader import ModelNet40
from PointNet_Pytorch.models.pointnet_classifier import PointNetClassifier
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import random
from tqdm import tqdm

def normalize_pc(points):
	centroid = np.mean(points, axis=0)
	points -= centroid
	furthest_distance = np.max(np.sqrt(np.sum(abs(points)**2,axis=-1)))
	points /= furthest_distance
	return points



dims = 3  # Always fixed
Char_name = "Adori"
model_path = './PointNet_Pytorch/classifier_model_state.pth'
local_points = normalize_pc(np.load(f"./Dataset/{Char_name}.npy")[0].reshape(-1, 3))
local_points = local_points.reshape(-1,3,1)




#local_points = np.load(f"./Dataset/{Char_name}.npy")[0].reshape(-1, 3, 1)

# Save Global Features 
#'''
Data = torch.tensor(local_points, dtype=torch.float32)

pointnet = PointNetClassifier(1, dims).eval()
pointnet.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
global_feature, global_feature_maxpooled = pointnet(Data)
global_feature = global_feature.detach().numpy()

np.save(f"./Dataset/{Char_name}_feature_normalized.npy",global_feature)
#'''

# Call critical points and critical global features
'''
cs_idx = np.argmax(global_feature, axis=0)
cs_idx = np.unique(cs_idx)

critical_points = local_points[cs_idx].reshape(-1, 3)
critical_global_feature = global_feature[cs_idx].reshape(-1, 1024)
#'''

# Save the per-point function values
global_features = np.load(f"./Dataset/{Char_name}_feature_normalized.npy").reshape(-1,1024)
local_points = local_points.reshape(-1, 3)

local_points = normalize_pc(local_points)

def unit_cube_adjacant_idx(datapoints, point, radius=1):
    indices = np.where((np.abs(datapoints - point) < radius).all(axis=1))[0]
    return indices

def point_functions(feature_points, point, feasible_indices, radius = 1) :
    check_points = feature_points[feasible_indices]
    val = len(np.where(np.sqrt(np.sum((check_points - point)**2,axis=1)) < radius)) / len(check_points)
    return val

vals = []

L = len(global_features)

for idx in tqdm(range(L)) :
    vals.append(point_functions(global_features, global_features[idx], unit_cube_adjacant_idx(local_points, local_points[idx])))

np.save(f"./Dataset/{Char_name}_weight_normalized.npy", np.array(vals))