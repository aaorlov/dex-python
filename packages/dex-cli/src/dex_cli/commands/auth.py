from typing import Any

import questionary
import typer
from rich.console import Console

from dex_cli.config import ACCOUNTS
from dex_cli.services.aws_access_manager import ApprovalsService, AuthService


app = typer.Typer(
	help="[bold yellow]Authentication[/] — login and manage account sessions.",
	rich_markup_mode="rich",
)
console = Console()

DEFAULT_TICKET_NUMBER = "N/A"


def _default_alias() -> str:
	"""Return the first configured account alias, or prompt to init."""
	if not ACCOUNTS:
		console.print("[red]No accounts configured.[/] Run [bold]dex init[/] first.")
		raise typer.Exit(1)
	return next(iter(ACCOUNTS))


@app.command()
def login(
	account: str = typer.Option(
		"",
		"--account",
		"-a",
		help="Account alias to authenticate. Defaults to the first configured account.",
	),
	ticket_number: str = typer.Option(
		DEFAULT_TICKET_NUMBER,
		"--ticket-number",
		"-t",
		help="Ticket number to use for the request.",
	),
) -> None:
	"""[bold green]Login[/] to an account and list pre-approvals.

	Authenticate via Cognito OAuth2 PKCE, then fetch and display
	your pre-approvals.

	[dim]Examples:[/]
	  dex auth login
	  dex auth login -a rivw
	  dex auth login -t 123456
	  dex auth login -a rivw -t 123456
	"""
	if not account:
		account = _default_alias()
	auth_service = AuthService()
	tokens, from_cache = auth_service.login(account)

	if from_cache:
		console.print(f"  [green]✓[/] [bold]{account}[/] — using cached session")
	else:
		console.print(f"  [green]✓[/] [bold]{account}[/] — authenticated")
	console.print()

	approvals_service = ApprovalsService(tokens.id_token, account)
	with console.status("[bold yellow]Fetching pre-approvals…[/]"):
		choices = approvals_service.list_preapproval_choices()

	if not choices:
		console.print("\n  [dim]No pre-approvals found.[/]")
		return

	selected = _select_preapprovals(choices)
	if selected:
		console.print(f"\n  [bold]Selected {len(selected)} pre-approval(s):[/]")
		for choice in selected:
			acct = choice.get("account", {}).get("name", choice.get("accountId", ""))
			ps = choice.get("permissionSet", {}).get("name", "")
			new_request = approvals_service.create_request(choice, ticket_number=ticket_number)
			console.print(f"    [cyan]•[/] {acct} / {ps} (status: {new_request.get("status", "N/A")})")
	else:
		console.print("\n  [dim]No items selected.[/]")


def _select_preapprovals(choices_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
	choices: list[questionary.Choice] = []
	for entry in choices_data:
		choices.append(questionary.Choice(
			title=entry["label"],
			value=entry["item"],
			disabled="already active" if entry["is_active"] else None,
			checked=entry.get("is_preselected", False),
		))

	selected = questionary.checkbox(
		"Select pre-approvals to request approve:",
		choices=choices,
	).ask()

	return selected or []


