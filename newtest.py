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

def normalize_point_cube(points):
    centroid = np.mean(points, axis=0)
    points -= centroid
    min_vals = np.min(points, axis=0)
    max_vals = np.max(points, axis=0)
    scale = np.max(max_vals - min_vals) / 2.0
    points /= scale
    return points

def normalize_point_sphere(points):
	centroid = np.mean(points, axis=0)
	points -= centroid
	furthest_distance = np.max(np.sqrt(np.sum(abs(points)**2,axis=-1)))
	points /= furthest_distance
	return points

dims = 3  # Always fixed
Char_name = "Asooni"

meshdata = np.load("./TruelyTruelyUsing/" + Char_name + "_mesh.fbx.npy")
jointdata = np.load("./TruelyTruelyUsing/" + Char_name + "_joint.fbx.npy")

NN_out_size = len(jointdata)
pointnet = PointNetClassifier(1,dims, NN_out_size)

meshdata = normalize_point_cube(meshdata).reshape(-1, 3, 1)
meshdata = torch.tensor(meshdata, dtype=torch.float32)
meshdata = meshdata[:1300]

global_feature, global_feature_maxpooled, local_embedding, T2, outcome = pointnet(meshdata)





loss = nn.CrossEntropyLoss()
regularization = nn.MSELoss()
optimizer = torch.optim.Adam(pointnet.parameters(), lr = 0.001)

print(outcome.shape)



'''
# model_path = './PointNet_Pytorch/classifier_model_state.pth'

local_points = normalize_point_sphere(np.load(f"./Dataset/{Char_name}.npy")[0].reshape(-1, 3))
local_points = local_points.reshape(-1,3,1)
#local_points = np.load(f"./Dataset/{Char_name}.npy")[0].reshape(-1, 3, 1)

#print(local_points.shape)
local_points = local_points[:1200]

#print(local_points.shape)
# Save Global Features
Data = torch.tensor(local_points, dtype=torch.float32)

#pointnet = PointNetClassifier(1, dims).eval()
pointnet = PointNetClassifier(1, dims)
#pointnet.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
global_feature, global_feature_maxpooled, local_embedding, T2 = pointnet(Data)
global_feature = global_feature.detach().numpy()
'''
'''
print(local_points.shape)
print(global_feature.shape)
print(local_embedding.shape)
'''