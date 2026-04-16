import questionary
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from dex_cli.config import ACCOUNTS, AccountConfig, add_account, remove_account

app = typer.Typer(
  help="[bold yellow]Account[/] — manage configured accounts.",
  rich_markup_mode="rich",
)
console = Console()


@app.command("add")
def add() -> None:
  """[bold green]Add[/] a new account interactively."""
  config = prompt_account()
  add_account(config)
  console.print(f"\n  [green]✓[/] Account [bold]{config.alias}[/] added.")


@app.command("list")
def list_accounts() -> None:
  """[bold cyan]List[/] all configured accounts."""
  if not ACCOUNTS:
    console.print("  [dim]No accounts configured. Run [bold]dex init[/] or [bold]dex account add[/].[/]")
    return
  table = Table(title="Configured Accounts", title_style="bold cyan", show_lines=False)
  table.add_column("Alias", style="bold white")
  table.add_column("Name", style="dim")
  table.add_column("API URL", style="dim")
  for cfg in ACCOUNTS.values():
    table.add_row(cfg.alias, cfg.name, cfg.api_url)
  console.print(Panel(table, border_style="cyan", padding=(1, 2)))


@app.command("remove")
def remove(
  alias: str = typer.Argument(help="Alias of the account to remove."),
) -> None:
  """[bold red]Remove[/] an account by alias."""
  remove_account(alias)
  console.print(f"  [green]✓[/] Account [bold]{alias}[/] removed.")


def prompt_account() -> AccountConfig:
  """Interactively prompt for all account fields."""
  name = questionary.text("Account name (e.g. Rivian-VW JV):").unsafe_ask()
  alias = questionary.text("Alias (short identifier, e.g. rivw):").unsafe_ask()
  api_url = questionary.text("API URL:").unsafe_ask()
  config_url = questionary.text("Config URL (cli-config.json):").unsafe_ask()
  cognito_domain = questionary.text("Cognito domain:").unsafe_ask()

  return AccountConfig(
    name=name,
    alias=alias,
    api_url=api_url.rstrip("/"),
    config_url=config_url,
    cognito_domain=cognito_domain
  )
