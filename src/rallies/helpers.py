import random
import tiktoken
import json
import os
import requests
from pathlib import Path
from getpass import getpass
from .llm import LLM, get_default_model
from rich.markdown import Markdown

class TokenCounter:
    def __init__(self, model: str = None):
        model_name = model or get_default_model()
        try:
            self.encoding = tiktoken.encoding_for_model(model_name)
        except KeyError:
            self.encoding = tiktoken.get_encoding("o200k_base")
    
    def count_tokens(self, text: str) -> int:
        if not text:
            return 0
        return len(self.encoding.encode(text))
    
    def count_conversation_tokens(self, conversation: list) -> int:
        total_tokens = 0
        for message in conversation:
            if isinstance(message, dict) and "content" in message:
                total_tokens += self.count_tokens(message["content"])
            elif isinstance(message, str):
                total_tokens += self.count_tokens(message)
        return total_tokens
    
    def format_token_count(self, token_count: int) -> str:
        if token_count >= 1000:
            return f"{token_count / 1000:.1f}k tokens"
        return f"{token_count} tokens"

def get_timeout_message(elapsed_time):
    """Get appropriate message based on elapsed time"""
    
    if elapsed_time < 10:
        return "[yellow]  Retrieving data...[/yellow]"
    else:
         # After retrieving data, randomly pick from these messages every 10 seconds
        messages = [
                "[yellow]  Cogitating...[/yellow]",
                "[yellow]  Deep dive...[/yellow]",
                "[yellow]  Percolating...[/yellow]",
                "[yellow]  Synthesizing...[/yellow]",
                "[yellow]  Triangulating...[/yellow]",
                "[yellow]  Crystallizing...[/yellow]",
                "[yellow]  Distilling...[/yellow]",
                "[yellow]  Calibrating...[/yellow]",
                "[yellow]  Optimizing...[/yellow]",
                "[yellow]  Finalizing...[/yellow]",
                "[yellow]  Polishing...[/yellow]",
                "[yellow]  Contemplating...[/yellow]",
                "[yellow]  Deliberating...[/yellow]",
                "[yellow]  Ruminating...[/yellow]",
                "[yellow]  Pondering...[/yellow]",
                "[yellow]  Mulling over...[/yellow]",
                "[yellow]  Reflecting...[/yellow]",
                "[yellow]  Meditating...[/yellow]",
                "[yellow]  Concentrating...[/yellow]",
                "[yellow]  Focusing...[/yellow]",
                "[yellow]  Absorbing...[/yellow]",
                "[yellow]  Digesting...[/yellow]",
                "[yellow]  Assimilating...[/yellow]",
                "[yellow]  Integrating...[/yellow]",
                "[yellow]  Harmonizing...[/yellow]",
                "[yellow]  Balancing...[/yellow]",
                "[yellow]  Aligning...[/yellow]",
                "[yellow]  Orchestrating...[/yellow]",
                "[yellow]  Weaving...[/yellow]",
                "[yellow]  Crafting...[/yellow]",
                "[yellow]  Sculpting...[/yellow]",
                "[yellow]  Refining...[/yellow]",
        ]
        # Change message every 10 seconds after initial retrieval
        message_index = int((elapsed_time - 10) // 10) % len(messages)
        return messages[message_index]

def show_help(console):
    console.print("\n[bright_cyan]Available Commands:[/bright_cyan]")
    console.print("  [white]/setup[/white]              Run first-time setup wizard for API keys")
    console.print("  [white]/key API_KEY[/white]         Set your Rallies API key (backward compatible)")
    console.print("  [white]/key openai API_KEY[/white]  Set your OpenAI API key")
    console.print("  [white]/key openrouter API_KEY[/white] Set your OpenRouter API key")
    console.print("  [white]/key rallies API_KEY[/white] Set your Rallies API key")
    console.print("  [white]/feed[/white]               Show recent high-scoring questions from the community")
    console.print("  [white]/clear[/white]              Clear conversation history and free up context")
    console.print("  [white]/compact[/white]            Clear conversation history but keep a summary in context.")
    console.print("                      Optional: /compact [instructions for summarization]")
    console.print("  [white]/exit (quit)[/white]        Exit the REPL")
    console.print("  [white]/help[/white]               Show help and available commands")
    console.print()


def handle_help_command(console):
    show_help(console)
    return True


def handle_clear_command(conversation, console):
    conversation.clear()
    console.print("[green]Conversation history cleared.[/green]")
    return True


def handle_compact_command(prompt, conversation, agent, console):
    if len(conversation) == 0:
        console.print("[red]No conversation history to compact.[/red]")
        return True
    
    console.print("Let us compact the conversation to reduce tokens")
    conversation = agent.compact(conversation)
    tokens = TokenCounter().count_conversation_tokens(conversation)
    console.print(f"[green]✓ Conversation condensed to {tokens} tokens. You can continue asking more questions now.[/green]")
    console.print()
    return True 


def handle_exit_command(console):
    console.print("\nGoodbye!")
    import sys
    sys.exit(0)


def get_config_dir():
    """Get or create the config directory"""
    home = Path.home()
    config_dir = home / ".rallies"
    config_dir.mkdir(exist_ok=True)
    return config_dir


def get_config_file():
    """Get the config file path"""
    return get_config_dir() / "config.json"


def load_config():
    """Load configuration from file"""
    config_file = get_config_file()
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_config(config):
    """Save configuration to file"""
    config_file = get_config_file()
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f)
        try:
            # Restrict permissions to user read/write only
            os.chmod(config_file, 0o600)
        except Exception:
            # Best effort; ignore if platform does not support
            pass
        return True
    except IOError:
        return False


