import click
from rich.console import Console
from rich.table import Table

from accounts.models import Organization, User

console = Console()


@click.group(name="users")
def users() -> None:
    """Manage Users."""
    pass


@users.command(name="list")
@click.option("--org", help="Filter by organization (ID or Name).")
def list_users(org: str | None) -> None:
    """List all users."""
    users_qs = User.objects.all().select_related("organization").order_by("id")

    if org:
        org_obj = _find_org(org)
        if org_obj:
            users_qs = users_qs.filter(organization=org_obj)
        else:
            return

    if not users_qs.exists():
        console.print("[yellow]No users found.[/yellow]")
        return

    table = Table(title="Users")
    table.add_column("ID", justify="right", style="cyan", no_wrap=True)
    table.add_column("Email", style="green")
    table.add_column("Organization", style="blue")
    table.add_column("Created At", style="blue")

    for user in users_qs:
        table.add_row(
            str(user.id),
            user.email,
            user.organization.name,
            user.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        )

    console.print(table)


@users.command(name="create")
@click.option("--email", required=True, help="Email of the user.")
@click.option(
    "--password",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    help="Password of the user.",
)
@click.option("--org", required=True, help="ID or name of the organization.")
def create_user(email: str, password: str, org: str) -> None:
    """Create a new user."""
    if User.objects.filter(email=email).exists():
        console.print(f"[red]Error: User with email '{email}' already exists.[/red]")
        return

    org_obj = _find_org(org)
    if not org_obj:
        return

    user = User.objects.create_user(email=email, password=password, organization=org_obj)
    console.print(f"[green]Successfully created user: {user.email} (ID: {user.id})[/green]")


@users.command(name="update")
@click.argument("identifier")
@click.option("--email", help="New email for the user.")
@click.option("--org", help="New organization (ID or Name) for the user.")
@click.option("--password", help="New password for the user.")
def update_user(identifier: str, email: str | None, org: str | None, password: str | None) -> None:
    """Update a user. IDENTIFIER can be ID or Email."""
    user = _find_user(identifier)
    if not user:
        return

    if email:
        user.email = email
    if org:
        org_obj = _find_org(org)
        if org_obj:
            user.organization = org_obj
        else:
            return
    if password:
        user.set_password(password)

    user.save()
    console.print(f"[green]Successfully updated user {identifier}.[/green]")


@users.command(name="delete")
@click.argument("identifier")
@click.option("--yes", is_flag=True, help="Skip confirmation.")
def delete_user(identifier: str, yes: bool) -> None:
    """Delete a user. IDENTIFIER can be ID or Email."""
    user = _find_user(identifier)
    if not user:
        return

    if not yes and not click.confirm(f"Are you sure you want to delete user '{user.email}'?"):
        return

    try:
        user.delete()
        console.print(f"[green]Successfully deleted user '{identifier}'.[/green]")
    except Exception as e:
        console.print(f"[red]Error deleting user: {e}[/red]")


def _find_user(identifier: str) -> User | None:
    """Helper to find a user by ID or Email."""
    try:
        if identifier.isdigit():
            return User.objects.get(id=int(identifier))
        return User.objects.get(email=identifier)
    except User.DoesNotExist:
        console.print(f"[red]Error: User with identifier '{identifier}' not found.[/red]")
        return None


def _find_org(identifier: str) -> Organization | None:
    """Helper to find an organization by ID or Name."""
    try:
        if identifier.isdigit():
            return Organization.objects.get(id=int(identifier))
        return Organization.objects.get(name=identifier)
    except Organization.DoesNotExist:
        console.print(f"[red]Error: Organization with identifier '{identifier}' not found.[/red]")
        return None
