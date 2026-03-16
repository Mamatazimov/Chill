import click

from chill import Chill

chill = Chill()


@click.group(invoke_without_command=True)
@click.option("-p", "--path", default=".", help="Proyekt joylashgan yo'l")
@click.pass_context
def cli(ctx, path):
    """
    Bu buyruq "NEW PROJECT"ni optimallashtiradi.
    """
    if ctx.invoked_subcommand is None:
        chill.chill(path)
    else:
        ctx.ensure_object(dict)
        ctx.obj["path"] = path


@cli.command()
@click.argument("comment", default="")
@click.pass_context
def save(ctx, comment):
    """
    This command saves your current Projects new version.
    """
    path = ctx.obj["path"]
    chill.save(comment, path)


@cli.command()
@click.argument("id", default=-1)
@click.pass_context
def back(ctx, id):
    """
    This command builds old version save.
    This works based on the entered id, if it is not entered one previous save id will be used.
    """
    path = ctx.obj["path"]
    chill.back(id, path)


@cli.command()
@click.pass_context
def list(ctx):
    """
    This command shows current Project's all flows and saves.
    """
    path = ctx.obj["path"]
    chill.list(path)


@cli.command()
@click.argument("flow_name")
@click.pass_context
def flow(ctx, flow_name):
    """
    This command create new flow.
    If it alredy exist then activate this flow.
    """
    path = ctx.obj["path"]
    chill.flow(path=path, flow_name=flow_name)


@cli.command()
def gui(comment):
    """
    This command starts terminal gui app.
    """
    pass


if __name__ == "__main__":
    cli()
    chill.db.close()
