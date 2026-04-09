import os
import sys
import questionary
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.markdown import Markdown
from openrouter_client import OpenRouterClient

# Initialize Rich Console
console = Console()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def load_config():
    """Load API key from .env"""
    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        console.print("[bold red]Error:[/] OPENROUTER_API_KEY not found in .env file.")
        console.print("Please copy .env.example to .env and add your API key.")
        sys.exit(1)
    return api_key

def display_models_table(models):
    """Display free models in a rich table"""
    table = Table(title="Available Free LLM Models", border_style="bright_blue")
    
    table.add_column("Index", justify="right", style="cyan", no_wrap=True)
    table.add_column("Model Name", style="magenta")
    table.add_column("Model ID", style="green")
    table.add_column("Context", justify="right", style="yellow")
    
    for i, model in enumerate(models, 1):
        table.add_row(
            str(i),
            model.get('name', 'N/A'),
            model.get('id', 'N/A'),
            str(model.get('context_length', 'N/A'))
        )
    
    console.print(table)

def chat_loop(client, model_id, model_name):
    """Interactive chat loop with the selected model"""
    clear_screen()
    console.print(Panel(f"Chatting with [bold cyan]{model_name}[/]\nType [bold red]'exit'[/] or [bold red]'quit'[/] to return to menu.", 
                        title="Terminal Chat", border_style="bright_blue"))
    
    messages = []
    
    while True:
        user_input = questionary.text("You:", qmark=">").ask()
        
        if not user_input or user_input.lower() in ['exit', 'quit']:
            break
            
        messages.append({"role": "user", "content": user_input})
        
        with console.status(f"[bold green]LLM is thinking...[/]", spinner="dots"):
            response = client.chat_completion(model_id, messages)
            
        if response:
            console.print("\n[bold magenta]AI:[/]")
            console.print(Markdown(response))
            console.print("-" * 20 + "\n")
            messages.append({"role": "assistant", "content": response})
        else:
            console.print("[bold red]Failed to get response from AI.[/]")

def show_cline_config(model):
    """Display configuration info for Cline/Extensions"""
    clear_screen()
    model_id = model.get('id')
    model_name = model.get('name')
    
    config_text = f"""
### Cline / Extension Configuration for {model_name}

**API Provider:** OpenRouter
**Model ID:** `{model_id}`
**Base URL:** `https://openrouter.ai/api/v1`

#### JSON Configuration Snippet:
```json
{{
  "apiProvider": "openrouter",
  "openrouterModelId": "{model_id}",
  "apiKey": "YOUR_OPENROUTER_API_KEY"
}}
```
"""
    console.print(Panel(Markdown(config_text), title="Configuration Helper", border_style="bright_green"))
    questionary.press_any_key_to_continue().ask()

def main():
    api_key = load_config()
    client = OpenRouterClient(api_key)
    
    clear_screen()
    console.print(Panel.fit("Welcome to [bold cyan]FreeRouter CLI[/] 🚀\nEasily manage and use OpenRouter's free models.", 
                            border_style="bright_magenta"))
    
    free_models = []
    
    while True:
        choice = questionary.select(
            "What would you like to do?",
            choices=[
                "List Free Models",
                "Select Model & Chat",
                "Get Config for Cline/Extensions",
                "Exit"
            ]
        ).ask()
        
        if choice == "Exit":
            console.print("[bold yellow]Goodbye![/]")
            break
            
        if choice == "List Free Models" or not free_models:
            with console.status("[bold blue]Fetching free models...[/]"):
                free_models = client.get_free_models()
            
            if not free_models:
                console.print("[bold red]No free models found or error occurred.[/]")
                continue
                
            display_models_table(free_models)
            if choice == "List Free Models":
                questionary.press_any_key_to_continue().ask()
                continue

        if choice in ["Select Model & Chat", "Get Config for Cline/Extensions"]:
            if not free_models:
                continue
                
            model_choices = [f"{m.get('name')} ({m.get('id')})" for m in free_models]
            selected_str = questionary.select(
                "Select a model:",
                choices=model_choices
            ).ask()
            
            if not selected_str:
                continue
                
            # Find the model object
            selected_model = next(m for m in free_models if f"{m.get('name')} ({m.get('id')})" == selected_str)
            
            if choice == "Select Model & Chat":
                chat_loop(client, selected_model.get('id'), selected_model.get('name'))
            else:
                show_cline_config(selected_model)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Exiting...[/]")
        sys.exit(0)
