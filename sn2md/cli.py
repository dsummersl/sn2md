import sys

import click

from .importer import import_supernote_file_core, import_supernote_directory_core

@click.group()
def cli():
    pass


@cli.command(name="file")
@click.argument("filename", type=click.Path(readable=True))
@click.option(
    "--template",
    "-t",
    type=click.Path(readable=True),
    default=None,
    help="Path to a custom markdown template file.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(writable=True),
    default="supernote",
    help="Output directory for images.",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force reprocessing even if the notebook hasn't changed.",
)
def import_supernote_file(
    filename: str, output: str, template: str, force: bool
) -> None:
    try:
        import_supernote_file_core(filename, output, template, force)
    except ValueError:
        print("Notebook already processed")
        sys.exit(1)


@cli.command(name="directory")
@click.argument("directory", type=click.Path(readable=True))
@click.option(
    "--template",
    "-t",
    type=click.Path(readable=True),
    default=None,
    help="Path to a custom markdown template file.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(writable=True),
    default="supernote",
    help="Output directory for images and files.",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force reprocessing even if the notebook hasn't changed.",
)
def import_supernote_directory(
    directory: str, output: str, template: str, force: bool
) -> None:
    import_supernote_directory_core(directory, output, template, force)


if __name__ == "__main__":
    cli()
