import base64
import hashlib
import json
import os
import sys

import click
import supernotelib as sn
import yaml
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from supernotelib.converter import ImageConverter, VisibilityOverlay

TO_MARKDOWN_TEMPLATE = """
Convert the following image to markdown format. Incorporate bullet journal
styles to this document. When you encounter a 'dot list' use a markdown
checkbox. Return only markdown (no codeblocks or flavor text before/after the output).
"""

chat = ChatOpenAI(model="gpt-4o")


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def image_to_markdown(path) -> str:
    result = chat.invoke(
        [
            HumanMessage(
                content=[
                    {"type": "text", "text": TO_MARKDOWN_TEMPLATE},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "data:image/png;base64," + encode_image(path)
                        },
                    },
                ]
            )
        ]
    )
    return str(result.content)


def load_notebook(path):
    return sn.load_notebook(path)


def convert_all(converter, total, path, save_func, visibility_overlay):
    file_name = path + "/page.png"
    basename, extension = os.path.splitext(file_name)
    max_digits = len(str(total))
    files = []
    for i in range(total):
        numbered_filename = basename + "_" + str(i).zfill(max_digits) + extension
        img = converter.convert(i, visibility_overlay)
        save_func(img, numbered_filename)
        files.append(numbered_filename)
    return files


def convert_to_png(notebook, path):
    # Compute the hash of the notebook
    notebook_hash = hashlib.sha256(
        json.dumps(notebook.get_metadata().__dict__).encode()
    ).hexdigest()

    # Check if the hash already exists in the metadata
    metadata_path = os.path.join(path, "metadata.yaml")
    if os.path.exists(metadata_path):
        with open(metadata_path, "r") as f:
            metadata = yaml.safe_load(f)
            if (
                "notebook_hash" in metadata
                and metadata["notebook_hash"] == notebook_hash
            ):
                raise ValueError("The notebook hasn't been modified.")
    else:
        # Store the notebook_hash in the metadata
        with open(metadata_path, "w") as f:
            yaml.dump({"notebook_hash": notebook_hash}, f)

    converter = ImageConverter(notebook)
    bg_visibility = VisibilityOverlay.DEFAULT
    vo = sn.converter.build_visibility_overlay(background=bg_visibility)

    def save(img, file_name):
        img.save(file_name, format="PNG")

    return convert_all(converter, notebook.get_total_pages(), path, save, vo)


@click.command()
@click.argument("filename", type=click.Path(readable=True))
@click.option(
    "--output",
    "-o",
    type=click.Path(writable=True),
    help="Output directory for images.",
)
def import_supernote(filename, output):
    # Export images of the note file into a directory with the same basename as the file.
    notebook = load_notebook(filename)
    notebook_name = os.path.splitext(os.path.basename(filename))[0]
    image_output_path = os.path.join(output, notebook_name)
    os.makedirs(image_output_path, exist_ok=True)

    try:
        # the notebook_name is YYYYMMDD_HHMMSS
        year_month_day = (
            f"{notebook_name[:4]}-{notebook_name[4:6]}-{notebook_name[6:8]}"
        )
        # Perform OCR on each page, asking the LLM to generate a markdown file of a specific format.
        markdown = f"""---
created: {year_month_day}
tags: journal/entry, supernote
---

# Text

"""

        pages = convert_to_png(notebook, image_output_path)
        for page in pages:
            markdown = markdown +"\n"+ image_to_markdown(page)

        markdown = markdown + "\n\n# Images\n\n"
        for page in pages:
            markdown = markdown + f"![{page}](file://{os.path.abspath(page)})\n"

        with open(os.path.join(image_output_path, f"{year_month_day}_supernote.md"), "w") as f:
            f.write(markdown)

        print(os.path.join(image_output_path, f"{year_month_day}_supernote.md"))
    except ValueError:
        click.echo("Notebook hasn't been modified.")
        sys.exit(1)


if __name__ == "__main__":
    import_supernote()
