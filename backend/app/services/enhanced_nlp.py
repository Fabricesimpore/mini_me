import re
import random
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional, Tuple
import json
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta

class EnhancedNLPService:
    """Enhanced NLP service with better intent detection and time parsing"""
    
    def __init__(self):
        # Enhanced intent patterns with confidence scores
        self.intent_patterns = {
            "memory_storage": {
                "patterns": [
                    (r"\b(i|I) (just|recently)?\s*(went|did|had|met|saw|visited|bought|ate|drank|finished|completed|started|learned)", 0.9),
                    (r"\b(today|yesterday|this morning|this evening|last night) i\b", 0.85),
                    (r"\b(i|I) (am|was|will be|have been)\s+(at|in|going)", 0.8),
                    (r"\b(finished|completed|started|achieved|accomplished)", 0.85),
                    (r"\b(personal best|milestone|achievement|first time)", 0.9),
                    (r"\b(note|remember|record|log):\s*", 0.95),
                ],
                "negative_patterns": [
                    r"\b(when|what|where|who|how|did i|have i)\b",
                    r"\?$"
                ]
            },
            "memory_query": {
                "patterns": [
                    (r"\b(when|what time) (did|was|were|have|had) (i|I)\b", 0.95),
                    (r"\b(what|where|who|how) did (i|I)\b", 0.9),
                    (r"\b(tell me|show me|find|search|look for) (about|when|what)", 0.85),
                    (r"\b(last time|most recent|recently when) (i|I)\b", 0.9),
                    (r"\b(how often|how many times) (do|did|have) (i|I)\b", 0.85),
                    (r"\b(what|who|where|when).*\?$", 0.8),
                    (r"\b(history|memories|past|previous) (of|about)\b", 0.85),
                ],
                "boost_patterns": [
                    r"\?$",
                    r"\b(query|search|find|recall)\b"
                ]
            },
            "reflection": {
                "patterns": [
                    (r"\b(i|I) (feel|am feeling|felt|have been feeling)\b", 0.9),
                    (r"\b(i'm|I'm|i am|I am) (stressed|happy|sad|anxious|excited|overwhelmed|tired|energetic|grateful)", 0.95),
                    (r"\b(thinking|worried|concerned|excited) about\b", 0.85),
                    (r"\b(grateful|thankful|appreciative) (for|that)\b", 0.9),
                    (r"\b(mood|emotion|feeling)s?\b.*(good|bad|great|terrible)", 0.8),
                ],
                "boost_patterns": [
                    r"\b(emotion|feeling|mood)\b"
                ]
            },
            "planning": {
                "patterns": [
                    (r"\b(i|I) (will|plan to|need to|should|must|have to|am)\b.*(tomorrow|next week|next month|later)", 0.9),
                    (r"\b(working|work|meeting|appointment|event).*(tomorrow|next week|later|at \d+)", 0.85),
                    (r"\b(tomorrow|next week|next month|later).*(i|I)\b", 0.8),
                    (r"\b(todo|to do|task|goal|objective):\s*", 0.9),
                    (r"\b(remind me|don't forget|remember to)\b", 0.95),
                ],
                "negative_patterns": [
                    r"\b(did|was|were|have been)\b"
                ]
            }
        }
        
        # Time expression patterns
        self.time_patterns = {
            "relative_past": [
                (r"(today|this morning|this afternoon|this evening)", lambda m=None: date.today()),
                (r"yesterday", lambda m=None: date.today() - timedelta(days=1)),
                (r"(\d+) days? ago", lambda m: date.today() - timedelta(days=int(m.group(1)))),
                (r"last (monday|tuesday|wednesday|thursday|friday|saturday|sunday)", self._last_weekday),
                (r"last week", lambda m=None: date.today() - timedelta(weeks=1)),
                (r"last month", lambda m=None: date.today() - relativedelta(months=1)),
                (r"(\d+) weeks? ago", lambda m: date.today() - timedelta(weeks=int(m.group(1)))),
                (r"(\d+) months? ago", lambda m: date.today() - relativedelta(months=int(m.group(1)))),
            ],
            "relative_future": [
                (r"tomorrow", lambda m=None: date.today() + timedelta(days=1)),
                (r"next (monday|tuesday|wednesday|thursday|friday|saturday|sunday)", self._next_weekday),
                (r"next week", lambda m=None: date.today() + timedelta(weeks=1)),
                (r"next month", lambda m=None: date.today() + relativedelta(months=1)),
                (r"in (\d+) days?", lambda m: date.today() + timedelta(days=int(m.group(1)))),
            ],
            "specific": [
                (r"on (january|february|march|april|may|june|july|august|september|october|november|december) (\d{1,2})", self._parse_month_day),
                (r"(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})", self._parse_date),
            ],
            "time_of_day": [
                (r"at (\d{1,2}):(\d{2})\s*(am|pm)?", self._parse_time),
                (r"this morning", ("06:00", "12:00")),
                (r"this afternoon", ("12:00", "18:00")),
                (r"this evening", ("18:00", "23:00")),
                (r"tonight", ("18:00", "23:59")),
            ]
        }
    
    def analyze_message(self, message: str, previous_message: str = None, previous_intent: str = None) -> Dict[str, Any]:
        """Analyze a message with enhanced intent detection and context awareness"""
        message_lower = message.lower()
        
        # Check for conversational follow-ups first
        if previous_message and previous_intent:
            # Check if this is a response to a question
            if "how many hours" in previous_message.lower() and any(word in message_lower for word in ["hr", "hour", "maybe"]):
                intent = "conversation_response"
                confidence = 0.9
                intent_scores = {"conversation_response": 0.9}
            elif message_lower in ["what?", "what", "huh?", "sorry?", "pardon?", "what do you mean?", "i don't understand"]:
                intent = "clarification_request"
                confidence = 0.95
                intent_scores = {"clarification_request": 0.95}
            elif len(message_lower.split()) <= 3 and previous_intent == "planning":
                # Short responses after planning questions are likely follow-ups
                intent = "conversation_response"
                confidence = 0.8
                intent_scores = {"conversation_response": 0.8}
            else:
                # Normal intent detection
                intent_scores = {}
                for intent_type, config in self.intent_patterns.items():
                    score = self._calculate_intent_score(message_lower, config)
                    intent_scores[intent_type] = score
                
                best_intent = max(intent_scores.items(), key=lambda x: x[1])
                intent = best_intent[0] if best_intent[1] > 0.5 else "general"
                confidence = best_intent[1] if best_intent[1] > 0.5 else 0.0
        else:
            # Normal intent detection without context
            intent_scores = {}
            for intent_type, config in self.intent_patterns.items():
                score = self._calculate_intent_score(message_lower, config)
                intent_scores[intent_type] = score
            
            best_intent = max(intent_scores.items(), key=lambda x: x[1])
            intent = best_intent[0] if best_intent[1] > 0.5 else "general"
            confidence = best_intent[1] if best_intent[1] > 0.5 else 0.0
        
        # Extract entities
        entities = self.extract_entities(message)
        
        # Extract time information
        time_info = self.extract_time_info(message)
        
        return {
            "intent": intent,
            "confidence": confidence,
            "entities": entities,
            "time_info": time_info,
            "original_message": message,
            "all_intent_scores": intent_scores
        }
    
    def _calculate_intent_score(self, message: str, config: Dict) -> float:
        """Calculate intent score based on patterns"""
        score = 0.0
        matches = 0
        
        # Check positive patterns
        for pattern_info in config["patterns"]:
            if isinstance(pattern_info, tuple):
                pattern, weight = pattern_info
            else:
                pattern, weight = pattern_info, 1.0
            
            if re.search(pattern, message):
                score += weight
                matches += 1
        
        # Check negative patterns
        if "negative_patterns" in config:
            for pattern in config["negative_patterns"]:
                if re.search(pattern, message):
                    score -= 0.3
        
        # Check boost patterns
        if "boost_patterns" in config:
            for pattern in config["boost_patterns"]:
                if re.search(pattern, message):
                    score += 0.2
        
        # Normalize score
        if matches > 0:
            score = score / matches
        
        return max(0.0, min(1.0, score))
    
    def extract_entities(self, message: str) -> List[Dict[str, Any]]:
        """Extract entities with improved patterns"""
        entities = []
        
        # Enhanced entity patterns
        entity_patterns = {
            "person": [
                r"\b(?:with |met |saw |talked to |called |texted |emailed |visited )([A-Z][a-z]+(?: [A-Z][a-z]+)*)",
                r"\b([A-Z][a-z]+(?: [A-Z][a-z]+)*) (?:called|texted|emailed|visited|invited) me",
            ],
            "place": [
                r"\b(?:at |in |to |from )(?:the )?([A-Z][a-z]+(?: [A-Z][a-z]+)*(?:\'s)?)",
                r"\b(gym|office|home|work|school|store|restaurant|cafe|park|beach|mall|hospital|airport)\b",
            ],
            "activity": [
                r"\b(workout|exercise|meeting|lunch|dinner|breakfast|coffee|run|walk|work|project|study|read|watch|play)\b",
                r"\b(shopping|cooking|cleaning|driving|traveling|sleeping|eating|drinking)\b",
            ],
            "emotion": [
                r"\b(happy|sad|stressed|anxious|excited|overwhelmed|tired|energetic|grateful|angry|frustrated|calm|peaceful)\b",
                r"\b(good|great|bad|terrible|amazing|awful|okay|fine)\b",
            ],
            "quantity": [
                r"\b(\d+)\s*(miles?|km|kilometers?|minutes?|hours?|days?|weeks?|months?|years?)\b",
                r"\b(\d+)\s*(times?|reps?|sets?|cups?|glasses?|bottles?|pieces?)\b",
            ]
        }
        
        for entity_type, patterns in entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, message, re.IGNORECASE)
                for match in matches:
                    value = match.group(1) if match.groups() else match.group(0)
                    entities.append({
                        "type": entity_type,
                        "value": value.strip(),
                        "start": match.start(),
                        "end": match.end(),
                        "confidence": 0.9
                    })
        
        # Remove duplicates
        seen = set()
        unique_entities = []
        for entity in entities:
            key = (entity["type"], entity["value"].lower())
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
        
        return unique_entities
    
    def extract_time_info(self, message: str) -> Dict[str, Any]:
        """Extract temporal information from message"""
        time_info = {
            "has_time": False,
            "time_type": None,
            "date": None,
            "date_range": None,
            "time_of_day": None,
            "raw_expression": None
        }
        
        message_lower = message.lower()
        
        # Check relative past expressions
        for pattern, handler in self.time_patterns["relative_past"]:
            match = re.search(pattern, message_lower)
            if match:
                time_info["has_time"] = True
                time_info["time_type"] = "relative_past"
                time_info["raw_expression"] = match.group(0)
                
                if callable(handler):
                    time_info["date"] = handler(match)
                break
        
        # Check for time of day
        for pattern, time_range in self.time_patterns["time_of_day"]:
            if re.search(pattern, message_lower):
                if isinstance(time_range, tuple):
                    time_info["time_of_day"] = time_range
                break
        
        return time_info
    
    def _last_weekday(self, match=None) -> date:
        """Get the date of last occurrence of a weekday"""
        if match:
            weekday_name = match.group(1).lower()
        else:
            return date.today() - timedelta(days=7)
        
        weekdays = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        target_weekday = weekdays.get(weekday_name, 0)
        today = date.today()
        days_back = (today.weekday() - target_weekday) % 7
        if days_back == 0:
            days_back = 7
        
        return today - timedelta(days=days_back)
    
    def _next_weekday(self, match=None) -> date:
        """Get the date of next occurrence of a weekday"""
        if match:
            weekday_name = match.group(1).lower()
        else:
            return date.today() + timedelta(days=7)
        
        weekdays = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        target_weekday = weekdays.get(weekday_name, 0)
        today = date.today()
        days_forward = (target_weekday - today.weekday()) % 7
        if days_forward == 0:
            days_forward = 7
        
        return today + timedelta(days=days_forward)
    
    def _parse_month_day(self, match) -> date:
        """Parse month and day"""
        month_name = match.group(1)
        day = int(match.group(2))
        
        months = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
        
        month = months.get(month_name.lower(), 1)
        year = date.today().year
        
        try:
            return date(year, month, day)
        except:
            return date.today()
    
    def _parse_date(self, match) -> date:
        """Parse date in various formats"""
        try:
            parts = match.groups()
            if len(parts[2]) == 2:
                year = 2000 + int(parts[2])
            else:
                year = int(parts[2])
            
            return date(year, int(parts[0]), int(parts[1]))
        except:
            return date.today()
    
    def _parse_time(self, match) -> Tuple[str, str]:
        """Parse time expression"""
        hour = int(match.group(1))
        minute = int(match.group(2))
        am_pm = match.group(3) if match.groups() > 2 else None
        
        if am_pm and am_pm.lower() == 'pm' and hour < 12:
            hour += 12
        elif am_pm and am_pm.lower() == 'am' and hour == 12:
            hour = 0
        
        return (f"{hour:02d}:{minute:02d}", f"{hour:02d}:{minute:02d}")
    
    def generate_contextual_response(self, intent: str, entities: List[Dict], 
                                   memories: List[Any] = None, time_info: Dict = None, 
                                   message: str = None, previous_message: str = None,
                                   in_conversation: bool = False) -> str:
        """Generate more contextual and natural responses"""
        
        # Get current time for context-aware responses
        current_hour = datetime.now().hour
        message_lower = message.lower() if message else ""
        
        # Handle special conversation intents first
        if intent == "conversation_response":
            if previous_message and "how many hours" in previous_message.lower():
                hours_match = re.search(r'(\d+)', message)
                if hours_match:
                    hours = int(hours_match.group(1))
                    if hours <= 4:
                        return f"Only {hours} hours? That's going to be tough with work at 9am. You'll definitely feel it tomorrow. Maybe try to squeeze in a bit more if you can?"
                    elif hours <= 6:
                        return f"{hours} hours isn't too bad, though you might still feel a bit tired. Make sure to have some caffeine ready for the morning!"
                    else:
                        return f"{hours} hours should be decent! You're being smart about it. Sweet dreams when you do hit the pillow."
                return "I see. Try to get as much rest as you can. Every bit helps when you have an early start."
            return "Got it. Tell me more about what's on your mind."
        
        elif intent == "clarification_request":
            if previous_message:
                return f"Sorry if I confused you! I was responding to when you said '{previous_message}'. Did I misunderstand something? Feel free to rephrase or ask me something else."
            return "Sorry, I might have misunderstood. Could you tell me more about what you meant?"
        
        elif intent == "memory_storage":
            # Extract key information
            activities = [e["value"] for e in entities if e["type"] == "activity"]
            people = [e["value"] for e in entities if e["type"] == "person"]
            places = [e["value"] for e in entities if e["type"] == "place"]
            emotions = [e["value"] for e in entities if e["type"] == "emotion"]
            
            response_parts = ["I've recorded that"]
            
            if activities:
                # Add appropriate verb if needed
                activity = activities[0].lower()
                if activity in ["breakfast", "lunch", "dinner", "meal", "snack"]:
                    response_parts.append(f"you had {activity}")
                elif activity.endswith("ing"):
                    response_parts.append(f"you were {activity}")
                else:
                    response_parts.append(f"you {activity}")
            if people:
                response_parts.append(f"with {people[0]}")
            if places:
                response_parts.append(f"at {places[0]}")
            
            response = " ".join(response_parts) + "."
            
            if emotions:
                response += f" I can see you're feeling {emotions[0]}."
            
            # Add contextual follow-up
            if "gym" in str(activities).lower() or "workout" in str(activities).lower():
                response += " Keep up the great work on your fitness!"
            elif "meeting" in str(activities).lower():
                response += " Hope it was productive!"
            
            return response
        
        elif intent == "memory_query":
            if not memories:
                if time_info and time_info["has_time"]:
                    return f"I don't have any memories recorded for {time_info['raw_expression']}. Try telling me about your activities!"
                return "I don't have any memories matching that query yet. Tell me more about your daily activities so I can help you remember better."
            
            # Format response based on query type
            if len(memories) == 1:
                memory = memories[0]
                return f"Based on my records: {memory.content}"
            else:
                response = f"I found {len(memories)} memories:\n\n"
                for i, memory in enumerate(memories[:5], 1):
                    # Format timestamp
                    time_str = memory.created_at.strftime("%B %d at %I:%M %p")
                    response += f"{i}. {time_str}: {memory.content}\n"
                
                if len(memories) > 5:
                    response += f"\n...and {len(memories) - 5} more memories."
                
                return response
        
        elif intent == "reflection":
            emotions = [e["value"] for e in entities if e["type"] == "emotion"]
            
            if emotions:
                emotion = emotions[0].lower()
                responses = {
                    "stressed": "I understand you're feeling stressed. It's important to take breaks and practice self-care. What's the main source of stress right now?",
                    "happy": "That's wonderful to hear! Happiness is worth celebrating. What's bringing you joy today?",
                    "anxious": "I hear that you're feeling anxious. Remember to breathe deeply. Would you like to talk about what's on your mind?",
                    "tired": "Rest is important for your well-being. Have you been getting enough sleep lately?",
                    "excited": "Your excitement is contagious! What are you looking forward to?",
                    "grateful": "Gratitude is such a positive mindset. It's great that you're recognizing the good things in your life."
                }
                
                return responses.get(emotion, f"Thank you for sharing that you're feeling {emotion}. Your emotional well-being is important.")
            
            return "Thank you for sharing your thoughts. Self-reflection helps me understand you better and track your emotional journey."
        
        elif intent == "planning":
            # Handle future planning with encouragement
            activities = [e["value"] for e in entities if e["type"] == "activity"]
            time_mentions = time_info.get("raw_expression", "") if time_info else ""
            message_lower = message.lower() if message else ""
            
            if "work" in message_lower or "working" in message_lower:
                # Check if they're up late and have work tomorrow
                if current_hour >= 23 or current_hour <= 3:
                    return "Oh, you have work tomorrow at 9am and you're still up? That's rough - you might want to try getting some sleep soon. Even a few hours can help. What's keeping you awake?"
                elif "still up" in message_lower:
                    # They mentioned being up late regardless of current time
                    return "Working tomorrow at 9am and mentioning you're still up? Sounds like you might have had a late night. How many hours of sleep are you hoping to get? Sometimes even a power nap can make a difference."
                else:
                    return "I've noted that you're working tomorrow at 9am. How are you feeling about it? Is there anything specific you need to prepare?"
            
            return "I'll remember that for you. Would you like me to help you prepare or remind you about anything specific?"
        
        else:
            # Context-aware conversational responses
            message_lower = message.lower() if message else ""
            
            # Check if we're in an active conversation
            if in_conversation or (previous_message and "?" in previous_message):
                # Continue the conversation naturally
                if "sleeping late" in message_lower:
                    return "Ah, planning to sleep in tomorrow? That's good since you're up so late now. Will you be able to with work at 9am though?"
                elif any(word in message_lower for word in ["tired", "exhausted", "sleepy"]):
                    return "I can imagine you're tired! Being up this late when you have work tomorrow is rough. What's keeping you from heading to bed?"
                else:
                    # Generic conversational continuation
                    responses = [
                        "I hear you. What else is on your mind?",
                        "That makes sense. Tell me more.",
                        "Interesting. How are you feeling about that?",
                        "Got it. Anything else you want to talk about?"
                    ]
                    return random.choice(responses)
            
            # Time-based responses only for new conversations
            elif current_hour >= 23 or current_hour <= 4:
                if "still up" in message_lower or "can't sleep" in message_lower:
                    return "I notice you're up pretty late! What's on your mind? Sometimes talking about it helps. Are you having trouble sleeping, or just enjoying the quiet hours?"
                elif "work" in message_lower and "tomorrow" in message_lower:
                    return "Working tomorrow and still awake at this hour? That's going to be a tough morning. What time do you need to be up? Maybe we should think about winding down soon."
                elif any(greeting in message_lower for greeting in ["hey", "hi", "hello"]):
                    return "Hey there! You're up late tonight. How's your evening going? Anything interesting keeping you awake?"
                else:
                    return "It's pretty late - or early, depending on how you look at it! What brings you here at this hour? Feel like sharing what's on your mind?"
            
            # Morning responses (5 AM - 11 AM)
            elif 5 <= current_hour < 12:
                if any(greeting in message_lower for greeting in ["hey", "hi", "hello", "good morning"]):
                    morning_greetings = [
                        "Good morning! How did you sleep? Ready to take on the day, or still warming up to it?",
                        "Hey there! Morning person or still need that coffee? What's the plan for today?",
                        "Morning! Hope you got some good rest. What's on your mind this morning?",
                        "Hi! Starting the day early I see. Feeling energized or taking it slow?"
                    ]
                    return random.choice(morning_greetings)
                else:
                    morning_responses = [
                        "Morning! What's on your agenda today? I'm here if you want to talk through your plans or just chat.",
                        "Good morning! Anything exciting happening today, or is it more of a routine kind of day?",
                        "Rise and shine! What are you looking forward to today? Or maybe dreading?",
                        "Morning vibes! How are you feeling about the day ahead?"
                    ]
                    return random.choice(morning_responses)
            
            # Afternoon responses (12 PM - 5 PM)
            elif 12 <= current_hour < 17:
                if any(greeting in message_lower for greeting in ["hey", "hi", "hello"]):
                    return "Hey! How's your day going so far? Productive afternoon or taking it easy?"
                else:
                    return "Afternoon! What's happening in your world right now? Feel free to share - whether it's work stuff, personal thoughts, or just random musings."
            
            # Evening responses (5 PM - 11 PM)
            elif 17 <= current_hour < 23:
                if any(greeting in message_lower for greeting in ["hey", "hi", "hello"]):
                    return "Hey there! How was your day? Winding down or still have things on your plate?"
                else:
                    return "Evening! Perfect time to reflect on the day. What's been the highlight so far? Or maybe there's something you need to get off your chest?"
            
            # Default conversational response with variety
            default_responses = [
                "I'm here and listening. What's going on with you right now? Whether it's something specific or you just want to chat, I'm all ears.",
                "Hey! I'm here for whatever you need - venting, planning, remembering, or just chatting. What's up?",
                "Thanks for checking in! What's on your mind? I'm here to listen, help you remember things, or just have a conversation.",
                "Hi there! Feel free to share whatever's on your mind - could be about your day, your thoughts, or anything really. I'm here to listen and help.",
                "Hey! Whether you want to talk about something specific or just see what's in your memory bank, I'm here. What would you like to do?"
            ]
            return random.choice(default_responses)