# Supernote to Markdown converter (sn2md)

**sn2md** is a command-line tool to convert Supernote `.note` files into markdown. It leverages OpenAI GPT-4o to convert images and text from Supernote files into a structured markdown document.

## Features

- Converts Supernote `.note` files to markdown.
- Supports conversion of images to markdown using the Mermaid diagramming tool.
- Automatically handles math equations using `$` and `$$` style math blocks.
- Generates a markdown file with metadata and embedded images.

## Installation

```sh
pip install sn2md
```

Setup your **OPENAI_API_KEY** environment variable.

## Development

```sh
git clone https://github.com/yourusername/supernote-importer.git
cd supernote-importer
poetry install
```

## Usage

To import a single Supernote `.note` file, use the `file` command:

```sh
# import one .note file:
sn2md file <path_to_note_file> --output <output_directory>

# import a directory of .note files:
sn2md directory <path_to_directory> --output <output_directory>
```

Notes:
- A cache file is also generated, so repeated runs don't recreate the same data.
  You can force a refresh by running with the `--force` flag.


## Custom Templates

You can provide your own [jinja template](https://jinja.palletsprojects.com/en/3.1.x/templates/#synopsis), if you prefer to customize the markdown
output. The default template is:

```md
---
created: {{year_month_day}}
tags: supernote
---

{{markdown}}

# Images
{% for image in images %}
- ![{{ image.name }}]({{image.name}})
{% endfor %}
```

Variables supplied to the template:
- `year_month_day`: The date the note was created (eg, 2024-05-12).
- `markdown`: The markdown content of the note.
- `images`: an array of image objects with the following properties:
  - `name`: The name of the image file.
  - `rel_path`: The relative path to the image file to where the file was run
    from.
  - `abs_path`: The absolute path to the image file.


## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [Supernote](https://www.supernote.com/) for their amazing note-taking devices.
- [LangChain](https://github.com/langchain/langchain) for providing the core libraries used in this project.
- [OpenAI](https://www.openai.com/) for the GPT-4 model.
