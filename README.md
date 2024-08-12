# Code
* 0_utils

  -- Necessary libraries to Run other codes

  -- Needs Mayapy. (Maya installlation is essential)

* 1_Getting_skinning_weights

  -- Needs Mayapy

  -- Input : .fbx (T-pose file) file address

* 2_Target_maker
  
  -- Making labels for each mesh points
  
  -- Input : T-pose file's changed numpy array.

* 3_Tpose_fbx_to_numpy

  -- Change Tpose fbx file into numpy files

  -- Input : .fbx (T-pose file) file address

* 4_testing.ipynb

  -- Learning process of PointNet

  -- Trained model "Ybotbased_pointnet_model.pth" is PointNet adjusted model that changed into fitted on Ybot.fbx charactor T-pose file.
