import click
from services import get_response

@click.command()
def chat():
    """
    Basic E-commerce Chatbot CLI.
    Runs a continuous loop until user types 'exit'.
    """
    click.echo("--------------------------------------------------")
    click.echo(" WELCOME TO BASIC E-COMMERCE CHATBOT (BCA PROJECT)")
    click.echo("--------------------------------------------------")
    click.echo(" Type 'help' for instructions.")
    click.echo(" Type 'exit' to quit.")
    click.echo("--------------------------------------------------")

    while True:
        # Get user input
        try:
            user_input = click.prompt("You", prompt_suffix=" > ")
            user_input = user_input.strip()

            if not user_input:
                continue

            # Process input using services logic
            response = get_response(user_input)

            # Display response
            click.echo(f"Bot > {response}")
            click.echo("") # Newline for readability

            # Handle Exit
            if "Goodbye" in response:
                break

        except (KeyboardInterrupt, click.Abort):
            click.echo("\nSession interrupted. Exiting...")
            break

if __name__ == '__main__':
    chat()
