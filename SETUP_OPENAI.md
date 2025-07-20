# Setting Up OpenAI for Enhanced Chat Features

The Digital Twin Platform can use OpenAI's GPT-3.5 for more intelligent and context-aware conversations. Here's how to set it up:

## Quick Setup

1. **Get an OpenAI API Key**
   - Go to https://platform.openai.com/api-keys
   - Create a new API key
   - Copy the key (starts with `sk-`)

2. **Configure the Backend**
   ```bash
   cd backend
   python3 setup_env.py
   ```
   - Enter your OpenAI API key when prompted
   - Or manually create a `.env` file with:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```

3. **Install OpenAI Package**
   ```bash
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install openai
   ```

4. **Restart the Backend**
   - Stop the backend (Ctrl+C)
   - Start it again to load the new environment variables

## Features with OpenAI

When OpenAI is configured, you get:
- **Context-aware responses** - The AI remembers your conversation history
- **Personality adaptation** - Learns and mirrors your communication style
- **Intelligent insights** - Provides meaningful analysis of your patterns
- **Topic extraction** - Automatically identifies what you're discussing
- **Sentiment analysis** - Understands the emotional tone of conversations

## Features without OpenAI

The app works perfectly without OpenAI, using:
- **Smart fallback responses** - Pre-programmed conversational AI
- **Pattern matching** - Recognizes common queries and intents
- **Basic personalization** - Learns from your interactions over time
- **All other features** - Integrations, analytics, and ML models work normally

## Cost Considerations

- GPT-3.5 is very affordable (~$0.002 per 1K tokens)
- Average conversation uses ~500-1000 tokens
- $5 credit can handle thousands of conversations

## Troubleshooting

If the chat isn't using OpenAI:
1. Check the backend logs for "OpenAI error" messages
2. Verify your API key is correct in `.env`
3. Ensure you have credits on your OpenAI account
4. Check that `pip install openai` succeeded

## Privacy Note

- Your conversations are sent to OpenAI's API when enabled
- OpenAI doesn't train on API data by default
- You can disable it anytime by removing the API key