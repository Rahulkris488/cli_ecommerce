"""
app.py — ShopEase E-commerce CLI Chatbot
Entry point. Uses Click for CLI interface and a continuous conversation loop.

Run with:
    python app.py
or:
    python app.py --name "Alice"
"""

import click
from services import get_response

BANNER = """
╔══════════════════════════════════════════════════════════╗
║          🛍️  ShopEase Customer Support Bot 🛍️              ║
║        Natural Language Interface for E-commerce         ║
╚══════════════════════════════════════════════════════════╝
  Type 'help' to see available options.
  Type 'bye' or 'exit' to quit.
──────────────────────────────────────────────────────────
"""


@click.command()
@click.option(
    "--name",
    default="Customer",
    help="Your name for a personalized greeting.",
    show_default=True
)
def chat(name: str):
    """
    ShopEase CLI Chatbot — handles order tracking, products,
    delivery, returns, refunds, and payment queries.
    """
    click.echo(BANNER)
    click.echo(f"  Hello, {name}! How can I help you today?\n")

    # Session context — persists across turns within one session
    context = {
        "awaiting_order_id": False,
        "should_exit": False,
        "user_name": name,
        "cart": {},
        "last_product": None,
        "last_intent": None,
    }

    while True:
        try:
            # Prompt for user input
            user_input = click.prompt(click.style("You", fg="cyan", bold=True))
            user_input = user_input.strip()

            # Skip empty input
            if not user_input:
                click.echo(click.style("  Bot: Please type something. I'm here to help!", fg="green"))
                continue

            # Get bot response
            response, context = get_response(user_input, context)

            # Print bot response with colour
            click.echo(click.style(f"  Bot: {response}", fg="green"))
            click.echo()

            # Exit if farewell detected
            if context.get("should_exit"):
                break

        except click.exceptions.Abort:
            # Handle Ctrl+C gracefully
            click.echo(
                click.style("\n  Bot: Session interrupted. Thanks for visiting ShopEase! 👋", fg="yellow")
            )
            break

    click.echo("\n──────────────────────────────────────────────────────────")
    click.echo("  Session ended. Visit us again at www.shopease.com!")


if __name__ == "__main__":
    chat()