def get_rallies_api_key():
    """Get the stored Rallies API key (backward compatible with older 'api_key')."""
    config = load_config()
    return config.get("rallies_api_key") or config.get("api_key")


def set_rallies_api_key(api_key: str) -> bool:
    """Set and save the Rallies API key."""
    config = load_config()
    config["rallies_api_key"] = api_key
    # Keep old key name for backward compatibility
    config["api_key"] = api_key
    return save_config(config)


def get_openai_api_key() -> str:
    """Resolve OpenAI API key from env or config."""
    # Environment variable takes precedence
    env_key = os.getenv("OPENAI_API_KEY")
    if env_key:
        return env_key
    config = load_config()
    return config.get("openai_api_key")


def set_openai_api_key(api_key: str) -> bool:
    """Persist OpenAI API key in config."""
    config = load_config()
    config["openai_api_key"] = api_key
    saved = save_config(config)
    if saved:
        # Make available in current process
        os.environ["OPENAI_API_KEY"] = api_key
    return saved

def get_openrouter_api_key() -> str:
    """Resolve OpenRouter API key from env or config."""
    # Environment variable takes precedence
    env_key = os.getenv("OPENROUTER_API_KEY")
    if env_key:
        return env_key
    config = load_config()
    return config.get("openrouter_api_key")

def set_openrouter_api_key(api_key: str) -> bool:
    """Persist OpenRouter API key in config."""
    config = load_config()
    config["openrouter_api_key"] = api_key
    saved = save_config(config)
    if saved:
        # Make available in current process
        os.environ["OPENROUTER_API_KEY"] = api_key
    return saved

# Backward-compatible functions
def get_api_key():
    return get_rallies_api_key()

def set_api_key(api_key):
    return set_rallies_api_key(api_key)


def handle_key_command(prompt, agent, console):
    """Handle the /key command

    Supported forms:
      /key API_KEY                 -> sets Rallies API key (backward compatible)
      /key rallies API_KEY         -> sets Rallies API key
      /key openai API_KEY          -> sets OpenAI API key
      /key openrouter API_KEY      -> sets OpenRouter API key
    """
    parts = prompt.strip().split()
    if len(parts) < 2:
        console.print("[red]Usage: /key [openai|openrouter|rallies] API_KEY[/red]")
        return True

    if len(parts) == 2:
        # Backward compatible: set Rallies key
        api_key = parts[1]
        if set_rallies_api_key(api_key):
            agent.api_key = api_key
            console.print("[green]Rallies API key saved and activated.[/green]")
        else:
            console.print("[red]Failed to save Rallies API key.[/red]")
        return True

    provider = parts[1].lower()
    api_key = parts[2] if len(parts) > 2 else None
    if not api_key:
        console.print("[red]Usage: /key [openai|openrouter|rallies] API_KEY[/red]")
        return True

    if provider == "openai":
        if set_openai_api_key(api_key):
            console.print("[green]OpenAI API key saved and activated for this session.[/green]")
        else:
            console.print("[red]Failed to save OpenAI API key.[/red]")
    elif provider == "openrouter":
        if set_openrouter_api_key(api_key):
            console.print("[green]OpenRouter API key saved and activated for this session.[/green]")
        else:
            console.print("[red]Failed to save OpenRouter API key.[/red]")
    elif provider == "rallies":
        if set_rallies_api_key(api_key):
            agent.api_key = api_key
            console.print("[green]Rallies API key saved and activated.[/green]")
        else:
            console.print("[red]Failed to save Rallies API key.[/red]")
    else:
        console.print("[red]Unknown provider. Use 'openai', 'openrouter', or 'rallies'.[/red]")
    return True


