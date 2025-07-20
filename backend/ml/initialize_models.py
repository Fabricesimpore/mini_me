"""Initialize and save ML models for the Digital Twin Platform"""
import os
import pickle
import joblib
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
import torch
import torch.nn as nn

# Create models directory
models_dir = Path(__file__).parent.parent / "ml_models"
models_dir.mkdir(exist_ok=True)

print("Initializing ML models...")

# 1. Communication Style Model (TF-IDF + Random Forest)
print("Creating communication style model...")
comm_vectorizer = TfidfVectorizer(max_features=1000, ngram_range=(1, 2))
comm_classifier = RandomForestClassifier(n_estimators=100, random_state=42)

# Save with dummy data to establish the model structure
dummy_texts = [
    "I think we should analyze this carefully",
    "Let's dive right in!",
    "Consider all perspectives",
    "Quick decision needed"
]
dummy_labels = [0, 1, 0, 1]  # 0: analytical, 1: direct

X_comm = comm_vectorizer.fit_transform(dummy_texts)
comm_classifier.fit(X_comm, dummy_labels)

joblib.dump(comm_vectorizer, models_dir / "communication_vectorizer.pkl")
joblib.dump(comm_classifier, models_dir / "communication_classifier.pkl")
print("✓ Communication style model saved")

# 2. Behavioral Pattern Model (Simple neural network)
print("Creating behavioral pattern model...")
class SimpleBehavioralNet(nn.Module):
    def __init__(self, input_size=10, hidden_size=20, output_size=5):
        super().__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(hidden_size, output_size)
        
    def forward(self, x):
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        return x

behavioral_model = SimpleBehavioralNet()
torch.save(behavioral_model.state_dict(), models_dir / "behavioral_pattern_model.pth")
print("✓ Behavioral pattern model saved")

# 3. Productivity Predictor
print("Creating productivity predictor...")
prod_scaler = StandardScaler()
prod_model = RandomForestClassifier(n_estimators=50, random_state=42)

# Dummy data: [hour_of_day, day_of_week, task_count, break_count]
dummy_features = np.array([
    [9, 1, 5, 2],   # Morning weekday
    [14, 1, 3, 1],  # Afternoon weekday
    [10, 6, 2, 3],  # Weekend morning
    [20, 5, 1, 0],  # Evening
])
dummy_productivity = [3, 2, 1, 0]  # 0-3 productivity scale

X_prod = prod_scaler.fit_transform(dummy_features)
prod_model.fit(X_prod, dummy_productivity)

joblib.dump(prod_scaler, models_dir / "productivity_scaler.pkl")
joblib.dump(prod_model, models_dir / "productivity_model.pkl")
print("✓ Productivity predictor saved")

# 4. Learning Style Classifier
print("Creating learning style classifier...")
learning_features = StandardScaler()
learning_model = RandomForestClassifier(n_estimators=50, random_state=42)

# Dummy data: [reading_time, video_time, practice_time, discussion_time]
dummy_learning = np.array([
    [30, 10, 50, 10],  # Kinesthetic
    [10, 60, 20, 10],  # Visual
    [50, 20, 20, 10],  # Reading
    [10, 10, 30, 50],  # Social
])
dummy_styles = [0, 1, 2, 3]  # Different learning styles

X_learn = learning_features.fit_transform(dummy_learning)
learning_model.fit(X_learn, dummy_styles)

joblib.dump(learning_features, models_dir / "learning_scaler.pkl")
joblib.dump(learning_model, models_dir / "learning_model.pkl")
print("✓ Learning style classifier saved")

# 5. Save model metadata
metadata = {
    "version": "1.0",
    "created_at": "2025-01-20",
    "models": {
        "communication_style": {
            "vectorizer": "communication_vectorizer.pkl",
            "classifier": "communication_classifier.pkl",
            "classes": ["analytical", "direct", "collaborative", "creative"]
        },
        "behavioral_pattern": {
            "model": "behavioral_pattern_model.pth",
            "input_size": 10,
            "patterns": ["focused", "multitasking", "break-taking", "deep-work", "collaborative"]
        },
        "productivity": {
            "scaler": "productivity_scaler.pkl",
            "model": "productivity_model.pkl",
            "scale": [0, 1, 2, 3]  # Low to High
        },
        "learning_style": {
            "scaler": "learning_scaler.pkl", 
            "model": "learning_model.pkl",
            "styles": ["kinesthetic", "visual", "reading", "social"]
        }
    }
}

with open(models_dir / "model_metadata.json", "w") as f:
    import json
    json.dump(metadata, f, indent=2)

print("\n✅ All models initialized successfully!")
print(f"Models saved to: {models_dir}")
print("\nModels created:")
for model_type in metadata["models"]:
    print(f"  - {model_type}")