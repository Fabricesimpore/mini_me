#!/usr/bin/env python3
"""Simple test to verify basic API structure"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing Digital Twin Backend API structure...")

try:
    # Test basic imports
    print("✓ Testing core imports...")
    from core.database import Base, get_db
    print("  - Database module OK")
    
    from core.websocket_manager import WebSocketManager
    print("  - WebSocket manager OK")
    
    # Test API endpoints
    print("\n✓ Testing API endpoint imports...")
    from api import health
    print("  - Health endpoint OK")
    
    print("\n✅ Basic API structure is valid!")
    print("\nTo run the full API, you need to:")
    print("1. Install all dependencies: pip install -r requirements.txt")
    print("2. Run: uvicorn main:app --reload")
    
except ImportError as e:
    print(f"\n❌ Import error: {e}")
    print("\nMake sure you have the required dependencies installed.")
except Exception as e:
    print(f"\n❌ Error: {e}")