import sys
import argparse
import os
from rich.text import Text
from rallies.manager import Manager
from rallies import console
from rallies.helpers import handle_setup_command, get_openai_api_key

def display_application_banner():
    banner_text = """
██╗    ██████╗ █████╗ ██╗     ██╗     ██╗███████╗███████╗
  ██╗  ██╔══██╗██╔══██╗██║     ██║     ██║██╔════╝██╔════╝
    ██ ╗█████╔╝███████║██║     ██║     ██║█████╗  ███████╗
  ██╔╝ ██╔══██╗██╔══██║██║     ██║     ██║██╔══╝  ╚════██║
██╔╝   ██║  ██║██║  ██║███████╗███████╗██║███████╗███████║
╚╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝╚══════╝╚══════╝
"""
    
    # Create gradient effect similar to Gemini CLI
    lines = banner_text.strip().split('\n')
    gradient_colors = ['bright_blue', 'blue', 'cyan', 'bright_cyan', 'magenta', 'bright_magenta']
    
    styled_lines = []
    for i, line in enumerate(lines):
        color = gradient_colors[i % len(gradient_colors)]
        styled_lines.append(Text(line, style=f"bold {color}"))
    
    # Combine all lines
    full_banner = Text()
    full_banner.append("\n\n")
    for line in styled_lines:
        full_banner.append(line)
        full_banner.append('\n')
    
    # Add subtitle with gradient
    subtitle = Text("AI powered investment research, backed by real-time data", style="bold bright_magenta")
    full_banner.append('\n')
    full_banner.append(subtitle)
    
    # Print banner without border, left-aligned like Gemini CLI
    console.print(full_banner)

def interactive_shell(no_banner: bool = False):
    if not no_banner:
        display_application_banner()
        # Tips section for user guidance
        console.print("\n[dim white]Tips for getting started:[/dim white]")
        console.print("[white]1. Ask questions about stocks, analyze trends, or get market insights.[/white]")
        console.print("[white]2. Be specific for the best results.[/white]")
        console.print("[white]3. Type /help for more information.[/white]\n")
    
    # Setup guidance if no OpenAI key
    if not get_openai_api_key():
        console.print("[yellow]OpenAI API key not found. Launching setup...[/yellow]")
        handle_setup_command(console)
        if not get_openai_api_key():
            console.print("[red]OpenAI API key is required to proceed.[/red]")
            sys.exit(1)

    selected_agent = Manager()
    print("\nType your queries below. Press Ctrl+C to exit.\n")
    messages = []
    try:
        while True:
            console.print("[bright_cyan]> [/bright_cyan]", end="")
            user_input_text = input()
            if user_input_text.strip():
                messages.append({"role": "user", "content": user_input_text})
                selected_agent.process_prompt(user_input_text, messages)
            else:
                console.print("[yellow]Please enter a query.[/yellow]\n")
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        sys.exit(0)

def main():
    parser = argparse.ArgumentParser(prog="rallies", add_help=True)
    parser.add_argument("-q", "--query", help="Run a single query in non-interactive mode")
    parser.add_argument("--no-banner", action="store_true", help="Disable startup banner")
    parser.add_argument("--no-color", action="store_true", help="Disable color output")
    parser.add_argument("--setup", action="store_true", help="Run setup wizard and exit")
    parser.add_argument("--plan-only", action="store_true", help="Print plan JSON and exit")
    parser.add_argument("--model", help="Override model name for this run")
    args = parser.parse_args()

    # Allow model override via flag for this process
    if args.model:
        os.environ["RALLIES_MODEL"] = args.model

    if args.no_color:
        os.environ["NO_COLOR"] = "1"

    if args.setup:
        handle_setup_command(console)
        return

    # Non-interactive one-shot mode
    if args.query is not None:
        # Allow reading from stdin when '-' is passed
        query = args.query
        if query.strip() == "-":
            query = sys.stdin.read()

        # Ensure key setup in one-shot
        if not get_openai_api_key():
            console.print("[yellow]OpenAI API key not found. Launching setup...[/yellow]")
            handle_setup_command(console)
            if not get_openai_api_key():
                console.print("[red]OpenAI API key is required to proceed.[/red]")
                sys.exit(1)

        manager = Manager()
        conversation = [{"role": "user", "content": query}]
        if args.plan_only:
            plan = manager.agent.run(conversation)
            console.print(str(plan))
            return
        result = manager.process_prompt(query, conversation)
        # Print final answer to stdout (already streamed to panel)
        if result:
            print(result)
        return

    # Interactive REPL
    interactive_shell(no_banner=args.no_banner)

if __name__ == '__main__':
    main()