def handle_setup_command(console):
    """Interactive setup wizard for first-time users."""
    console.print("\n[bright_cyan]Setup Wizard[/bright_cyan]")
    console.print("We'll configure your API keys. Press Enter to skip a field.")
    try:
        # OpenAI key
        existing_openai = get_openai_api_key()
        if existing_openai:
            console.print("[dim]OpenAI key already configured.[/dim]")
        else:
            openai_key = getpass("OpenAI API key: ")
            if openai_key.strip():
                if set_openai_api_key(openai_key.strip()):
                    console.print("[green]✓ OpenAI key saved.[/green]")
                else:
                    console.print("[red]Failed to save OpenAI key.[/red]")

        # OpenRouter key (optional)
        existing_openrouter = get_openrouter_api_key()
        if existing_openrouter:
            console.print("[dim]OpenRouter key already configured (optional).[/dim]")
        else:
            openrouter_key = getpass("OpenRouter API key (optional): ")
            if openrouter_key.strip():
                if set_openrouter_api_key(openrouter_key.strip()):
                    console.print("[green]✓ OpenRouter key saved.[/green]")
                else:
                    console.print("[red]Failed to save OpenRouter key.[/red]")

        # Rallies key (optional)
        existing_rallies = get_rallies_api_key()
        if existing_rallies:
            console.print("[dim]Rallies key already configured (optional).[/dim]")
        else:
            rallies_key = getpass("Rallies API key (optional): ")
            if rallies_key.strip():
                if set_rallies_api_key(rallies_key.strip()):
                    console.print("[green]✓ Rallies key saved.[/green]")
                else:
                    console.print("[red]Failed to save Rallies key.[/red]")

        console.print()
        console.print("[green]Setup complete. You can start asking questions![/green]")
    except KeyboardInterrupt:
        console.print("\n[yellow]Setup cancelled by user.[/yellow]")
    return True


def handle_feed_command(console):
    """Handle the /feed command - show recent high-scoring questions"""
    try:
        console.print("[yellow]Loading feed...[/yellow]")
        
        # Make request to the feed API
        response = requests.get("https://rallies.ai/api/get-feed-conversations?myfeed=0", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("conversations"):
                conversations = data["conversations"]
                
                # Filter for score > 4 and limit to 25, sorted by created_at
                high_score_conversations = [
                    conv for conv in conversations 
                    if conv.get("score", 0) > 4
                ]
                
                # Sort by created_at (most recent first)
                high_score_conversations.sort(
                    key=lambda x: x.get("created_at", ""), 
                    reverse=True
                )
                
                # Take only the first 25
                feed_items = high_score_conversations[:25]
                
                if feed_items:
                    console.print(f"\n[bright_cyan]Rallies feed, recent questions:[/bright_cyan]")
                    
                    # Build markdown content
                    markdown_content = []
                    for i, item in enumerate(feed_items, 1):
                        question = item.get("question", "").strip()
                        unique_link = item.get("unique_link", "")
                        score = item.get("score", 0)
                        
                        if question and unique_link:
                            # Truncate long questions
                            if len(question) > 80:
                                question = question[:77] + "..."
                            
                            url = f"https://rallies.ai/chat/{unique_link}"
                            markdown_content.append(f"{i:2}. [{question}]({url})")
                    
                    # Render all links as markdown
                    if markdown_content:
                        markdown_text = "\n".join(markdown_content)
                        console.print(Markdown(markdown_text))
                        console.print()
                        console.print("[dim]Click any question to open it in your browser[/dim]")
                else:
                    console.print("[yellow]No high-scoring questions found in the feed.[/yellow]")
            else:
                console.print("[red]Failed to load feed data.[/red]")
        else:
            console.print(f"[red]API request failed with status {response.status_code}[/red]")
            
    except requests.exceptions.Timeout:
        console.print("[red]Request timed out. Please try again.[/red]")
    except requests.exceptions.RequestException as e:
        console.print(f"[red]Network error: {str(e)}[/red]")
    except Exception as e:
        console.print(f"[red]Error loading feed: {str(e)}[/red]")
    
    return True


def handle_command(prompt, conversation, agent, console):
    if prompt.strip() == "/help":
        return handle_help_command(console)
    
    if prompt.strip() == "/setup":
        return handle_setup_command(console)
    
    if prompt.strip() == "/feed":
        return handle_feed_command(console)
    
    if prompt.strip() == "/clear":
        return handle_clear_command(conversation, console)
    
    if prompt.strip().startswith("/compact"):
        return handle_compact_command(prompt, conversation, agent, console)
    
    if prompt.strip().startswith("/key"):
        return handle_key_command(prompt, agent, console)
    
    if prompt.strip() in ["/exit", "/quit"]:
        handle_exit_command(console)

    
    return False