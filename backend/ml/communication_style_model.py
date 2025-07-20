import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModel
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
import logging
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import joblib
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger(__name__)


class CommunicationStyleAnalyzer:
    """Analyzes communication patterns and style from text data"""
    
    def __init__(self, model_path: str = "./ml/models"):
        self.model_path = Path(model_path)
        self.model_path.mkdir(exist_ok=True, parents=True)
        
        # Load pre-trained language model for embeddings
        self.tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
        self.language_model = AutoModel.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
        
        # Communication style dimensions
        self.style_dimensions = {
            'formality': {'formal': 0, 'casual': 1},
            'tone': {'positive': 0, 'neutral': 1, 'negative': 2},
            'directness': {'direct': 0, 'indirect': 1},
            'length': {'concise': 0, 'moderate': 1, 'verbose': 2},
            'emotion': {'emotional': 0, 'balanced': 1, 'analytical': 2}
        }
        
        # Initialize clusterer for pattern discovery
        self.pattern_clusterer = None
        self.pca = None
        
    def analyze_communication_batch(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze a batch of messages for communication patterns"""
        if not messages:
            return {"error": "No messages to analyze"}
        
        # Extract text and metadata
        texts = []
        metadata = []
        
        for msg in messages:
            text = msg.get('content', '') or msg.get('text', '')
            if text:
                texts.append(text)
                metadata.append({
                    'timestamp': msg.get('timestamp'),
                    'recipient': msg.get('recipient') or msg.get('to'),
                    'subject': msg.get('subject'),
                    'type': msg.get('type', 'email')
                })
        
        if not texts:
            return {"error": "No text content found in messages"}
        
        # Get embeddings
        embeddings = self._get_text_embeddings(texts)
        
        # Analyze individual messages
        message_analyses = []
        for text, embedding, meta in zip(texts, embeddings, metadata):
            analysis = self._analyze_single_message(text, embedding)
            analysis['metadata'] = meta
            message_analyses.append(analysis)
        
        # Aggregate patterns
        patterns = self._aggregate_communication_patterns(message_analyses)
        
        # Discover clusters
        clusters = self._discover_communication_clusters(embeddings, texts)
        
        return {
            "total_messages": len(messages),
            "individual_analyses": message_analyses[:10],  # Limit for response size
            "aggregate_patterns": patterns,
            "communication_clusters": clusters,
            "style_profile": self._create_style_profile(patterns)
        }
    
    def _get_text_embeddings(self, texts: List[str]) -> np.ndarray:
        """Get embeddings for a list of texts"""
        embeddings = []
        
        for text in texts:
            # Truncate long texts
            text = text[:512]
            
            # Tokenize
            inputs = self.tokenizer(text, return_tensors='pt', padding=True, truncation=True, max_length=512)
            
            # Get embeddings
            with torch.no_grad():
                outputs = self.language_model(**inputs)
                # Use mean pooling
                embedding = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
                embeddings.append(embedding)
        
        return np.array(embeddings)
    
    def _analyze_single_message(self, text: str, embedding: np.ndarray) -> Dict[str, Any]:
        """Analyze a single message for style characteristics"""
        analysis = {
            'text_sample': text[:100] + '...' if len(text) > 100 else text,
            'length': len(text.split()),
            'formality_score': self._calculate_formality(text),
            'tone_score': self._calculate_tone(text),
            'directness_score': self._calculate_directness(text),
            'emotion_score': self._calculate_emotion(text),
            'linguistic_features': self._extract_linguistic_features(text)
        }
        
        return analysis
    
    def _calculate_formality(self, text: str) -> float:
        """Calculate formality score (0 = very casual, 1 = very formal)"""
        # Simple heuristic based on word choices and patterns
        formal_indicators = [
            'please', 'kindly', 'regarding', 'pursuant', 'therefore',
            'however', 'furthermore', 'nevertheless', 'accordingly'
        ]
        casual_indicators = [
            'hey', 'hi', 'lol', 'btw', 'gonna', 'wanna', 'yeah', 'cool',
            '!', '?', '...', ':)', ':D', ';)'
        ]
        
        text_lower = text.lower()
        formal_count = sum(1 for word in formal_indicators if word in text_lower)
        casual_count = sum(1 for word in casual_indicators if word in text_lower)
        
        # Check for contractions (casual)
        contractions = ["don't", "won't", "can't", "isn't", "aren't", "i'm", "you're"]
        casual_count += sum(1 for c in contractions if c in text_lower)
        
        total_indicators = formal_count + casual_count
        if total_indicators == 0:
            return 0.5  # Neutral
        
        return formal_count / total_indicators
    
    def _calculate_tone(self, text: str) -> Dict[str, float]:
        """Calculate tone scores"""
        # Simple sentiment analysis using word lists
        positive_words = [
            'great', 'excellent', 'good', 'wonderful', 'fantastic', 'amazing',
            'thank', 'appreciate', 'glad', 'happy', 'pleased', 'delighted'
        ]
        negative_words = [
            'bad', 'poor', 'terrible', 'awful', 'disappointed', 'frustrated',
            'angry', 'upset', 'concern', 'problem', 'issue', 'unfortunately'
        ]
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        total_sentiment = positive_count + negative_count
        if total_sentiment == 0:
            return {'positive': 0.33, 'neutral': 0.34, 'negative': 0.33}
        
        return {
            'positive': positive_count / total_sentiment,
            'negative': negative_count / total_sentiment,
            'neutral': 1 - (positive_count + negative_count) / (len(text.split()) + 1)
        }
    
    def _calculate_directness(self, text: str) -> float:
        """Calculate directness score (0 = very indirect, 1 = very direct)"""
        # Direct communication indicators
        direct_indicators = [
            'need', 'must', 'will', 'require', 'expect', 'want',
            'please do', 'make sure', 'ensure', 'immediately'
        ]
        indirect_indicators = [
            'perhaps', 'maybe', 'might', 'could', 'would you mind',
            'if possible', 'when you get a chance', 'no rush'
        ]
        
        text_lower = text.lower()
        direct_count = sum(1 for phrase in direct_indicators if phrase in text_lower)
        indirect_count = sum(1 for phrase in indirect_indicators if phrase in text_lower)
        
        # Questions are often indirect
        question_count = text.count('?')
        indirect_count += question_count * 0.5
        
        total = direct_count + indirect_count
        if total == 0:
            return 0.5
        
        return direct_count / total
    
    def _calculate_emotion(self, text: str) -> Dict[str, float]:
        """Calculate emotional content"""
        # Emotion indicators
        emotional_words = [
            'feel', 'felt', 'feeling', 'love', 'hate', 'excited', 'worried',
            'anxious', 'happy', 'sad', 'angry', 'frustrated', 'delighted'
        ]
        analytical_words = [
            'analyze', 'consider', 'evaluate', 'assess', 'determine',
            'conclude', 'observe', 'data', 'metrics', 'performance'
        ]
        
        text_lower = text.lower()
        emotional_count = sum(1 for word in emotional_words if word in text_lower)
        analytical_count = sum(1 for word in analytical_words if word in text_lower)
        
        # Exclamation marks indicate emotion
        emotional_count += text.count('!') * 0.5
        
        total = emotional_count + analytical_count
        if total == 0:
            return {'emotional': 0.33, 'balanced': 0.34, 'analytical': 0.33}
        
        emotional_ratio = emotional_count / total
        analytical_ratio = analytical_count / total
        
        return {
            'emotional': emotional_ratio,
            'analytical': analytical_ratio,
            'balanced': 1 - abs(emotional_ratio - analytical_ratio)
        }
    
    def _extract_linguistic_features(self, text: str) -> Dict[str, Any]:
        """Extract various linguistic features"""
        words = text.split()
        sentences = text.split('. ')
        
        features = {
            'avg_word_length': np.mean([len(word) for word in words]) if words else 0,
            'avg_sentence_length': np.mean([len(s.split()) for s in sentences]) if sentences else 0,
            'vocabulary_diversity': len(set(words)) / len(words) if words else 0,
            'punctuation_usage': {
                'exclamation': text.count('!'),
                'question': text.count('?'),
                'ellipsis': text.count('...'),
                'comma': text.count(',')
            },
            'capitalization': sum(1 for word in words if word.isupper()) / len(words) if words else 0
        }
        
        return features
    
    def _aggregate_communication_patterns(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate individual analyses into overall patterns"""
        if not analyses:
            return {}
        
        # Aggregate scores
        formality_scores = [a['formality_score'] for a in analyses]
        directness_scores = [a['directness_score'] for a in analyses]
        word_counts = [a['length'] for a in analyses]
        
        # Aggregate tone
        tone_aggregate = defaultdict(list)
        for analysis in analyses:
            for tone, score in analysis['tone_score'].items():
                tone_aggregate[tone].append(score)
        
        # Aggregate emotion
        emotion_aggregate = defaultdict(list)
        for analysis in analyses:
            for emotion, score in analysis['emotion_score'].items():
                emotion_aggregate[emotion].append(score)
        
        patterns = {
            'average_formality': np.mean(formality_scores),
            'formality_consistency': 1 - np.std(formality_scores),
            'average_directness': np.mean(directness_scores),
            'average_message_length': np.mean(word_counts),
            'length_variance': np.std(word_counts),
            'dominant_tone': max(tone_aggregate.items(), key=lambda x: np.mean(x[1]))[0],
            'tone_distribution': {k: np.mean(v) for k, v in tone_aggregate.items()},
            'dominant_emotion': max(emotion_aggregate.items(), key=lambda x: np.mean(x[1]))[0],
            'emotion_distribution': {k: np.mean(v) for k, v in emotion_aggregate.items()}
        }
        
        # Communication style classification
        patterns['communication_style'] = self._classify_communication_style(patterns)
        
        return patterns
    
    def _classify_communication_style(self, patterns: Dict[str, Any]) -> str:
        """Classify overall communication style based on patterns"""
        formality = patterns.get('average_formality', 0.5)
        directness = patterns.get('average_directness', 0.5)
        emotion = patterns.get('emotion_distribution', {})
        
        # Simple rule-based classification
        if formality > 0.7 and directness > 0.7:
            return "professional_assertive"
        elif formality > 0.7 and directness < 0.3:
            return "professional_diplomatic"
        elif formality < 0.3 and emotion.get('emotional', 0) > 0.5:
            return "casual_expressive"
        elif formality < 0.3 and directness > 0.7:
            return "casual_direct"
        elif emotion.get('analytical', 0) > 0.6:
            return "analytical_focused"
        else:
            return "balanced_adaptive"
    
    def _discover_communication_clusters(self, embeddings: np.ndarray, texts: List[str]) -> List[Dict[str, Any]]:
        """Discover clusters in communication patterns"""
        if len(embeddings) < 5:
            return []
        
        # Reduce dimensionality for clustering
        n_components = min(10, len(embeddings) - 1)
        self.pca = PCA(n_components=n_components)
        reduced_embeddings = self.pca.fit_transform(embeddings)
        
        # Determine optimal number of clusters
        n_clusters = min(5, len(embeddings) // 3)
        self.pattern_clusterer = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = self.pattern_clusterer.fit_predict(reduced_embeddings)
        
        # Analyze each cluster
        cluster_info = []
        for i in range(n_clusters):
            cluster_indices = np.where(clusters == i)[0]
            cluster_texts = [texts[idx] for idx in cluster_indices]
            
            # Get representative samples
            cluster_center = self.pattern_clusterer.cluster_centers_[i]
            distances = np.linalg.norm(reduced_embeddings[cluster_indices] - cluster_center, axis=1)
            representative_idx = cluster_indices[np.argmin(distances)]
            
            cluster_info.append({
                'cluster_id': i,
                'size': len(cluster_indices),
                'percentage': len(cluster_indices) / len(texts) * 100,
                'representative_text': texts[representative_idx][:200] + '...',
                'common_patterns': self._extract_cluster_patterns(cluster_texts)
            })
        
        return cluster_info
    
    def _extract_cluster_patterns(self, texts: List[str]) -> Dict[str, Any]:
        """Extract common patterns from a cluster of texts"""
        # Simple pattern extraction
        all_words = ' '.join(texts).lower().split()
        word_freq = defaultdict(int)
        
        for word in all_words:
            if len(word) > 3:  # Skip short words
                word_freq[word] += 1
        
        # Get top words
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Average characteristics
        lengths = [len(text.split()) for text in texts]
        
        return {
            'top_words': [word for word, _ in top_words],
            'avg_length': np.mean(lengths),
            'length_range': (min(lengths), max(lengths))
        }
    
    def _create_style_profile(self, patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Create a comprehensive communication style profile"""
        profile = {
            'primary_style': patterns.get('communication_style', 'unknown'),
            'formality_level': self._categorize_score(patterns.get('average_formality', 0.5), 
                                                     ['casual', 'balanced', 'formal']),
            'directness_level': self._categorize_score(patterns.get('average_directness', 0.5),
                                                      ['indirect', 'balanced', 'direct']),
            'emotional_expression': patterns.get('dominant_emotion', 'balanced'),
            'message_length_preference': self._categorize_score(
                patterns.get('average_message_length', 50) / 100,
                ['concise', 'moderate', 'detailed']
            ),
            'consistency_score': patterns.get('formality_consistency', 0),
            'adaptability_indicators': {
                'varies_formality': patterns.get('formality_consistency', 1) < 0.7,
                'varies_length': patterns.get('length_variance', 0) > 20,
                'multi_tonal': len([v for v in patterns.get('tone_distribution', {}).values() if v > 0.2]) > 1
            }
        }
        
        return profile
    
    def _categorize_score(self, score: float, categories: List[str]) -> str:
        """Categorize a score into named categories"""
        if len(categories) == 2:
            return categories[0] if score < 0.5 else categories[1]
        elif len(categories) == 3:
            if score < 0.33:
                return categories[0]
            elif score < 0.67:
                return categories[1]
            else:
                return categories[2]
        return categories[0]
    
    def train_personalized_model(self, user_messages: List[Dict[str, Any]], user_id: str) -> Dict[str, Any]:
        """Train a personalized communication model for a specific user"""
        if len(user_messages) < 20:
            return {"error": "Insufficient messages for personalization", "required": 20, "current": len(user_messages)}
        
        # Analyze all messages
        analysis = self.analyze_communication_batch(user_messages)
        
        # Save user profile
        profile = {
            'user_id': user_id,
            'style_profile': analysis['style_profile'],
            'aggregate_patterns': analysis['aggregate_patterns'],
            'message_clusters': analysis['communication_clusters'],
            'training_date': datetime.utcnow().isoformat(),
            'training_samples': len(user_messages)
        }
        
        profile_path = self.model_path / f'communication_profile_{user_id}.pkl'
        joblib.dump(profile, profile_path)
        
        return {
            "status": "success",
            "profile": profile['style_profile'],
            "samples_analyzed": len(user_messages)
        }
    
    def generate_message_suggestion(self, user_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate message suggestions based on user's communication style"""
        # Load user profile
        profile_path = self.model_path / f'communication_profile_{user_id}.pkl'
        
        if not profile_path.exists():
            return {"error": "No communication profile found for user"}
        
        profile = joblib.load(profile_path)
        style = profile['style_profile']
        patterns = profile['aggregate_patterns']
        
        # Generate suggestions based on context
        recipient = context.get('recipient', 'general')
        purpose = context.get('purpose', 'general')
        
        suggestions = {
            'greeting': self._suggest_greeting(style['formality_level'], recipient),
            'tone': self._suggest_tone(style['primary_style'], purpose),
            'structure': self._suggest_structure(style['message_length_preference']),
            'closing': self._suggest_closing(style['formality_level']),
            'style_tips': self._get_style_tips(style, patterns)
        }
        
        return suggestions
    
    def _suggest_greeting(self, formality: str, recipient: str) -> List[str]:
        """Suggest appropriate greetings"""
        greetings = {
            'formal': ['Dear', 'Good morning', 'Good afternoon'],
            'balanced': ['Hi', 'Hello', 'Good day'],
            'casual': ['Hey', 'Hi there', 'Hello']
        }
        return greetings.get(formality, greetings['balanced'])
    
    def _suggest_tone(self, style: str, purpose: str) -> str:
        """Suggest appropriate tone"""
        tone_map = {
            'professional_assertive': 'Clear and confident, state your points directly',
            'professional_diplomatic': 'Polite and considerate, use diplomatic language',
            'casual_expressive': 'Friendly and warm, feel free to express personality',
            'casual_direct': 'Straightforward and informal, get to the point quickly',
            'analytical_focused': 'Fact-based and logical, support with data',
            'balanced_adaptive': 'Flexible approach, adjust based on recipient'
        }
        return tone_map.get(style, 'Maintain your natural communication style')
    
    def _suggest_structure(self, length_pref: str) -> Dict[str, str]:
        """Suggest message structure"""
        structures = {
            'concise': {
                'format': 'Brief and to the point',
                'tip': 'Use bullet points for multiple items'
            },
            'moderate': {
                'format': 'Standard paragraph structure',
                'tip': 'Include context but stay focused'
            },
            'detailed': {
                'format': 'Comprehensive with sections',
                'tip': 'Use headings for different topics'
            }
        }
        return structures.get(length_pref, structures['moderate'])
    
    def _suggest_closing(self, formality: str) -> List[str]:
        """Suggest appropriate closings"""
        closings = {
            'formal': ['Best regards', 'Sincerely', 'Kind regards'],
            'balanced': ['Best', 'Thanks', 'Regards'],
            'casual': ['Cheers', 'Thanks!', 'Talk soon']
        }
        return closings.get(formality, closings['balanced'])
    
    def _get_style_tips(self, style: Dict[str, Any], patterns: Dict[str, Any]) -> List[str]:
        """Get personalized style tips"""
        tips = []
        
        if style['consistency_score'] < 0.5:
            tips.append("Your style varies significantly - this shows adaptability!")
        
        if patterns.get('average_formality', 0.5) > 0.7:
            tips.append("You tend toward formal communication - consider the audience")
        
        if patterns.get('average_directness', 0.5) < 0.3:
            tips.append("You prefer indirect communication - this can be diplomatic")
        
        if style['adaptability_indicators']['multi_tonal']:
            tips.append("You effectively adjust your tone for different situations")
        
        return tips