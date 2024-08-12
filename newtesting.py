import torch
import torch.nn as nn
import numpy as np
from torch.utils.data import DataLoader, Dataset
import matplotlib.pyplot as plt
from PointNet_Pytorch.models.pointnet_classifier import PointNetClassifier
from tqdm import tqdm

# Custom Dataset for handling mesh data and labels
class MeshDataset(Dataset):
    def __init__(self, meshdata, labels, transform=None):
        self.meshdata = meshdata
        self.labels = labels
        self.transform = transform

    def __len__(self):
        return len(self.meshdata)

    def __getitem__(self, idx):
        sample = self.meshdata[idx]
        label = self.labels[idx]
        if self.transform:
            sample = self.transform(sample)
        return sample, label

# Normalization functions (assuming 3D data)
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
    furthest_distance = np.max(np.sqrt(np.sum(abs(points)**2, axis=-1)))
    points /= furthest_distance
    return points

# Load and normalize data
Char_name = "Asooni"

meshdata = np.load("./TruelyTruelyUsing/" + Char_name + "_mesh.fbx.npy")
jointdata = np.load("./TruelyTruelyUsing/" + Char_name + "_joint.fbx.npy")

# Data normalization and reshaping
meshdata = normalize_point_cube(meshdata).reshape(-1, 3, 1)
meshdata = torch.tensor(meshdata, dtype=torch.float32)

target_data = np.load("./TruelyTruelyUsing/" + Char_name + "_target.npy")
labels = np.argmax(target_data, axis=1)
labels = torch.tensor(labels)

# Create Dataset and DataLoader
dataset = MeshDataset(meshdata, labels)
train_size = int(0.8 * len(dataset))
val_size = len(dataset) - train_size
train_dataset, val_dataset = torch.utils.data.random_split(dataset, [train_size, val_size])

Batch_size = 1000

train_loader = DataLoader(train_dataset, batch_size=Batch_size, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=Batch_size, shuffle=False)

# Model, loss function, and optimizer
NN_out_size = len(jointdata)
pointnet = PointNetClassifier(1, 3, NN_out_size)
loss_fn = nn.CrossEntropyLoss()
regularization = nn.MSELoss()
optimizer = torch.optim.Adam(pointnet.parameters(), lr=0.03)
identity = torch.eye(64).float()

# For learning curve
train_losses = []
val_losses = []
accuracies = []

# Training loop
num_epochs = 1
for epoch in range(num_epochs):
    pointnet.train()
    total_train_loss = 0
    for batch_mesh, batch_labels in tqdm(train_loader):
        optimizer.zero_grad()

        global_feature, global_feature_maxpooled, local_embedding, T2, outcome = pointnet(batch_mesh)
        
        # Compute loss
        classification_loss = loss_fn(outcome, batch_labels)
        reg_loss = 0.01 * regularization(torch.bmm(T2, T2.permute(0, 2, 1)), identity.expand(T2.shape[0], -1, -1))
        loss = classification_loss + reg_loss

        loss.backward()
        optimizer.step()

        total_train_loss += loss.item()

    avg_train_loss = total_train_loss / len(train_loader)
    train_losses.append(avg_train_loss)
    print(f"Epoch [{epoch+1}/{num_epochs}], Training Loss: {avg_train_loss:.4f}")

    # Validation loop
    pointnet.eval()
    total_val_loss = 0
    correct = 0
    with torch.no_grad():
        for batch_mesh, batch_labels in val_loader:
            global_feature, global_feature_maxpooled, local_embedding, T2, outcome = pointnet(batch_mesh)
            
            # Compute loss
            classification_loss = loss_fn(outcome, batch_labels)
            reg_loss = 0.01 * regularization(torch.bmm(T2, T2.permute(0, 2, 1)), identity.expand(T2.shape[0], -1, -1))
            loss = classification_loss + reg_loss

            total_val_loss += loss.item()

            # Accuracy calculation
            _, predicted = torch.max(outcome, 1)
            correct += (predicted == batch_labels).sum().item()

    avg_val_loss = total_val_loss / len(val_loader)
    accuracy = correct / len(val_dataset)
    val_losses.append(avg_val_loss)
    accuracies.append(accuracy)
    print(f"Validation Loss: {avg_val_loss:.4f}, Accuracy: {accuracy:.4f}")

# Save the model
model_path = './pointnet_model.pth'
torch.save(pointnet.state_dict(), model_path)
print(f"Model saved to {model_path}")

# Plot learning curves
plt.figure(figsize=(12, 5))

# Plot training and validation loss
plt.subplot(1, 2, 1)
plt.plot(range(1, num_epochs + 1), train_losses, label='Training Loss')
plt.plot(range(1, num_epochs + 1), val_losses, label='Validation Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.legend()
plt.title('Training and Validation Loss')

# Plot accuracy
plt.subplot(1, 2, 2)
plt.plot(range(1, num_epochs + 1), accuracies, label='Validation Accuracy')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.legend()
plt.title('Validation Accuracy')

plt.show()

# Load the model
loaded_model = PointNetClassifier(1, 3, NN_out_size)
loaded_model.load_state_dict(torch.load(model_path))
loaded_model.eval()

# Example for inference
example_mesh = torch.randn(1, 3, 1)  # Replace with actual example mesh data
with torch.no_grad():
    # Get predictions
    outputs = loaded_model(example_mesh)
    # Check if the output is a tuple and extract the first element if it is
    if isinstance(outputs, tuple):
        outputs = outputs[0]
        print(outputs)
    # Get the predicted label
    predicted_label = torch.argmax(outputs, dim=1)
    print(f"Predicted Label: {predicted_label.item()}")
