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

### Import a Single Supernote File

To import a single Supernote `.note` file, use the `file` command:

```sh
poetry run python import_supernote.py file <path_to_note_file> --output <output_directory>
```

- `<path_to_note_file>`: Path to the Supernote `.note` file.
- `<output_directory>`: Directory where the output markdown and images will be saved.

### Import a Directory of Supernote Files

To import all Supernote `.note` files in a directory, use the `directory` command:

```sh
poetry run python import_supernote.py directory <path_to_directory> --output <output_directory>
```

- `<path_to_directory>`: Path to the directory containing Supernote `.note` files.
- `<output_directory>`: Directory where the output markdown and images will be saved.

## Example

```sh
poetry run python import_supernote.py file example.note --output output
```

This will convert `example.note` to a markdown file and save it in the `output` directory.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [Supernote](https://www.supernote.com/) for their amazing note-taking devices.
- [LangChain](https://github.com/langchain/langchain) for providing the core libraries used in this project.
- [OpenAI](https://www.openai.com/) for the GPT-4 model.
