import click

from fincli.commands.organizations import organizations
from fincli.commands.tiers import tiers
from fincli.commands.users import users


@click.group()
def cli() -> None:
    """Finis CLI - Admin management tool."""
    pass

cli.add_command(tiers)
cli.add_command(organizations)
cli.add_command(users)
