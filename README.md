# OpenRouter CLI 🚀

-------------------

Manage and interact with OpenRouter's current **FREE LLM models** directly from your terminal.

## Features

- **Real-time Discovery**: Automatically fetches and filters models from OpenRouter to show only those with **$0.00** pricing for both prompts and completions.
- **Interactive Terminal Chat**: Test the free models instantly with a built-in chat loop featuring markdown support.
- **Cline & Extension Helper**: Generates ready-to-use configuration strings and JSON snippets for tools like [Cline](https://github.com/cline/cline) or other IDE extensions.
- **Modern CLI**: A polished user experience built with `rich` and `questionary`.

## Pre-requisites

- [Python 3.8+](https://www.python.org/)
- An [OpenRouter](https://openrouter.ai/) account and an [OpenRouter API Token](https://openrouter.ai/docs/api/reference/authentication).

## Installation

1. **Clone** this project

```shell
git clone https://github.com/alexolinux/openrouter-cli.git
```

2. **Navigate** to the project directory

```shell
cd openrouter-cli
```

3. **Set up a virtual environment** (optional but recommended)

```shell
python3 -m venv venv
source venv/bin/activate
```

4. **Install dependencies**

```shell
pip install -r requirements.txt
```

## Configuration

1. Copy the example environment file:

 ```shell
 cp .env.example .env
 ```

2. Open `.env` in your favorite editor and add your OpenRouter API Key

```env
OPENROUTER_API_KEY=your-api-key-goes-here
```

## Usage

Simply run the main script to start the interactive menu:

```shell
python3 main.py
```

### Extra Usage Tip

Add a convenient global alias for the CLI so you can run it from anywhere without specifying the full path. Add the following function to your shell's configuration file (e.g., `~/.bashrc` or `~/.zshrc`):

```shell
# Customize this path according to your project structure
orcli() {
  $(pwd)/.venv/bin/python $(pwd)/main.py "$@"
}
```

This creates an `orcli` command that forwards all arguments to the OpenRouter CLI. After adding the function, reload your shell configuration:

```shell
source ~/.bashrc   # or source ~/.zshrc
```

Now you can invoke the CLI globally:

```shell
orcli
```

### Options

- **List Free Models**: Displays a table of all currently available free models, their IDs, and context lengths.
- **Select Model & Chat**: Choose a model and start a direct conversation in your terminal.
- **Get Config for Cline/Extensions**: Select a model to get the exact configuration details needed for external tools.

## Troubleshooting

- **No models found**: Ensure your `.env` file is correctly set up and your API key is valid.
- **Connection Error**: Check your internet connection and verify that you can reach `openrouter.ai`.

*Created with ❤️  for free AI enthusiasts.*

## Author

[Alex Mendes](https://github.com/alexolinux)
