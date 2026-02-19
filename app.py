"""
app.py — ShopEase E-commerce CLI v2.1
Premium CLI experience with Rich UI, Auto-complete, and Typed Interactions.
"""

import time
import sys
import random
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.live import Live
from rich.spinner import Spinner
from rich.align import Align
from rich.layout import Layout
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory

from engine import IntentEngine

# Initialize Console and Engine
console = Console()
engine = IntentEngine()

# Custom Styles
PROMPT_STYLE = Style.from_dict({
    'prompt': 'ansicyan bold',
})

# Auto-complete words
COMMANDS = [
    "track order", "where is my order", "check status",
    "return policy", "refund", "exchange",
    "help", "menu", "options",
    "iphone", "macbook", "headphones", "shoes", "watch",
    "price", "cost", "available", "stock",
    "cancel order", "exit", "bye", "quit"
]

completer = WordCompleter(COMMANDS, ignore_case=True)

def show_dashboard():
    """Displays a graphical dashboard on startup."""
    
    # 1. Header Banner
    banner_text = r"""
   _____ __                 ______
  / ___// /_  ____  ____   / ____/___ _________
  \__ \/ __ \/ __ \/ __ \ / __/ / __ `/ ___/ _ \\
 ___/ / / / / /_/ / /_/ // /___/ /_/ (__  )  __/
/____/_/ /_/\____/ .___//_____/\__,_/____/\___/
                /_/
    """
    console.print(Align.center(f"[bold blue]{banner_text}[/bold blue]"))
    console.print(Align.center("[yellow]★ v3.0 ULTIMATE EDITION ★[/yellow]"))
    console.print("\n")

    # 2. Category Grid
    table = Table(title="🔥 Trending Categories", box=None, header_style="bold magenta", padding=(0,2))
    table.add_column("Category", justify="center")
    table.add_column("Top Picks", justify="center")
    
    table.add_row("📱 [bold cyan]Electronics[/bold cyan]", "iPhone 15, MacBook M3, Sony XM5")
    table.add_row("👟 [bold green]Fashion[/bold green]", "Nike Jordans, Ray-Ban, Levi's")
    table.add_row("🏠 [bold orange1]Home[/bold orange1]", "Dyson Vacuum, Smart Fridge")
    
    # 3. Quick Stats Panel
    stats_panel = Panel(
        "⚡ [bold]Fast Delivery[/bold] | 💳 [bold]EMI Available[/bold] | 🔄 [bold]7-Day Returns[/bold]",
        style="dim white",
        width=60
    )
    
    console.print(Align.center(table))
    console.print(Align.center(stats_panel))
    console.print("\n")

def simulate_typing(text):
    """Simulates typing effect for realism."""
    with Live(Spinner('dots', text=text, style="cyan"), refresh_per_second=10, transient=True):
        time.sleep(random.uniform(0.3, 0.8))

def display_help():
    """Enhanced Help Menu."""
    grid = Table.grid(expand=True)
    grid.add_column()
    grid.add_column()
    
    left_panel = Panel(
        "[bold green]Shopping[/bold green]\n"
        "• 'Show iPhones'\n"
        "• 'Laptops under 50000'\n"
        "• 'Add to cart'\n"
        "• 'View Cart' / 'Checkout'",
        title="🛒 Buying", border_style="green"
    )
    
    right_panel = Panel(
        "[bold blue]Support[/bold blue]\n"
        "• 'Track 1001'\n"
        "• 'Return policy'\n"
        "• 'Call support'\n"
        "• 'Exit'",
        title="📞 Services", border_style="blue"
    )
    
    grid.add_row(left_panel, right_panel)
    console.print(grid)

def main():
    show_dashboard()
    
    # Initialize Request Session
    session = PromptSession(
        history=FileHistory('.history.txt'),
        completer=completer,
        style=PROMPT_STYLE
    )

    console.print("[bold green]ShopEase:[/bold green] Welcome! How can I help you today?")

    context = {"cart": []}
    
    while True:
        try:
            # User Input
            user_input = session.prompt("You: ", placeholder="Ask anything...")
            user_input = user_input.strip()

            if not user_input:
                continue

            # Debug shortcut
            if user_input == "--debug":
                console.print("[dim]Debug info will be shown.[/dim]")
                continue

            # Simulate typing
            simulate_typing("Processing...")

            # Get Response
            response_md, context, debug_info = engine.get_response(user_input, context)

            # Styling logic
            color = "green"
            title = "ShopEase"
            if "Total Amount" in response_md: color = "gold1" # Checkout
            if "⚠️" in response_md: color = "yellow"
            if "❌" in response_md: color = "red"
            
            # Render response
            console.print(Panel(Markdown(response_md), title=title, border_style=color))

            # Show Suggestions
            suggestions = engine.get_suggestions(context.get("last_intent", ""), context)
            if suggestions:
                sugg_text = " | ".join([f"[italic cyan]{s}[/italic cyan]" for s in suggestions])
                console.print(f"   [dim]👉 Try: {sugg_text}[/dim]")
            
            # Show Cart Summary (Mini) if items in cart
            if context.get("cart") and context.get("last_intent") != "cart_view":
                 count = len(context["cart"])
                 total = sum(x['price'] for x in context['cart'])
                 console.print(Align.right(f"[dim]🛒 Cart: {count} item(s) | ₹{total:,}[/dim]"))

            if context.get("should_exit"):
                break
                
        except KeyboardInterrupt:
            console.print("\n[bold red]Goodbye![/bold red]")
            break
        except EOFError:
            break

if __name__ == "__main__":
    main()
