import os
import pytest
import tempfile
import yaml
from unittest.mock import patch, mock_open

from sn2md.importer import (
    compute_and_check_notebook_hash,
    import_supernote_file_core,
    import_supernote_directory_core,
)

# Mock functions from other modules
from sn2md.supernote_utils import load_notebook, convert_notebook_to_pngs
from sn2md.langchain_utils import image_to_markdown

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname

def test_compute_and_check_notebook_hash(temp_dir):
    notebook_path = os.path.join(temp_dir, "test.note")
    metadata_path = os.path.join(temp_dir, ".sn2md.metadata.yaml")

    with open(notebook_path, "w") as f:
        f.write("test content")

    compute_and_check_notebook_hash(notebook_path, temp_dir)

    with open(metadata_path, "r") as f:
        metadata = yaml.safe_load(f)
        assert "notebook_hash" in metadata
        assert metadata["notebook"] == notebook_path

    with pytest.raises(ValueError, match="The notebook hasn't been modified."):
        compute_and_check_notebook_hash(notebook_path, temp_dir)

def test_import_supernote_file_core(temp_dir):
    filename = os.path.join(temp_dir, "test.note")
    output = temp_dir
    template_path = None

    with open(filename, "w") as f:
        f.write("test content")

    with patch("sn2md.importer.compute_and_check_notebook_hash") as mock_hash, \
         patch("sn2md.importer.load_notebook") as mock_load, \
         patch("sn2md.importer.convert_notebook_to_pngs") as mock_convert, \
         patch("sn2md.importer.image_to_markdown") as mock_image_to_md, \
         patch("builtins.open", mock_open()) as mock_file:

        mock_load.return_value = "mock_notebook"
        mock_convert.return_value = ["page1.png", "page2.png"]
        mock_image_to_md.side_effect = ["markdown1", "markdown2"]

        import_supernote_file_core(filename, output, template_path, force=True)

        mock_hash.assert_called_once_with(filename, os.path.join(output, "test"))
        mock_load.assert_called_once_with(filename)
        mock_convert.assert_called_once_with("mock_notebook", os.path.join(output, "test"))
        assert mock_image_to_md.call_count == 2

def test_import_supernote_directory_core(temp_dir):
    directory = temp_dir
    output = temp_dir
    template_path = None

    note_file = os.path.join(directory, "test.note")
    with open(note_file, "w") as f:
        f.write("test content")

    with patch("sn2md.importer.import_supernote_file_core") as mock_import_file:
        import_supernote_directory_core(directory, output, template_path, force=True)
        assert mock_import_file.call_count == 2
        mock_import_file.assert_any_call(note_file, output, template_path, True)
