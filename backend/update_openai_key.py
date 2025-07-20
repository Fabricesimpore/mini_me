#!/usr/bin/env python3
"""Update OpenAI API key in .env file"""
import os
from pathlib import Path

def update_openai_key():
    env_file = Path(__file__).parent / ".env"
    
    print("🔧 Update OpenAI API Key")
    print("=" * 50)
    
    # Read current .env
    if env_file.exists():
        with open(env_file, 'r') as f:
            lines = f.readlines()
    else:
        print("❌ No .env file found! Creating one...")
        lines = []
    
    # Get new API key
    print("\nEnter your OpenAI API key (get one at https://platform.openai.com/api-keys)")
    print("It should start with 'sk-'")
    api_key = input("OpenAI API Key: ").strip()
    
    if not api_key:
        print("❌ No API key provided. Exiting.")
        return
    
    if not api_key.startswith('sk-'):
        print("⚠️  Warning: OpenAI keys usually start with 'sk-'")
        confirm = input("Continue anyway? (y/N): ").lower()
        if confirm != 'y':
            return
    
    # Update or add OPENAI_API_KEY
    updated = False
    new_lines = []
    
    for line in lines:
        if line.strip().startswith('OPENAI_API_KEY='):
            new_lines.append(f'OPENAI_API_KEY={api_key}\n')
            updated = True
        else:
            new_lines.append(line)
    
    # If not found, add it
    if not updated:
        new_lines.append(f'\nOPENAI_API_KEY={api_key}\n')
    
    # Write back
    with open(env_file, 'w') as f:
        f.writelines(new_lines)
    
    print(f"\n✅ OpenAI API key updated in {env_file}")
    print("\n📋 Next steps:")
    print("1. Install OpenAI package: pip install openai")
    print("2. Restart the backend server")
    print("3. The chat will now use GPT-3.5 for intelligent responses!")

if __name__ == "__main__":
    update_openai_key()