import hashlib
import logging
import base64
import os

import yaml
from jinja2 import Template

from .types import Config
from .ai_utils import image_to_markdown, image_to_text
from .supernote_utils import convert_notebook_to_pngs, convert_binary_to_image, load_notebook

logger = logging.getLogger(__name__)


DEFAULT_MD_TEMPLATE = """---
created: {{year_month_day}}
tags: supernote
---

{{markdown}}

# Images
{% for image in images %}
- ![{{ image.name }}]({{image.name}})
{%- endfor %}

# Keywords
{% for keyword in keywords %}
- Page {{ keyword.page_number }}: {{ keyword.content }}
{%- endfor %}

# Links
{% for link in links %}
- Page {{ link.page_number }}: {{ link.type }} {{ link.inout }} {{ link.name }}
{%- endfor %}

# Titles
{% for title in titles %}
- Page {{ title.page_number }}: Level {{ title.level }} "{{ title.content }}"
{%- endfor %}
"""


def compute_and_check_notebook_hash(notebook_path: str, output_path: str) -> None:
    # Compute the hash of the notebook file itself using SHA-1 (same as shasum)
    with open(notebook_path, "rb") as f:
        notebook_hash = hashlib.sha1(f.read()).hexdigest()

    # Check if the hash already exists in the metadata
    metadata_path = os.path.join(output_path, ".sn2md.metadata.yaml")
    if os.path.exists(metadata_path):
        with open(metadata_path, "r") as f:
            metadata = yaml.safe_load(f)
            if (
                "notebook_hash" in metadata
                and metadata["notebook_hash"] == notebook_hash
            ):
                raise ValueError("The notebook hasn't been modified.")

    # Store the notebook_hash in the metadata
    with open(metadata_path, "w") as f:
        yaml.dump({"notebook_hash": notebook_hash, "notebook": notebook_path}, f)


def import_supernote_file_core(
    filename: str, output: str, config: Config, force: bool = False
) -> None:
    global DEFAULT_MD_TEMPLATE
    template = DEFAULT_MD_TEMPLATE

    if config['template']:
        template = config['template']

    jinja_template = Template(template)

    # Export images of the note file into a directory with the same basename as the file.
    notebook = load_notebook(filename)

    notebook_name = os.path.splitext(os.path.basename(filename))[0]
    image_output_path = os.path.join(output, notebook_name)
    os.makedirs(image_output_path, exist_ok=True)
    try:
        compute_and_check_notebook_hash(filename, image_output_path)
    except ValueError as e:
        if not force:
            raise e
        else:
            print(f"Reprocessing {filename}")

    # the notebook_name is YYYYMMDD_HHMMSS
    year_month_day = f"{notebook_name[:4]}-{notebook_name[4:6]}-{notebook_name[6:8]}"
    # Perform OCR on each page, asking the LLM to generate a markdown file of a specific format.

    pngs = convert_notebook_to_pngs(notebook, image_output_path)
    markdown = ""
    for i, page in enumerate(pngs):
        context = ""
        if i > 0 and len(markdown) > 0:
            # include the last 50 characters...
            context = markdown[-50:]
        markdown = markdown + "\n" + image_to_markdown(
            page,
            context,
            config['openai_api_key'],
            config['model'],
            config['prompt'],
        )

    images = [
        {
            "name": f"{notebook_name}_{i}.png",
            "rel_path": os.path.join(image_output_path, f"{notebook_name}_{i}.png"),
            "abs_path": os.path.abspath(
                os.path.join(image_output_path, f"{notebook_name}_{i}.png")
            ),
        }
        for i in range(len(pngs))
    ]

    # Codes:
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

    jinja_markdown = jinja_template.render(
        year_month_day=year_month_day, markdown=markdown, images=images,
        links=[{
            'page_number': link.get_page_number(),
            'type': get_link_str(link.get_type()),
            'name': os.path.basename(base64.standard_b64decode(link.get_filepath())).decode('utf-8'),
            'device_path': base64.standard_b64decode(link.get_filepath()),
            'inout': get_inout_str(link.get_inout())
        } for link in notebook.links],
        keywords=[{
            'page_number': keyword.get_page_number(),
            'content': keyword.get_content().decode('utf-8')
        } for keyword in notebook.keywords],
        titles=[{
            'page_number': title.get_page_number(),
            'content': image_to_text(
                convert_binary_to_image(notebook, title),
                config['openai_api_key'],
                config['model']
            ),
            'level': title.metadata['TITLELEVEL']
        } for title in notebook.titles]
    )

    with open(os.path.join(image_output_path, f"{notebook_name}.md"), "w") as f:
        _ = f.write(jinja_markdown)

    print(os.path.join(image_output_path, f"{notebook_name}.md"))


def import_supernote_directory_core(
    directory: str, output: str, config: Config, force: bool = False
) -> None:
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".note"):
                filename = os.path.join(root, file)
                try:
                    import_supernote_file_core(filename, output, config, force)
                except ValueError as e:
                    logger.debug(f"Skipping {filename}: {e}")
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".note"):
                filename = os.path.join(root, file)
                try:
                    import_supernote_file_core(filename, output, config, force)
                except ValueError as e:
                    logger.debug(f"Skipping {filename}: {e}")
