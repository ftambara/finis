import click
from rich.console import Console
from rich.table import Table

from accounts.models import Organization, SpendingTier

console = Console()

@click.group(name="organizations")
def organizations() -> None:
    """Manage Organizations."""
    pass

@organizations.command(name="list")
def list_orgs() -> None:
    """List all organizations."""
    orgs_qs = Organization.objects.all().select_related("spending_tier").order_by("id")
    
    if not orgs_qs.exists():
        console.print("[yellow]No organizations found.[/yellow]")
        return

    table = Table(title="Organizations")
    table.add_column("ID", justify="right", style="cyan", no_wrap=True)
    table.add_column("Name", style="magenta")
    table.add_column("Spending Tier", style="green")
    table.add_column("Created At", style="blue")

    for org in orgs_qs:
        table.add_row(
            str(org.id),
            org.name,
            org.spending_tier.name,
            org.created_at.strftime("%Y-%m-%d %H:%M:%S")
        )

    console.print(table)

@organizations.command(name="create")
@click.option("--name", required=True, help="Name of the organization.")
@click.option("--tier", required=True, help="ID or name of the spending tier.")
def create_org(name: str, tier: str) -> None:
    """Create a new organization."""
    if Organization.objects.filter(name=name).exists():
        console.print(f"[red]Error: Organization with name '{name}' already exists.[/red]")
        return

    tier_obj = _find_tier(tier)
    if not tier_obj:
        return

    org = Organization.objects.create(name=name, spending_tier=tier_obj)
    console.print(f"[green]Successfully created organization: {org.name} (ID: {org.id})[/green]")

@organizations.command(name="update")
@click.argument("identifier")
@click.option("--name", help="New name for the organization.")
@click.option("--tier", help="New tier (ID or Name) for the organization.")
def update_org(identifier: str, name: str | None, tier: str | None) -> None:
    """Update an organization. IDENTIFIER can be ID or Name."""
    org = _find_org(identifier)
    if not org:
        return

    if name:
        org.name = name
    if tier:
        tier_obj = _find_tier(tier)
        if tier_obj:
            org.spending_tier = tier_obj
        else:
            return

    org.save()
    console.print(f"[green]Successfully updated organization {identifier}.[/green]")

@organizations.command(name="delete")
@click.argument("identifier")
@click.option("--yes", is_flag=True, help="Skip confirmation.")
def delete_org(identifier: str, yes: bool) -> None:
    """Delete an organization. IDENTIFIER can be ID or Name."""
    org = _find_org(identifier)
    if not org:
        return

    if not yes and not click.confirm(f"Are you sure you want to delete organization '{org.name}'?"):
        return

    try:
        org.delete()
        console.print(f"[green]Successfully deleted organization '{identifier}'.[/green]")
    except Exception as e:
        console.print(f"[red]Error deleting organization: {e}[/red]")

def _find_org(identifier: str) -> Organization | None:
    """Helper to find an organization by ID or Name."""
    try:
        if identifier.isdigit():
            return Organization.objects.get(id=int(identifier))
        return Organization.objects.get(name=identifier)
    except Organization.DoesNotExist:
        console.print(f"[red]Error: Organization with identifier '{identifier}' not found.[/red]")
        return None

def _find_tier(identifier: str) -> SpendingTier | None:
    """Helper to find a tier by ID or Name."""
    try:
        if identifier.isdigit():
            return SpendingTier.objects.get(id=int(identifier))
        return SpendingTier.objects.get(name=identifier)
    except SpendingTier.DoesNotExist:
        console.print(f"[red]Error: Tier with identifier '{identifier}' not found.[/red]")
        return None
