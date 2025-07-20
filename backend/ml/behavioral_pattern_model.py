import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta
import logging
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
from pathlib import Path

logger = logging.getLogger(__name__)


class BehavioralSequenceDataset(Dataset):
    """Dataset for behavioral sequences"""
    
    def __init__(self, sequences: List[np.ndarray], labels: List[int]):
        self.sequences = sequences
        self.labels = labels
        
    def __len__(self):
        return len(self.sequences)
    
    def __getitem__(self, idx):
        return torch.FloatTensor(self.sequences[idx]), torch.LongTensor([self.labels[idx]])


class BehavioralPatternLSTM(nn.Module):
    """LSTM model for behavioral pattern recognition"""
    
    def __init__(self, input_size: int, hidden_size: int = 128, num_layers: int = 2, 
                 num_classes: int = 10, dropout: float = 0.2):
        super(BehavioralPatternLSTM, self).__init__()
        
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # LSTM layers
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0
        )
        
        # Attention mechanism
        self.attention = nn.Sequential(
            nn.Linear(hidden_size, hidden_size),
            nn.Tanh(),
            nn.Linear(hidden_size, 1)
        )
        
        # Output layers
        self.fc1 = nn.Linear(hidden_size, hidden_size // 2)
        self.dropout = nn.Dropout(dropout)
        self.fc2 = nn.Linear(hidden_size // 2, num_classes)
        self.relu = nn.ReLU()
        
    def forward(self, x):
        # LSTM forward pass
        lstm_out, _ = self.lstm(x)
        
        # Apply attention
        attention_weights = torch.softmax(self.attention(lstm_out), dim=1)
        context_vector = torch.sum(attention_weights * lstm_out, dim=1)
        
        # Classification
        out = self.fc1(context_vector)
        out = self.relu(out)
        out = self.dropout(out)
        out = self.fc2(out)
        
        return out, attention_weights


class BehavioralPatternTrainer:
    """Trainer for behavioral pattern recognition models"""
    
    def __init__(self, model_path: str = "./ml/models"):
        self.model_path = Path(model_path)
        self.model_path.mkdir(exist_ok=True, parents=True)
        
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.pattern_labels = {
            0: "productive_flow",
            1: "distracted_browsing", 
            2: "communication_heavy",
            3: "learning_research",
            4: "creative_work",
            5: "administrative_tasks",
            6: "break_leisure",
            7: "meeting_collaboration",
            8: "deep_focus",
            9: "multitasking"
        }
        
    def prepare_behavioral_data(self, behaviors: List[Dict[str, Any]]) -> Tuple[List[np.ndarray], List[int]]:
        """Prepare behavioral data for training"""
        sequences = []
        labels = []
        
        # Group behaviors by time windows
        time_windows = self._create_time_windows(behaviors, window_size_minutes=30)
        
        for window in time_windows:
            if len(window) < 5:  # Skip windows with too few behaviors
                continue
            
            # Extract features from window
            feature_sequence = self._extract_feature_sequence(window)
            if feature_sequence is not None:
                sequences.append(feature_sequence)
                
                # Assign label based on dominant pattern
                label = self._assign_pattern_label(window)
                labels.append(label)
        
        return sequences, labels
    
    def _create_time_windows(self, behaviors: List[Dict[str, Any]], 
                           window_size_minutes: int = 30) -> List[List[Dict]]:
        """Create time-based windows from behaviors"""
        if not behaviors:
            return []
        
        # Sort by timestamp
        sorted_behaviors = sorted(behaviors, key=lambda x: x.get('timestamp', datetime.utcnow()))
        
        windows = []
        current_window = []
        window_start = None
        
        for behavior in sorted_behaviors:
            timestamp = behavior.get('timestamp', datetime.utcnow())
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            if window_start is None:
                window_start = timestamp
                current_window = [behavior]
            elif (timestamp - window_start).total_seconds() < window_size_minutes * 60:
                current_window.append(behavior)
            else:
                if current_window:
                    windows.append(current_window)
                window_start = timestamp
                current_window = [behavior]
        
        if current_window:
            windows.append(current_window)
        
        return windows
    
    def _extract_feature_sequence(self, window: List[Dict[str, Any]]) -> Optional[np.ndarray]:
        """Extract feature sequence from a behavior window"""
        features = []
        
        for behavior in window:
            feature_vector = self._extract_features(behavior)
            if feature_vector is not None:
                features.append(feature_vector)
        
        if not features:
            return None
        
        # Pad or truncate to fixed length
        max_seq_length = 50
        feature_array = np.array(features)
        
        if len(features) > max_seq_length:
            feature_array = feature_array[:max_seq_length]
        elif len(features) < max_seq_length:
            padding = np.zeros((max_seq_length - len(features), feature_array.shape[1]))
            feature_array = np.vstack([feature_array, padding])
        
        return feature_array
    
    def _extract_features(self, behavior: Dict[str, Any]) -> Optional[np.ndarray]:
        """Extract features from a single behavior"""
        features = []
        
        # Time-based features
        timestamp = behavior.get('timestamp', datetime.utcnow())
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        features.extend([
            timestamp.hour / 24,  # Normalized hour
            timestamp.weekday() / 7,  # Normalized day of week
            1 if timestamp.weekday() < 5 else 0  # Is weekday
        ])
        
        # Behavior type features (one-hot encoding)
        behavior_type = behavior.get('type', 'unknown')
        behavior_types = ['page_visit', 'click', 'scroll', 'idle', 'typing', 'app_switch']
        for bt in behavior_types:
            features.append(1 if behavior_type == bt else 0)
        
        # Activity features
        data = behavior.get('data', {})
        
        # URL/App features
        url = data.get('url', '')
        features.extend([
            1 if 'github' in url else 0,
            1 if 'stackoverflow' in url else 0,
            1 if 'google' in url else 0,
            1 if 'slack' in url else 0,
            1 if 'email' in url else 0,
            1 if 'calendar' in url else 0,
            1 if 'docs' in url else 0,
            1 if 'youtube' in url else 0,
            1 if 'social' in url or 'facebook' in url or 'twitter' in url else 0
        ])
        
        # Interaction intensity
        features.append(data.get('duration', 0) / 3600 if 'duration' in data else 0)  # Normalized duration
        features.append(data.get('scroll_depth', 0) / 100 if 'scroll_depth' in data else 0)  # Normalized scroll
        features.append(data.get('click_count', 0) / 100 if 'click_count' in data else 0)  # Normalized clicks
        
        return np.array(features)
    
    def _assign_pattern_label(self, window: List[Dict[str, Any]]) -> int:
        """Assign a pattern label to a behavior window"""
        # Analyze window characteristics
        behavior_types = [b.get('type', '') for b in window]
        urls = [b.get('data', {}).get('url', '') for b in window]
        
        # Count different activities
        coding_sites = sum(1 for url in urls if any(site in url for site in ['github', 'stackoverflow', 'localhost']))
        social_sites = sum(1 for url in urls if any(site in url for site in ['slack', 'teams', 'discord', 'email']))
        research_sites = sum(1 for url in urls if any(site in url for site in ['google', 'wikipedia', 'arxiv']))
        doc_sites = sum(1 for url in urls if any(site in url for site in ['docs', 'sheets', 'word']))
        
        total_sites = len(urls)
        if total_sites == 0:
            return 9  # multitasking (default)
        
        # Determine dominant pattern
        if coding_sites / total_sites > 0.6:
            return 8  # deep_focus
        elif social_sites / total_sites > 0.5:
            return 2  # communication_heavy
        elif research_sites / total_sites > 0.4:
            return 3  # learning_research
        elif doc_sites / total_sites > 0.4:
            return 5  # administrative_tasks
        elif len(set(urls)) / len(urls) > 0.8:  # High URL diversity
            return 1  # distracted_browsing
        else:
            return 0  # productive_flow
    
    def train_model(self, behaviors: List[Dict[str, Any]], epochs: int = 50, 
                    batch_size: int = 32, learning_rate: float = 0.001):
        """Train the behavioral pattern recognition model"""
        logger.info("Preparing behavioral data for training...")
        
        # Prepare data
        sequences, labels = self.prepare_behavioral_data(behaviors)
        
        if len(sequences) < 10:
            logger.warning("Insufficient data for training")
            return {"error": "Insufficient data", "required_samples": 10, "current_samples": len(sequences)}
        
        # Convert to numpy arrays
        X = np.array(sequences)
        y = np.array(labels)
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Create datasets
        train_dataset = BehavioralSequenceDataset(X_train, y_train)
        val_dataset = BehavioralSequenceDataset(X_val, y_val)
        
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
        
        # Initialize model
        input_size = X.shape[2]  # Number of features
        self.model = BehavioralPatternLSTM(
            input_size=input_size,
            num_classes=len(self.pattern_labels)
        )
        
        # Training setup
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5)
        
        # Training loop
        train_losses = []
        val_accuracies = []
        
        logger.info(f"Starting training for {epochs} epochs...")
        
        for epoch in range(epochs):
            # Training phase
            self.model.train()
            train_loss = 0
            
            for batch_sequences, batch_labels in train_loader:
                optimizer.zero_grad()
                
                outputs, _ = self.model(batch_sequences)
                loss = criterion(outputs, batch_labels.squeeze())
                
                loss.backward()
                optimizer.step()
                
                train_loss += loss.item()
            
            avg_train_loss = train_loss / len(train_loader)
            train_losses.append(avg_train_loss)
            
            # Validation phase
            self.model.eval()
            correct = 0
            total = 0
            
            with torch.no_grad():
                for batch_sequences, batch_labels in val_loader:
                    outputs, _ = self.model(batch_sequences)
                    _, predicted = torch.max(outputs.data, 1)
                    total += batch_labels.size(0)
                    correct += (predicted == batch_labels.squeeze()).sum().item()
            
            val_accuracy = correct / total
            val_accuracies.append(val_accuracy)
            
            scheduler.step(avg_train_loss)
            
            if epoch % 10 == 0:
                logger.info(f"Epoch {epoch}: Loss={avg_train_loss:.4f}, Val Accuracy={val_accuracy:.4f}")
        
        # Save model
        self.save_model()
        
        return {
            "status": "success",
            "epochs_trained": epochs,
            "final_loss": train_losses[-1],
            "final_accuracy": val_accuracies[-1],
            "training_samples": len(X_train),
            "validation_samples": len(X_val)
        }
    
    def predict_pattern(self, behaviors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Predict behavioral pattern from a sequence of behaviors"""
        if self.model is None:
            self.load_model()
            if self.model is None:
                return {"error": "No trained model available"}
        
        # Prepare data
        sequences, _ = self.prepare_behavioral_data(behaviors)
        
        if not sequences:
            return {"error": "No valid sequences found"}
        
        # Get the most recent sequence
        sequence = torch.FloatTensor(sequences[-1]).unsqueeze(0)
        
        self.model.eval()
        with torch.no_grad():
            outputs, attention_weights = self.model(sequence)
            probabilities = torch.softmax(outputs, dim=1)
            predicted_class = torch.argmax(outputs, dim=1).item()
        
        # Get top 3 predictions
        top_probs, top_indices = torch.topk(probabilities, k=min(3, len(self.pattern_labels)))
        
        predictions = []
        for prob, idx in zip(top_probs[0], top_indices[0]):
            predictions.append({
                "pattern": self.pattern_labels[idx.item()],
                "confidence": prob.item()
            })
        
        return {
            "primary_pattern": self.pattern_labels[predicted_class],
            "confidence": probabilities[0][predicted_class].item(),
            "all_predictions": predictions,
            "attention_focus": self._interpret_attention(attention_weights)
        }
    
    def _interpret_attention(self, attention_weights: torch.Tensor) -> List[int]:
        """Interpret attention weights to show which time steps were most important"""
        # Get top 5 time steps with highest attention
        weights = attention_weights.squeeze().cpu().numpy()
        top_indices = np.argsort(weights)[-5:][::-1]
        return top_indices.tolist()
    
    def save_model(self):
        """Save trained model and scaler"""
        if self.model is None:
            return
        
        model_state = {
            'model_state_dict': self.model.state_dict(),
            'model_config': {
                'input_size': self.model.lstm.input_size,
                'hidden_size': self.model.hidden_size,
                'num_layers': self.model.num_layers,
                'num_classes': len(self.pattern_labels)
            },
            'pattern_labels': self.pattern_labels,
            'feature_names': self.feature_names
        }
        
        torch.save(model_state, self.model_path / 'behavioral_pattern_model.pth')
        joblib.dump(self.scaler, self.model_path / 'feature_scaler.pkl')
        
        logger.info("Model saved successfully")
    
    def load_model(self):
        """Load trained model"""
        model_file = self.model_path / 'behavioral_pattern_model.pth'
        scaler_file = self.model_path / 'feature_scaler.pkl'
        
        if not model_file.exists():
            logger.warning("No saved model found")
            return
        
        # Load model state
        model_state = torch.load(model_file, map_location=torch.device('cpu'))
        
        # Initialize model with saved config
        config = model_state['model_config']
        self.model = BehavioralPatternLSTM(
            input_size=config['input_size'],
            hidden_size=config['hidden_size'],
            num_layers=config['num_layers'],
            num_classes=config['num_classes']
        )
        
        # Load weights
        self.model.load_state_dict(model_state['model_state_dict'])
        self.pattern_labels = model_state['pattern_labels']
        self.feature_names = model_state.get('feature_names', [])
        
        # Load scaler if exists
        if scaler_file.exists():
            self.scaler = joblib.load(scaler_file)
        
        logger.info("Model loaded successfully")