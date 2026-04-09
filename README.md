# OpenRouter CLI 🚀

-------------------

Manage and interact with OpenRouter's current **FREE LLM models** directly from your terminal.

## Features

- **Real-time Discovery**: Automatically fetches and filters models from OpenRouter to show only those with $0.00 pricing for both prompts and completions.
- **Interactive Terminal Chat**: Test the free models instantly with a built-in chat loop featuring markdown support.
- **Cline & Extension Helper**: Generates ready-to-use configuration strings and JSON snippets for tools like [Cline](https://github.com/cline/cline) or other IDE extensions.
- **Modern CLI**: A polished user experience built with `rich` and `questionary`.

## Prerequisites

- [Python 3.8+](https://www.python.org/)
- An [OpenRouter](https://openrouter.ai/) account and an API Token.

## Installation

1. **Clone or download** this project.
2. **Navigate** to the project directory:
   ```bash
   cd openrouter_free
   ```
3. **Set up a virtual environment** (optional but recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` in your favorite editor and add your OpenRouter API Key:
   ```env
   OPENROUTER_API_KEY=sk-or-v1-your-key-goes-here
   ```

## Usage

Simply run the main script to start the interactive menu:

```bash
python3 main.py
```

### Options:
- **List Free Models**: Displays a table of all currently available free models, their IDs, and context lengths.
- **Select Model & Chat**: Choose a model and start a direct conversation in your terminal.
- **Get Config for Cline/Extensions**: Select a model to get the exact configuration details needed for external tools.

## Troubleshooting

- **No models found**: Ensure your `.env` file is correctly set up and your API key is valid.
- **Connection Error**: Check your internet connection and verify that you can reach `openrouter.ai`.

---
*Created with ❤️ for free AI enthusiasts.*
