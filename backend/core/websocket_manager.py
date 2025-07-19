from typing import Dict, List
from fastapi import WebSocket
import json
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_data_streams: Dict[str, List[dict]] = defaultdict(list)
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept WebSocket connection"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"User {user_id} connected via WebSocket")
    
    def disconnect(self, user_id: str):
        """Remove WebSocket connection"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
    
    async def send_personal_message(self, message: dict, user_id: str):
        """Send message to specific user"""
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected users"""
        for connection in self.active_connections.values():
            await connection.send_json(message)
    
    async def process_behavioral_data(self, user_id: str, data: dict):
        """Process incoming behavioral data from user"""
        # Store in memory for processing
        self.user_data_streams[user_id].append(data)
        
        # Process based on data type
        data_type = data.get("type")
        
        if data_type == "screen_activity":
            await self._process_screen_activity(user_id, data)
        elif data_type == "communication":
            await self._process_communication(user_id, data)
        elif data_type == "decision":
            await self._process_decision(user_id, data)
        elif data_type == "navigation":
            await self._process_navigation(user_id, data)
        
        # Send acknowledgment
        await self.send_personal_message({
            "type": "ack",
            "message": f"Received {data_type} data",
            "timestamp": data.get("timestamp")
        }, user_id)
    
    async def _process_screen_activity(self, user_id: str, data: dict):
        """Process screen activity data"""
        logger.info(f"Processing screen activity for user {user_id}")
        # TODO: Implement screen activity processing
    
    async def _process_communication(self, user_id: str, data: dict):
        """Process communication data"""
        logger.info(f"Processing communication data for user {user_id}")
        # TODO: Implement communication processing
    
    async def _process_decision(self, user_id: str, data: dict):
        """Process decision data"""
        logger.info(f"Processing decision data for user {user_id}")
        # TODO: Implement decision processing
    
    async def _process_navigation(self, user_id: str, data: dict):
        """Process navigation data"""
        logger.info(f"Processing navigation data for user {user_id}")
        # TODO: Implement navigation processing