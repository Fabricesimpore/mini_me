import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json

class NLPService:
    """Service for natural language processing of chat messages"""
    
    def __init__(self):
        # Intent patterns
        self.intent_patterns = {
            "memory_storage": [
                r"i (went|did|had|met|saw|visited)",
                r"today i",
                r"yesterday i",
                r"last (week|month|year)",
                r"i (am|was|will be)",
                r"(finished|completed|started)",
                r"personal best",
                r"achievement"
            ],
            "memory_query": [
                r"when (did|was|were)",
                r"what did i",
                r"who did i",
                r"where did i",
                r"how (often|many)",
                r"last time",
                r"do i (usually|often|always)",
                r"tell me about"
            ],
            "reflection": [
                r"i (feel|am feeling|felt)",
                r"i'm (stressed|happy|sad|anxious|excited|overwhelmed)",
                r"thinking about",
                r"worried about",
                r"grateful for"
            ]
        }
        
        # Entity patterns
        self.entity_patterns = {
            "person": r"\b(?:with |met |saw |talked to |called |emailed )([A-Z][a-z]+(?: [A-Z][a-z]+)?)\b",
            "place": r"\b(?:at |in |to |from )(?:the )?([A-Z][a-z]+(?: [A-Z][a-z]+)*)\b",
            "time": r"\b(today|yesterday|tomorrow|last \w+|next \w+|\d{1,2}(?:am|pm)|morning|afternoon|evening)\b",
            "activity": r"\b(gym|workout|meeting|lunch|dinner|coffee|run|walk|work|project)\b",
            "emotion": r"\b(happy|sad|stressed|anxious|excited|overwhelmed|tired|energetic|grateful)\b"
        }
    
    def analyze_message(self, message: str) -> Dict[str, Any]:
        """Analyze a message to determine intent and extract entities"""
        message_lower = message.lower()
        
        # Determine intent
        intent = "general"
        for intent_type, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    intent = intent_type
                    break
            if intent != "general":
                break
        
        # Extract entities
        entities = self.extract_entities(message)
        
        return {
            "intent": intent,
            "entities": entities,
            "original_message": message
        }
    
    def extract_entities(self, message: str) -> List[Dict[str, Any]]:
        """Extract entities from a message"""
        entities = []
        
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.finditer(pattern, message, re.IGNORECASE)
            for match in matches:
                value = match.group(1) if match.groups() else match.group(0)
                entities.append({
                    "type": entity_type,
                    "value": value.strip(),
                    "start": match.start(),
                    "end": match.end()
                })
        
        return entities
    
    def extract_memory_data(self, message: str, entities: List[Dict]) -> Dict[str, Any]:
        """Extract structured data for memory storage"""
        data = {
            "type": "episodic",
            "metadata": {}
        }
        
        # Determine memory type based on content
        if any(e["type"] == "person" for e in entities):
            data["metadata"]["has_social_interaction"] = True
            if "relationship" in message.lower():
                data["type"] = "social"
        
        if any(e["type"] == "activity" for e in entities):
            data["metadata"]["activity"] = [e["value"] for e in entities if e["type"] == "activity"]
        
        if any(e["type"] == "emotion" for e in entities):
            data["metadata"]["emotion"] = entities[0]["value"]
            data["type"] = "semantic"
        
        # Extract achievement or milestone
        if re.search(r"(personal best|achievement|milestone|first time)", message, re.IGNORECASE):
            data["metadata"]["achievement"] = True
        
        # Extract temporal information
        time_entities = [e for e in entities if e["type"] == "time"]
        if time_entities:
            data["metadata"]["temporal"] = time_entities[0]["value"]
        
        return data
    
    def extract_query_params(self, message: str, entities: List[Dict]) -> Dict[str, Any]:
        """Extract parameters for memory queries"""
        params = {
            "query": message,
            "type": None,
            "time_range": None
        }
        
        # Determine query type
        if "when" in message.lower():
            params["query_type"] = "temporal"
        elif "who" in message.lower():
            params["type"] = "social"
        elif "what" in message.lower():
            params["query_type"] = "activity"
        
        # Extract time range
        time_patterns = {
            "last week": {"days": 7},
            "last month": {"days": 30},
            "yesterday": {"days": 1},
            "last year": {"days": 365}
        }
        
        for pattern, delta in time_patterns.items():
            if pattern in message.lower():
                params["time_range"] = {
                    "start": datetime.utcnow() - timedelta(**delta),
                    "end": datetime.utcnow()
                }
                break
        
        return params
    
    def extract_reflection_data(self, message: str, entities: List[Dict]) -> Dict[str, Any]:
        """Extract data from self-reflection messages"""
        data = {}
        
        # Extract emotions
        emotion_entities = [e for e in entities if e["type"] == "emotion"]
        if emotion_entities:
            data["emotion"] = emotion_entities[0]["value"]
        
        # Extract topics of reflection
        if "about" in message:
            about_match = re.search(r"about (.+?)(?:\.|$)", message, re.IGNORECASE)
            if about_match:
                data["topic"] = about_match.group(1).strip()
        
        # Determine intensity
        intensity_words = ["very", "really", "extremely", "quite", "somewhat"]
        for word in intensity_words:
            if word in message.lower():
                data["intensity"] = word
                break
        
        return data