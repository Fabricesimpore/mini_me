#!/usr/bin/env python3
"""Set up environment variables for the Digital Twin Platform"""
import os
from pathlib import Path

def setup_env():
    env_file = Path(__file__).parent / ".env"
    
    print("🔧 Digital Twin Platform Environment Setup")
    print("=" * 50)
    
    # Check if .env already exists
    if env_file.exists():
        print("⚠️  .env file already exists!")
        overwrite = input("Do you want to overwrite it? (y/N): ").lower()
        if overwrite != 'y':
            print("Setup cancelled.")
            return
    
    # Collect configuration
    print("\n1. OpenAI Configuration (for advanced chat features)")
    openai_key = input("Enter your OpenAI API key (or press Enter to skip): ").strip()
    
    print("\n2. Security Configuration")
    secret_key = input("Enter a secret key for JWT (or press Enter for default): ").strip()
    if not secret_key:
        import secrets
        secret_key = secrets.token_urlsafe(32)
        print(f"Generated secret key: {secret_key[:10]}...")
    
    # Write .env file
    env_content = f"""# Digital Twin Platform Configuration

# OpenAI API (optional - for enhanced chat features)
OPENAI_API_KEY={openai_key}

# Security
SECRET_KEY={secret_key}

# Database
DATABASE_URL=sqlite:///./digital_twin.db

# Feature Flags
ENABLE_OPENAI_CHAT={'true' if openai_key else 'false'}
ENABLE_ML_MODELS=true
ENABLE_REAL_INTEGRATIONS=false
"""
    
    env_file.write_text(env_content)
    print(f"\n✅ Environment file created at: {env_file}")
    
    # Create .env.example
    example_content = """# Digital Twin Platform Configuration

# OpenAI API (optional - for enhanced chat features)
OPENAI_API_KEY=your-openai-api-key-here

# Security
SECRET_KEY=your-secret-key-here-change-in-production

# Database
DATABASE_URL=sqlite:///./digital_twin.db

# Feature Flags
ENABLE_OPENAI_CHAT=false
ENABLE_ML_MODELS=true
ENABLE_REAL_INTEGRATIONS=false
"""
    
    example_file = Path(__file__).parent / ".env.example"
    example_file.write_text(example_content)
    print(f"✅ Example file created at: {example_file}")
    
    print("\n📋 Next steps:")
    print("1. Restart the backend server to load new environment variables")
    print("2. If you added an OpenAI key, the chat will use GPT-3.5 for responses")
    print("3. The app will work without OpenAI, using intelligent fallback responses")

if __name__ == "__main__":
    setup_env()