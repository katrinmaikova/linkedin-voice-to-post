# LinkedIn Post Writer Bot

A Flexus bot that converts voice memos and text ideas into LinkedIn posts matching your personal writing style.

## Features

- **Voice-to-Text**: Send audio messages and get them transcribed using ElevenLabs speech-to-text
- **Style Learning**: Analyzes your existing LinkedIn posts to learn your writing patterns
- **Style Matching**: Generates posts that sound like you, not a generic bot
- **Persistent Storage**: Saves your style profile in policy documents for future use
- **Interactive Setup**: Guides you through the style learning process

## How It Works

### 1. First-Time Setup
- User provides 5 sample LinkedIn posts
- Bot analyzes:
  - Tone (professional, casual, inspirational, etc.)
  - Structure (paragraphs, bullet points, storytelling)
  - Length (character count and typical post length)
  - Formatting (line breaks, emojis, hashtags)
  - Voice (first person vs third person)
  - Opening and closing patterns
- Bot shows analysis and asks for approval
- Style profile saved to `/linkedin-writer/style-profile` policy document

### 2. Creating Posts
- User sends voice memo or text with ideas
- Bot transcribes audio (if applicable)
- Bot generates LinkedIn post draft matching learned style
- User reviews and can request adjustments

### 3. Updating Style
- User can provide new sample posts anytime
- Bot re-analyzes and updates the style profile
- Shows what changed in the updated profile

## Technical Details

### Tools Provided

1. **transcribe_audio**: Converts audio messages to text using ElevenLabs speech-to-text API
2. **analyze_style**: Analyzes sample LinkedIn posts to extract writing patterns
3. **generate_post**: Creates LinkedIn post drafts based on content and style profile
4. **flexus_policy_document**: Stores and retrieves the style profile
5. **flexus_mongo_store**: Additional storage for message history

### Requirements

- ElevenLabs API key (configured in bot setup for speech-to-text transcription)
- Python packages: `flexus-client-kit`, `elevenlabs`

### Architecture

- **Bot Name**: `linkedin_writer`
- **Version**: `0.1.0`
- **Model**: `grok-4-1-fast-non-reasoning` (fast responses for simple drafting tasks)
- **Storage**: Policy documents for style profiles, MongoDB for general storage
- **External API**: ElevenLabs speech-to-text API for audio transcription

## Files

- `linkedin_writer_bot.py`: Main bot runtime with tool handlers
- `linkedin_writer_prompts.py`: System prompts and instructions
- `linkedin_writer_install.py`: Marketplace registration
- `linkedin_writer-1024x1536.webp`: Large marketplace image
- `linkedin_writer-256x256.webp`: Bot avatar

## Installation

1. Install the package:
   ```bash
   pip install -e /workspace
   ```

2. Register the bot (BOB will handle this):
   ```bash
   python -m linkedin_writer.linkedin_writer_install --ws=<workspace_id>
   ```

3. Configure ElevenLabs API key in bot setup after hiring

## Usage Flow

```
User: [Pastes 5 sample LinkedIn posts]
Bot: [Analyzes style, shows results]
Bot: "Does this match your style? Any adjustments?"
User: "Looks good!"
Bot: [Saves style profile]

User: [Sends voice memo about new product launch]
Bot: [Transcribes audio]
Bot: [Generates post draft matching style]
Bot: "Here's your draft: [post]"
User: [Reviews and publishes]
```

## Future Enhancements

- Support for LinkedIn post templates
- A/B testing different post versions
- Analytics integration to track post performance
- Style variations for different audiences
- Image generation for posts
- Hashtag suggestions based on content
