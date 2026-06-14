import base64
from typing import Generator
import uuid
import shutil
import logging
import os
from contextlib import contextmanager
from datetime import datetime

from jinja2 import Template
from supernotelib import Notebook

from sn2md.ai_utils import image_to_markdown, image_to_text
from sn2md.importers.atelier import AtelierExtractor
from sn2md.importers.pdf import PDFExtractor
from sn2md.importers.png import PNGExtractor
from sn2md.types import Config, ImageExtractor
from sn2md.importers.note import NotebookExtractor, convert_binary_to_image
from sn2md.metadata import check_metadata_file, write_metadata_file

from tqdm import tqdm

logger = logging.getLogger(__name__)


@contextmanager
def generate_images(
    image_extractor: ImageExtractor, file_name: str, output: str
) -> Generator[list[str], None, None]:
    image_output_path = os.path.join(output, uuid.uuid4().hex)
    os.makedirs(image_output_path, exist_ok=True)

    logger.debug("Storing images in %s", image_output_path)

    try:
        yield image_extractor.extract_images(file_name, image_output_path)
    finally:
        shutil.rmtree(image_output_path)


def process_pages(pngs: list[str], config: Config, model: str, progress: bool) -> str:
    page_list = tqdm(pngs, desc="Processing pages", unit="page") if progress else pngs
    template_output = ""
    for i, page in enumerate(page_list):
        context = ""
        if i > 0 and len(template_output) > 0:
            # include the last 50 characters...for continuity of the transcription:
            context = template_output[-50:]
        template_output = (
            template_output
            + "\n"
            + image_to_markdown(
                page,
                context,
                config.api_key,
                model,
                config.prompt,
            )
        )
    return template_output


def create_basic_context(file_basename: str, file_name: str) -> dict:
    return {
        "file_basename": file_basename,
        "file_name": file_name,
        "ctime": datetime.fromtimestamp(os.path.getctime(file_name)),
        "mtime": datetime.fromtimestamp(os.path.getmtime(file_name)),
        "year_month_day": datetime.fromtimestamp(os.path.getctime(file_name)).strftime(
            "%Y-%m-%d"
        ),
    }

def create_notebook_context(notebook: Notebook, config: Config, model: str) -> dict:
    # Codes:
    # TODO add a pull request for this feature:
    # https://github.com/jya-dev/supernote-tool/blob/807d5fa4bf524fdb1f9c7f1c67ed66ea96a49db5/supernotelib/fileformat.py#L236
    def get_link_str(type_code: int) -> str:
        if type_code == 0:
            return "page"
        elif type_code == 1:
            return "file"
        elif type_code == 2:
            return "web"

        return "unknown"

    def get_inout_str(type_code: int) -> str:
        if type_code == 0:
            return "out"
        elif type_code == 1:
            return "in"

        return "unknown"

    return {
        "links": [
            {
                "page_number": link.get_page_number(),
                "type": get_link_str(link.get_type()),
                "name": os.path.basename(
                    base64.standard_b64decode(link.get_filepath())
                ).decode("utf-8"),
                "device_path": base64.standard_b64decode(link.get_filepath()),
                "inout": get_inout_str(link.get_inout()),
            }
            for link in (notebook.links if notebook else [])
        ],
        "keywords": [
            {
                "page_number": keyword.get_page_number(),
                "content": keyword.get_content().decode("utf-8"),
            }
            for keyword in (notebook.keywords if notebook else [])
        ],
        "titles": _extract_titles(notebook, config, model),
    }


def _extract_titles(notebook: Notebook | None, config: Config, model: str) -> list[dict]:
    titles = []
    for title in notebook.titles if notebook else []:
        try:
            image = convert_binary_to_image(notebook, title)
        except Exception as e:
            logger.warning(
                "Skipping title on page %s: failed to decode (%s)",
                title.get_page_number(),
                e,
            )
            continue
        titles.append(
            {
                "page_number": title.get_page_number(),
                "content": image_to_text(
                    image,
                    config.api_key,
                    model,
                    config.title_prompt,
                ),
                "level": title.metadata["TITLELEVEL"],
            }
        )
    return titles


