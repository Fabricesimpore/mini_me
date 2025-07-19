from typing import Dict, List, Any, Optional
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)


class StyleExtractor:
    """Extract communication style patterns"""
    
    def extract_style(self, text: str) -> Dict[str, Any]:
        """Extract style characteristics from text"""
        return {
            "formality_level": self._measure_formality(text),
            "sentence_structure": self._analyze_sentence_structure(text),
            "vocabulary_complexity": self._measure_vocabulary_complexity(text),
            "punctuation_style": self._analyze_punctuation(text)
        }
    
    def _measure_formality(self, text: str) -> float:
        """Measure formality level (0-1, where 1 is most formal)"""
        informal_indicators = ["hey", "gonna", "wanna", "yeah", "lol", "btw"]
        formal_indicators = ["hereby", "therefore", "furthermore", "regards", "sincerely"]
        
        text_lower = text.lower()
        informal_count = sum(1 for word in informal_indicators if word in text_lower)
        formal_count = sum(1 for word in formal_indicators if word in text_lower)
        
        if informal_count + formal_count == 0:
            return 0.5
        
        return formal_count / (informal_count + formal_count)
    
    def _analyze_sentence_structure(self, text: str) -> Dict[str, Any]:
        """Analyze sentence structure patterns"""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return {"avg_length": 0, "complexity": "simple"}
        
        avg_length = sum(len(s.split()) for s in sentences) / len(sentences)
        
        return {
            "avg_length": avg_length,
            "complexity": "complex" if avg_length > 20 else "moderate" if avg_length > 10 else "simple"
        }
    
    def _measure_vocabulary_complexity(self, text: str) -> str:
        """Measure vocabulary complexity"""
        words = text.lower().split()
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        
        if avg_word_length > 6:
            return "advanced"
        elif avg_word_length > 4:
            return "moderate"
        else:
            return "simple"
    
    def _analyze_punctuation(self, text: str) -> Dict[str, Any]:
        """Analyze punctuation usage patterns"""
        return {
            "exclamation_marks": text.count('!'),
            "question_marks": text.count('?'),
            "ellipses": text.count('...'),
            "emoji_count": self._count_emojis(text)
        }
    
    def _count_emojis(self, text: str) -> int:
        """Count emojis in text (simplified)"""
        # This is a simplified version - in production would use proper emoji detection
        emoji_pattern = re.compile(r'[😀-🙏🌀-🗿]+')
        return len(emoji_pattern.findall(text))


class RelationshipMapper:
    """Map and track relationships"""
    
    def infer_relationship_type(self, messages: List[Dict[str, Any]]) -> str:
        """Infer relationship type from message patterns"""
        # Analyze formality, topics, and communication patterns
        formality_scores = []
        topics = []
        
        for msg in messages:
            if 'formality_level' in msg:
                formality_scores.append(msg['formality_level'])
            if 'topics' in msg:
                topics.extend(msg['topics'])
        
        avg_formality = sum(formality_scores) / len(formality_scores) if formality_scores else 0.5
        
        # Simple heuristic for relationship type
        if avg_formality > 0.7:
            return "professional"
        elif avg_formality > 0.4:
            return "colleague"
        else:
            return "friend"


class ContextAnalyzer:
    """Analyze communication context"""
    
    def analyze_context(self, message: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the context of a message"""
        return {
            "urgency": self._detect_urgency(message),
            "sentiment": self._analyze_sentiment(message),
            "topic": self._extract_topic(message),
            "requires_response": self._needs_response(message)
        }
    
    def _detect_urgency(self, message: str) -> str:
        """Detect urgency level"""
        urgent_keywords = ["urgent", "asap", "immediately", "critical", "emergency"]
        message_lower = message.lower()
        
        if any(keyword in message_lower for keyword in urgent_keywords):
            return "high"
        elif "soon" in message_lower or "today" in message_lower:
            return "medium"
        else:
            return "low"
    
    def _analyze_sentiment(self, message: str) -> str:
        """Simple sentiment analysis"""
        # In production, would use proper NLP model
        positive_words = ["thanks", "great", "excellent", "happy", "good"]
        negative_words = ["sorry", "problem", "issue", "unfortunately", "bad"]
        
        message_lower = message.lower()
        positive_count = sum(1 for word in positive_words if word in message_lower)
        negative_count = sum(1 for word in negative_words if word in message_lower)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    def _extract_topic(self, message: str) -> str:
        """Extract main topic (simplified)"""
        # In production, would use topic modeling
        work_keywords = ["project", "meeting", "deadline", "report", "task"]
        personal_keywords = ["weekend", "family", "vacation", "dinner", "party"]
        
        message_lower = message.lower()
        work_score = sum(1 for word in work_keywords if word in message_lower)
        personal_score = sum(1 for word in personal_keywords if word in message_lower)
        
        if work_score > personal_score:
            return "work"
        elif personal_score > work_score:
            return "personal"
        else:
            return "general"
    
    def _needs_response(self, message: str) -> bool:
        """Determine if message requires a response"""
        question_marks = message.count('?')
        request_phrases = ["please", "could you", "would you", "can you"]
        
        return question_marks > 0 or any(phrase in message.lower() for phrase in request_phrases)


class CommunicationAnalyzer:
    def __init__(self):
        self.style_extractor = StyleExtractor()
        self.relationship_mapper = RelationshipMapper()
        self.context_analyzer = ContextAnalyzer()
    
    async def analyze_communication(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze communication data"""
        message = data.get("message", "")
        metadata = data.get("metadata", {})
        
        # Extract style
        style = self.style_extractor.extract_style(message)
        
        # Analyze context
        context = self.context_analyzer.analyze_context(message, metadata)
        
        # Combine analysis
        analysis = {
            "style": style,
            "context": context,
            "timestamp": datetime.utcnow().isoformat(),
            "message_length": len(message),
            "word_count": len(message.split())
        }
        
        logger.info(f"Analyzed communication: {analysis['context']['topic']} - {analysis['context']['sentiment']}")
        
        return analysis
    
    async def analyze_email_thread(self, thread: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze an email thread"""
        analysis = {
            'participants': self.extract_participants(thread),
            'relationship_type': self.relationship_mapper.infer_relationship_type(thread.get("messages", [])),
            'communication_patterns': await self._analyze_thread_patterns(thread)
        }
        
        return analysis
    
    def extract_participants(self, thread: Dict[str, Any]) -> List[str]:
        """Extract participants from thread"""
        participants = set()
        for message in thread.get("messages", []):
            if "from" in message:
                participants.add(message["from"])
            if "to" in message:
                participants.update(message["to"])
        return list(participants)
    
    async def _analyze_thread_patterns(self, thread: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze communication patterns in thread"""
        messages = thread.get("messages", [])
        
        if not messages:
            return {}
        
        # Analyze response times
        response_times = []
        for i in range(1, len(messages)):
            if messages[i].get("from") != messages[i-1].get("from"):
                # Calculate time between messages
                # In production, would parse actual timestamps
                response_times.append(60)  # Placeholder: 60 minutes
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            "avg_response_time_minutes": avg_response_time,
            "message_count": len(messages),
            "thread_duration_hours": 24  # Placeholder
        }