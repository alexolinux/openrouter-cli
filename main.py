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

def load_request_settings():
    """Load optional local request safeguards from the environment."""
    try:
        max_requests = int(os.getenv("OPENROUTER_MAX_REQUESTS", "0"))
        timeout = int(os.getenv("OPENROUTER_REQUEST_TIMEOUT_SECONDS", "30"))
        if max_requests < 0 or timeout <= 0:
            raise ValueError
    except ValueError:
        console.print(
            "[bold red]Error:[/] OPENROUTER_MAX_REQUESTS must be 0 or greater and "
            "OPENROUTER_REQUEST_TIMEOUT_SECONDS must be greater than 0."
        )
        sys.exit(1)
    return max_requests, timeout, os.getenv("OPENROUTER_MANAGEMENT_API_KEY")

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

def display_request_usage(client):
    """Display diagnostic usage recorded by this CLI process."""
    usage = client.get_usage()
    limit = str(client.max_requests) if client.max_requests else "Unlimited"
    remaining = (
        str(max(client.max_requests - usage.chat_completions, 0))
        if client.max_requests else "Unlimited"
    )

    table = Table(title="Local CLI Session Usage", border_style="bright_blue")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Requests sent", str(usage.total))
    table.add_row("Chat-completion requests", str(usage.chat_completions))
    table.add_row("Successful", str(usage.successful))
    table.add_row("Failed", str(usage.failed))
    table.add_row("Blocked by local limit", str(usage.blocked))
    table.add_row("Session request limit", limit)
    table.add_row("Requests remaining", remaining)
    table.add_row("Last response status", str(usage.last_status_code or "N/A"))
    table.add_row(
        "Last response time",
        f"{usage.last_duration_ms} ms" if usage.last_duration_ms is not None else "N/A"
    )
    console.print(table)

    if usage.rate_limit_headers:
        limits = Table(title="Latest API Rate-Limit Headers", border_style="yellow")
        limits.add_column("Header", style="cyan")
        limits.add_column("Value", style="yellow")
        for key, value in sorted(usage.rate_limit_headers.items()):
            limits.add_row(key, value)
        console.print(limits)
    else:
        console.print("[dim]No rate-limit headers have been returned by the API in this session.[/]")

def display_openrouter_key_usage(client):
    """Display live usage and configured limits reported by OpenRouter for this key."""
    with console.status("[bold blue]Fetching API key usage from OpenRouter...[/]"):
        key_info = client.get_current_key_info()
        account_requests_today = client.get_account_requests_today()

    if not key_info:
        console.print("[bold red]OpenRouter did not return API-key usage information.[/]")
        return

    table = Table(title="OpenRouter API Key Usage (Live)", border_style="bright_green")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Key label", str(key_info.get("label", "N/A")))
    table.add_row(
        "Account AI requests consumed today (UTC)",
        str(account_requests_today) if account_requests_today is not None
        else "Requires OPENROUTER_MANAGEMENT_API_KEY"
    )
    table.add_row("Free-tier key", str(key_info.get("is_free_tier", "N/A")))
    table.add_row("Usage (USD)", str(key_info.get("usage", "N/A")))
    table.add_row("Usage today (USD)", str(key_info.get("usage_daily", "N/A")))
    table.add_row("Usage this week (USD)", str(key_info.get("usage_weekly", "N/A")))
    table.add_row("Usage this month (USD)", str(key_info.get("usage_monthly", "N/A")))
    table.add_row("Configured key limit (USD)", str(key_info.get("limit", "No limit")))
    table.add_row("Key limit remaining (USD)", str(key_info.get("limit_remaining", "N/A")))
    table.add_row("Key limit reset", str(key_info.get("limit_reset", "N/A")))
    table.add_row("Expires at", str(key_info.get("expires_at", "Never")))
    console.print(table)
    console.print(
        "[dim]These values come from OpenRouter for the current API key. "
        "The request count covers the account and is available with a management API key.[/]"
    )

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

        usage = client.get_usage()
        console.print(
            f"[dim]Chat requests: {usage.chat_completions}/{client.max_requests if client.max_requests else 'Unlimited'} | "
            f"Last status: {usage.last_status_code or 'N/A'} | "
            f"Last response: {usage.last_duration_ms if usage.last_duration_ms is not None else 'N/A'} ms[/]"
        )

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
    max_requests, timeout, management_api_key = load_request_settings()
    client = OpenRouterClient(
        api_key, max_requests=max_requests, timeout=timeout,
        management_api_key=management_api_key
    )
    
    clear_screen()
    console.print(Panel.fit("Welcome to [bold cyan]OpenRouter CLI[/] 🚀\nEasily manage and use OpenRouter's free models.", 
                            border_style="bright_magenta"))
    
    free_models = []
    
    while True:
        choice = questionary.select(
            "What would you like to do?",
            choices=[
                "List Free Models",
                "Select Model & Chat",
                "Get Config for Cline/Extensions",
                "Show OpenRouter API Key Usage (Live)",
                "Show Session API Usage",
                "Exit"
            ]
        ).ask()
        
        if choice == "Exit":
            console.print("[bold yellow]Goodbye![/]")
            break

        if choice == "Show Session API Usage":
            display_request_usage(client)
            questionary.press_any_key_to_continue().ask()
            continue

        if choice == "Show OpenRouter API Key Usage (Live)":
            display_openrouter_key_usage(client)
            questionary.press_any_key_to_continue().ask()
            continue
            
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