def create_context(
    notebook: Notebook | None,
    pngs: list[str],
    config: Config,
    file_name: str,
    model: str,
    template_output: str,
    image_relative_path: str = ".",
) -> dict:
    file_basename = os.path.splitext(os.path.basename(file_name))[0]
    images = [
        {
            "name": os.path.join(image_relative_path, os.path.basename(png_path)) if image_relative_path != "." else os.path.basename(png_path),
            "rel_path": png_path,
            "abs_path": os.path.abspath(png_path),
        }
        for png_path in pngs
    ]

    # TODO add pages - for each page include keywords and titles
    context = {
        "markdown": template_output,
        "llm_output": template_output,
        "images": images,
        **create_basic_context(file_basename, file_name),
    }

    if notebook:
        return {
            **context,
            **create_notebook_context(notebook, config, model),
        }

    return {
        **context,
        "links": [],
        "keywords": [],
        "titles": [],
    }


def generate_output(
    pngs: list[str],
    config: Config,
    context: dict,
    file_name: str,
    output: str,
    template,
    image_full_path: str,
) -> None:
    jinja_markdown = template.render(context)

    output_filename_template = Template(config.output_filename_template)
    output_filename = output_filename_template.render(context)

    output_path_template = Template(config.output_path_template)
    output_path = output_path_template.render(context)
    output_path = os.path.join(output, output_path)
    os.makedirs(output_path, exist_ok=True)

    # Create image directory
    os.makedirs(image_full_path, exist_ok=True)

    output_path_and_file = os.path.join(output_path, output_filename)
    with open(output_path_and_file, "w") as f:
        _ = f.write(jinja_markdown)
    logger.debug("Wrote output to %s", output_path_and_file)

    # Move images to the configured image directory
    for png_path in pngs:
        png_name = os.path.basename(png_path)
        os.rename(png_path, os.path.join(image_full_path, png_name))

    write_metadata_file(file_name, output_path_and_file)

    logger.debug("Moved images to %s", image_full_path)

    print(output_path_and_file)


def verify_metadata_file(config: Config, output: str, file_name: str) -> None:
    file_basename = os.path.splitext(os.path.basename(file_name))[0]
    basic_context = create_basic_context(file_basename, file_name)

    output_path_template = Template(config.output_path_template)
    output_path = output_path_template.render(basic_context)
    output_path = os.path.join(output, output_path)

    check_metadata_file(output_path, file_name)


def import_supernote_file_core(
    image_extractor: ImageExtractor,
    file_name: str,
    output: str,
    config: Config,
    force: bool = False,
    progress: bool = False,
    model: str | None = None,
) -> None:
    logger.debug("import_supernote_file_core: %s", file_name)
    if not force:
        verify_metadata_file(config, output, file_name)

    model = model if model else config.model
    template = Template(config.template)

    with generate_images(image_extractor, file_name, output) as pngs:
        template_output = process_pages(pngs, config, model, progress)

        notebook = image_extractor.get_notebook(file_name)

        # Calculate paths early for context
        file_basename = os.path.splitext(os.path.basename(file_name))[0]
        basic_context = create_basic_context(file_basename, file_name)

        # Render output path and image path independently
        output_path_template = Template(config.output_path_template)
        output_path_rendered = output_path_template.render(basic_context)
        output_path_full = os.path.join(output, output_path_rendered)

        image_output_path_template = Template(config.image_output_path_template)
        image_path_rendered = image_output_path_template.render(basic_context)
        image_path_full = os.path.join(output, image_path_rendered)

        # Calculate relative path from output directory to image directory
        image_relative_path = os.path.relpath(image_path_full, output_path_full)

        context = create_context(
            notebook, pngs, config, file_name, model, template_output, image_relative_path
        )

        generate_output(pngs, config, context, file_name, output, template, image_path_full)


def import_supernote_directory_core(
    directory: str,
    output: str,
    config: Config,
    force: bool = False,
    progress: bool = False,
    model: str | None = None,
) -> None:
    for root, _, files in os.walk(directory):
        file_list = (
            tqdm(files, desc="Processing files", unit="file") if progress else files
        )
        for file in file_list:
            filename = os.path.join(root, file)
            try:
                if file.lower().endswith(".note"):
                    import_supernote_file_core(
                        NotebookExtractor(),
                        filename,
                        output,
                        config,
                        force,
                        progress,
                        model,
                    )
                if file.lower().endswith(".pdf"):
                    import_supernote_file_core(
                        PDFExtractor(), filename, output, config, force, progress, model
                    )
                if file.lower().endswith(".png"):
                    import_supernote_file_core(
                        PNGExtractor(), filename, output, config, force, progress, model
                    )
                if file.lower().endswith(".spd"):
                    import_supernote_file_core(
                        AtelierExtractor(),
                        filename,
                        output,
                        config,
                        force,
                        progress,
                        model,
                    )
            except ValueError as e:
                logger.debug(f"Skipping {filename}: {e}")
