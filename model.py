import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

# ---------------------------
# 1. Load and prepare data
# ---------------------------
# Replace 'parkinson_data.csv' with your actual file
df = pd.read_csv('parkinson_data.csv')

# Feature columns
feature_cols = ['ax', 'ay', 'az', 'gx', 'gy', 'gz', 'left_click', 'right_click']
X = df[feature_cols].values.astype(np.float32)
y = df['label'].values.astype(np.float32)   # label column name, modify if needed

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# Standardize features
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# Convert to PyTorch tensors
X_train_t = torch.tensor(X_train, dtype=torch.float32)
y_train_t = torch.tensor(y_train, dtype=torch.float32).view(-1, 1)
X_test_t = torch.tensor(X_test, dtype=torch.float32)
y_test_t = torch.tensor(y_test, dtype=torch.float32).view(-1, 1)

# Create DataLoader
train_dataset = TensorDataset(X_train_t, y_train_t)
test_dataset = TensorDataset(X_test_t, y_test_t)
train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)

# ---------------------------
# 2. Define the neural network
# ---------------------------
class ParkinsonClassifier(nn.Module):
    def __init__(self, input_dim):
        super(ParkinsonClassifier, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )
    
    def forward(self, x):
        return self.net(x)

# Model, loss, optimizer
model = ParkinsonClassifier(input_dim=8)
criterion = nn.BCELoss()   # binary cross entropy
optimizer = optim.Adam(model.parameters(), lr=0.001)

# ---------------------------
# 3. Training loop
# ---------------------------
epochs = 50
for epoch in range(epochs):
    model.train()
    running_loss = 0.0
    for batch_X, batch_y in train_loader:
        optimizer.zero_grad()
        outputs = model(batch_X)
        loss = criterion(outputs, batch_y)
        loss.backward()
        optimizer.step()
        running_loss += loss.item()
    
    # Print loss every 10 epochs
    if (epoch + 1) % 10 == 0:
        print(f"Epoch {epoch+1}/{epochs}, Loss: {running_loss/len(train_loader):.4f}")

# ---------------------------
# 4. Evaluation on test set
# ---------------------------
model.eval()
all_preds = []
all_labels = []
with torch.no_grad():
    for batch_X, batch_y in test_loader:
        outputs = model(batch_X)
        preds = (outputs > 0.5).float()
        all_preds.extend(preds.cpu().numpy())
        all_labels.extend(batch_y.cpu().numpy())

all_preds = np.array(all_preds).flatten()
all_labels = np.array(all_labels).flatten()

acc = accuracy_score(all_labels, all_preds)
print(f"\nTest Accuracy: {acc:.4f}")
print("Confusion Matrix:")
print(confusion_matrix(all_labels, all_preds))
print("\nClassification Report:")
print(classification_report(all_labels, all_preds))

# ---------------------------
# 5. Prediction on new samples
# ---------------------------
def predict_parkinson(new_data):
    """
    new_data: list or 2D array with 8 features [ax, ay, az, gx, gy, gz, left_click, right_click]
    Returns probability of Parkinson's.
    """
    model.eval()
    new_data = np.array(new_data, dtype=np.float32).reshape(1, -1)
    new_data_scaled = scaler.transform(new_data)
    new_tensor = torch.tensor(new_data_scaled, dtype=torch.float32)
    with torch.no_grad():
        prob = model(new_tensor).item()
    return prob

# Example: predict on first test sample
example_prob = predict_parkinson(X_test[0])
print(f"\nExample prediction probability: {example_prob:.4f} -> {'Parkinson' if example_prob > 0.5 else 'No Parkinson'}")