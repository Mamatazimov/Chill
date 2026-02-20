import click

from chill import Chill
from chill_init import chill_init


@click.group()
def cli():
    """Chill bu oddiy papka versiya manageri!"""
    pass


@cli.command()
@click.argument("path", default=".")
@click.argument("version", default="default")
def save(path, version):
    """Faylni versiyasi asosida saqlash"""
    click.echo(f"Saqlanmoqda: {path} (Versiya: {version})")
    Chill.save_version(version, False, path)


@cli.command()
@click.argument("path", default=".")
@click.argument("version", default="default")
def init(path, version):
    """Belgilangan versiya asosida faylni moslash"""
    click.echo(f"Tiklanmoqda: {path} (Versiya: {version})")
    Chill.save_version(version, True, path)


@cli.command()
def list():
    """Barcha loyhalarni olish"""
    Chill.get_saves()


@cli.command()
@click.argument("project")
def version(project):
    """Berilgan Loyha asosida versiyalarni"""
    Chill.get_versions(project)


if __name__ == "__main__":
    chill_init()
    cli()
