import os
import logging
import sys
import tomllib

import click
from platformdirs import user_config_dir

from .importer import (DEFAULT_MD_TEMPLATE, import_supernote_directory_core,
                       import_supernote_file_core, logger as importer_logger)
from .ai_utils import TO_MARKDOWN_TEMPLATE, TO_TEXT_TEMPLATE
from .types import Config

logger = logging.getLogger(__name__)


def setup_logging(level):
    logging.basicConfig(level=level)
    logger.setLevel(level)
    importer_logger.setLevel(level)
    logger.debug(f"Logging level: {level}")


def get_config(config_file: str) -> Config:
    defaults: Config = {
        "prompt": TO_MARKDOWN_TEMPLATE,
        "title_prompt": TO_TEXT_TEMPLATE,
        "template": DEFAULT_MD_TEMPLATE,
        "model": "gpt-4o-mini",
        "openai_api_key": os.environ.get("OPENAI_API_KEY"),
    }
    try:
        with open(config_file, "rb") as f:
            return {
                **defaults,
                **tomllib.load(f)
            }
    except FileNotFoundError:
        print(f"No config file found at {config_file}, using defaults", file=sys.stderr)

    return defaults


@click.group()
@click.option(
    "--config",
    "-c",
    type=click.Path(dir_okay=False),
    default=user_config_dir() + "/sn2md.toml",
    help="Path to a sn2md configuration",
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
@click.option(
    "--level",
    "-l",
    default="WARNING",
    help="Set the logging level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL)",
)
@click.pass_context
def cli(ctx, config, output, force, level):
    ctx.obj = {}
    ctx.obj["config"] = get_config(config)
    ctx.obj["output"] = output
    ctx.obj["force"] = force
    ctx.obj["level"] = level
    setup_logging(level)


@cli.command(name="file")
@click.argument("filename", type=click.Path(readable=True, dir_okay=False))
@click.pass_context
def import_supernote_file(ctx, filename: str) -> None:
    config = ctx.obj["config"]
    output = ctx.obj["output"]
    force = ctx.obj["force"]
    try:
        import_supernote_file_core(filename, output, config, force)
    except ValueError:
        print("Notebook already processed")
        sys.exit(1)


@cli.command(name="directory")
@click.argument("directory", type=click.Path(readable=True, file_okay=False))
@click.pass_context
def import_supernote_directory(ctx, directory: str) -> None:
    config = ctx.obj["config"]
    output = ctx.obj["output"]
    force = ctx.obj["force"]
    import_supernote_directory_core(directory, output, config, force)


if __name__ == "__main__":
    cli()
