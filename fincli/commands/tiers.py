import click
from rich.console import Console
from rich.table import Table

from accounts.models import SpendingTier

console = Console()

@click.group(name="tiers")
def tiers() -> None:
    """Manage Spending Tiers."""
    pass

@tiers.command(name="list")
def list_tiers() -> None:
    """List all spending tiers."""
    tiers_qs = SpendingTier.objects.all().order_by("id")
    
    if not tiers_qs.exists():
        console.print("[yellow]No tiers found.[/yellow]")
        return

    table = Table(title="Spending Tiers")
    table.add_column("ID", justify="right", style="cyan", no_wrap=True)
    table.add_column("Name", style="magenta")
    table.add_column("Token Limit", justify="right", style="green")
    table.add_column("Created At", style="blue")

    for tier in tiers_qs:
        table.add_row(
            str(tier.id),
            tier.name,
            str(tier.token_limit),
            tier.created_at.strftime("%Y-%m-%d %H:%M:%S")
        )

    console.print(table)

@tiers.command(name="create")
@click.option("--name", required=True, help="Name of the tier.")
@click.option("--token-limit", required=True, type=int, help="Token limit for the tier.")
def create_tier(name: str, token_limit: int) -> None:
    """Create a new spending tier."""
    if SpendingTier.objects.filter(name=name).exists():
        console.print(f"[red]Error: Tier with name '{name}' already exists.[/red]")
        return

    tier = SpendingTier.objects.create(name=name, token_limit=token_limit)
    console.print(f"[green]Successfully created tier: {tier.name} (ID: {tier.id})[/green]")

@tiers.command(name="update")
@click.argument("identifier")
@click.option("--name", help="New name for the tier.")
@click.option("--token-limit", type=int, help="New token limit for the tier.")
def update_tier(identifier: str, name: str | None, token_limit: int | None) -> None:
    """Update an existing tier. IDENTIFIER can be ID or Name."""
    tier = _find_tier(identifier)
    if not tier:
        return

    if name:
        tier.name = name
    if token_limit is not None:
        tier.token_limit = token_limit
    
    tier.save()
    console.print(f"[green]Successfully updated tier {identifier}.[/green]")

@tiers.command(name="delete")
@click.argument("identifier")
@click.option("--yes", is_flag=True, help="Skip confirmation.")
def delete_tier(identifier: str, yes: bool) -> None:
    """Delete a tier. IDENTIFIER can be ID or Name."""
    tier = _find_tier(identifier)
    if not tier:
        return

    if not yes and not click.confirm(f"Are you sure you want to delete tier '{tier.name}'?"):
        return

    try:
        tier.delete()
        console.print(f"[green]Successfully deleted tier '{identifier}'.[/green]")
    except Exception as e:
        console.print(f"[red]Error deleting tier: {e}[/red]")

def _find_tier(identifier: str) -> SpendingTier | None:
    """Helper to find a tier by ID or Name."""
    try:
        if identifier.isdigit():
            return SpendingTier.objects.get(id=int(identifier))
        return SpendingTier.objects.get(name=identifier)
    except SpendingTier.DoesNotExist:
        console.print(f"[red]Error: Tier with identifier '{identifier}' not found.[/red]")
        return None
