import hashlib
import os

import yaml
from jinja2 import Template

from .langchain_utils import image_to_markdown
from .supernote_utils import convert_notebook_to_pngs, load_notebook

DEFAULT_MD_TEMPLATE = """---
created: {{year_month_day}}
tags: supernote
---

{{markdown}}

# Images
{% for image in images %}
- ![{{ image.name }}]({{image.name}})
{% endfor %}
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
    filename: str, output: str, template_path: str | None = None, force: bool = False
) -> None:
    global DEFAULT_MD_TEMPLATE
    template = DEFAULT_MD_TEMPLATE

    if template_path:
        with open(template_path, "r") as template_file:
            template = template_file.read()

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
        markdown = markdown + "\n" + image_to_markdown(page, context)

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

    jinja_markdown = jinja_template.render(
        year_month_day=year_month_day, markdown=markdown, images=images
    )

    with open(os.path.join(image_output_path, f"{notebook_name}.md"), "w") as f:
        _ = f.write(jinja_markdown)

    print(os.path.join(image_output_path, f"{notebook_name}.md"))


def import_supernote_directory_core(
    directory: str, output: str, template_path: str | None = None, force: bool = False
) -> None:
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".note"):
                filename = os.path.join(root, file)
                try:
                    import_supernote_file_core(filename, output, template_path, force)
                except ValueError as e:
                    print(f"Skipping {filename}: {e}")
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".note"):
                filename = os.path.join(root, file)
                try:
                    import_supernote_file_core(filename, output, template_path, force)
                except ValueError as e:
                    print(f"Skipping {filename}: {e}")
