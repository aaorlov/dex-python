import typer
from rich.console import Console

from dex_cli.commands import account, auth
from dex_cli.commands.account import prompt_account
from dex_cli.config import ACCOUNTS, add_account

app = typer.Typer(
	name="dex",
	help="Dex — multi-account CLI toolkit.",
	no_args_is_help=True,
	rich_markup_mode="rich",
)
app.add_typer(auth.app, name="auth")
app.add_typer(account.app, name="account")

console = Console()

@app.command()
def init() -> None:
	"""[bold green]Initialize[/] dex by adding your first account."""
	if ACCOUNTS:
		console.print("  [dim]Already initialized. Use [bold]dex account add[/] to add more accounts.[/]")
		return
	console.print("[bold cyan]Welcome to dex![/] Let's set up your first account.\n")
	config = prompt_account()
	add_account(config)
	console.print(f"\n  [green]✓[/] Account [bold]{config.alias}[/] saved to ~/.config/dex/accounts.json")


@app.callback()
def main(
	verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output."),
) -> None:
	"""[bold cyan]dex[/] — multi-account CLI toolkit."""
	if verbose:
		import logging

		logging.basicConfig(level=logging.DEBUG)
