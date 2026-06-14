import base64
import os
import tempfile
from datetime import datetime
from unittest.mock import Mock, mock_open, patch

import pytest

from sn2md.importer import create_notebook_context

from sn2md.importer import (
    import_supernote_directory_core,
    import_supernote_file_core,
    verify_metadata_file,
)
from sn2md.types import Config


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname


@pytest.mark.parametrize(
    "output_path_template,image_output_path_template,expected_output_dir,expected_image_dir,expected_image_names",
    [
        # Default: images and output in same directory
        ("{{file_basename}}", "{{file_basename}}", "test", "test", ["page1.png", "page2.png"]),
        # Images in subdirectory relative to output
        (
            "{{file_basename}}",
            "{{file_basename}}/images",
            "test",
            "test/images",
            ["images/page1.png", "images/page2.png"],
        ),
        # Images in completely different directory
        (
            "notes/{{file_basename}}",
            "images/{{file_basename}}",
            "notes/test",
            "images/test",
            ["../../images/test/page1.png", "../../images/test/page2.png"],
        ),
        # Images at root level, output in subdirectory
        (
            "notes/{{file_basename}}",
            "{{file_basename}}",
            "notes/test",
            "test",
            ["../../test/page1.png", "../../test/page2.png"],
        ),
    ],
)
def test_import_supernote_file_core(
    temp_dir,
    output_path_template,
    image_output_path_template,
    expected_output_dir,
    expected_image_dir,
    expected_image_names,
):
    filename = os.path.join(temp_dir, "test.note")
    output = temp_dir

    with open(filename, "w") as f:
        _ = f.write("test content")

    with (
        patch("sn2md.importer.check_metadata_file") as mock_check_metadata,
        patch("sn2md.importer.image_to_markdown") as mock_image_to_md,
        patch("sn2md.importer.write_metadata_file") as mock_write_metadata,
        patch("builtins.open", mock_open()) as _,
        patch("uuid.uuid4") as mock_uuid,
        patch("os.rename") as mock_rename,
        patch("os.makedirs") as mock_makedirs,
        patch("shutil.rmtree") as _,
    ):
        mock_uuid.return_value.hex = "test-uuid"
        mock_extractor = Mock()
        mock_notebook = Mock()
        mock_keyword = Mock()
        mock_keyword.get_page_number.return_value = 0
        mock_keyword.get_content.return_value = b"some keyword"
        mock_notebook.keywords = [mock_keyword]
        mock_notebook.titles = []
        mock_notebook.links = []

        mock_image_to_md.side_effect = ["markdown1", "markdown2"]

        config = Config(
            output_path_template=output_path_template,
            output_filename_template="{{file_basename}}.md",
            image_output_path_template=image_output_path_template,
            prompt="TO_MARKDOWN_TEMPLATE",
            title_prompt="TO_TEXT_TEMPLATE",
            template="{{markdown}}",
            model="mock-model",
            api_key="mock-key",
        )

        mock_extractor.get_notebook.return_value = mock_notebook
        mock_extractor.extract_images.return_value = ["page1.png", "page2.png"]

        import_supernote_file_core(
            mock_extractor, filename, output, config, force=True, progress=False
        )

        mock_check_metadata.assert_not_called()
        assert mock_image_to_md.call_count == 2
        mock_write_metadata.assert_called_once()

        # Verify images were moved to the correct directory
        assert mock_rename.call_count == 2
        rename_calls = [call[0] for call in mock_rename.call_args_list]
        expected_full_image_dir = os.path.join(temp_dir, expected_image_dir)
        assert ("page1.png", os.path.join(expected_full_image_dir, "page1.png")) in rename_calls
        assert ("page2.png", os.path.join(expected_full_image_dir, "page2.png")) in rename_calls

        # Verify makedirs was called for both output and image directories
        makedirs_calls = [call[0][0] for call in mock_makedirs.call_args_list]
        assert os.path.join(temp_dir, expected_output_dir) in makedirs_calls
        assert expected_full_image_dir in makedirs_calls


def test_import_supernote_file_core_non_notebook(temp_dir):
    filename = os.path.join(temp_dir, "test.note")
    output = temp_dir

    with open(filename, "w") as f:
        _ = f.write("test content")

    with (
        patch("sn2md.importer.check_metadata_file") as mock_check_metadata,
        patch("sn2md.importer.image_to_markdown") as mock_image_to_md,
        patch("sn2md.importer.write_metadata_file") as mock_write_metadata,
        patch("sn2md.importer.os.rename") as _,
        patch("builtins.open", mock_open()) as _,
        patch("uuid.uuid4") as mock_uuid,
    ):
        mock_uuid.return_value.hex = "test-uuid"
        mock_extractor = Mock()
        mock_image_to_md.side_effect = ["markdown1", "markdown2"]

        config = Config()

        mock_extractor.get_notebook.return_value = None
        mock_extractor.extract_images.return_value = ["page1.png", "page2.png"]

        import_supernote_file_core(
            mock_extractor, filename, output, config, force=True, progress=False
        )

        mock_check_metadata.assert_not_called()
        assert mock_image_to_md.call_count == 2
        mock_write_metadata.assert_called_once()


@pytest.mark.parametrize(
    "progress, force", [(True, True), (True, False), (False, True), (False, False)]
)
def test_import_supernote_directory_core(temp_dir, progress, force):
    directory = temp_dir
    output = temp_dir
    config = None

    note_file = os.path.join(directory, "test.note")
    with open(note_file, "w") as f:
        f.write("test content")

    with (
        patch("sn2md.importer.import_supernote_file_core") as mock_import_file,
        patch("sn2md.importer.tqdm") as mock_tqdm,
    ):
        mock_tqdm.side_effect = lambda x, **kwargs: x
        import_supernote_directory_core(directory, output, config, force=force, progress=progress)
        assert mock_import_file.call_count == 1
        assert mock_import_file.call_args_list[0][0][1:] == (
            note_file,
            output,
            config,
            force,
            progress,
            None,
        )
        assert mock_tqdm.called == progress


def test_create_notebook_context():
    mock_notebook = Mock()
    mock_link = Mock()
    mock_link.get_page_number.return_value = 1
    mock_link.get_type.return_value = 2  # web link
    mock_link.get_filepath.return_value = base64.standard_b64encode(b"https://example.com")
    mock_link.get_inout.return_value = 0  # outgoing link
    mock_notebook.links = [mock_link]

    mock_keyword = Mock()
    mock_keyword.get_page_number.return_value = 2
    mock_keyword.get_content.return_value = b"test keyword"
    mock_notebook.keywords = [mock_keyword]

    mock_title = Mock()
    mock_title.get_page_number.return_value = 3
    mock_title.metadata = {"TITLELEVEL": 1}
    mock_notebook.titles = [mock_title]

    config = Config(
        output_path_template="{{file_basename}}",
        output_filename_template="{{file_basename}}.md",
        prompt="TO_MARKDOWN_TEMPLATE",
        title_prompt="TO_TEXT_TEMPLATE",
        template="{{markdown}}",
        model="mock-model",
        api_key="mock-key",
    )

    with patch("sn2md.importer.image_to_text") as mock_image_to_text, patch(
        "sn2md.importer.convert_binary_to_image"
    ) as mock_convert_image:
        mock_image_to_text.return_value = "Test Title"

        context = create_notebook_context(mock_notebook, config, "gpt-4")

        assert len(context["links"]) == 1
        assert context["links"][0]["page_number"] == 1
        assert context["links"][0]["type"] == "web"
        assert context["links"][0]["name"] == "example.com"
        assert context["links"][0]["inout"] == "out"

        assert len(context["keywords"]) == 1
        assert context["keywords"][0]["page_number"] == 2
        assert context["keywords"][0]["content"] == "test keyword"

        assert len(context["titles"]) == 1
        assert context["titles"][0]["page_number"] == 3
        assert context["titles"][0]["content"] == "Test Title"
        assert context["titles"][0]["level"] == 1

        mock_image_to_text.assert_called_once()
        mock_convert_image.assert_called_once_with(mock_notebook, mock_title)


def test_create_notebook_context_skips_undecodable_title():
    mock_notebook = Mock()
    mock_notebook.links = []
    mock_notebook.keywords = []

    bad_title = Mock()
    bad_title.get_page_number.return_value = 1
    bad_title.metadata = {"TITLELEVEL": 1}

    good_title = Mock()
    good_title.get_page_number.return_value = 2
    good_title.metadata = {"TITLELEVEL": 1}

    mock_notebook.titles = [bad_title, good_title]

    config = Config(
        output_path_template="{{file_basename}}",
        output_filename_template="{{file_basename}}.md",
        prompt="TO_MARKDOWN_TEMPLATE",
        title_prompt="TO_TEXT_TEMPLATE",
        template="{{markdown}}",
        model="mock-model",
        api_key="mock-key",
    )

    with patch("sn2md.importer.image_to_text") as mock_image_to_text, patch(
        "sn2md.importer.convert_binary_to_image"
    ) as mock_convert_image:
        mock_image_to_text.return_value = "Good Title"
        # First title fails to decode, second succeeds.
        mock_convert_image.side_effect = [TypeError("boom"), Mock()]

        context = create_notebook_context(mock_notebook, config, "gpt-4")

        # The undecodable title is skipped, the import continues.
        assert len(context["titles"]) == 1
        assert context["titles"][0]["page_number"] == 2
        assert context["titles"][0]["content"] == "Good Title"
        mock_image_to_text.assert_called_once()
        assert mock_convert_image.call_count == 2


def test_verify_metadata_file(temp_dir):
    filename = os.path.join(temp_dir, "test.note")
    output = temp_dir

    with open(filename, "w") as f:
        _ = f.write("test content")

    config = Config(
        output_path_template="{{file_basename}}",
        output_filename_template="{{file_basename}}.md",
        prompt="TO_MARKDOWN_TEMPLATE",
        title_prompt="TO_TEXT_TEMPLATE",
        template="{{markdown}}",
        model="mock-model",
        api_key="mock-key",
    )

    with patch("sn2md.importer.check_metadata_file") as mock_check_metadata:
        verify_metadata_file(config, output, filename)
        mock_check_metadata.assert_called_once_with(os.path.join(output, "test"), filename)


def test_verify_metadata_file_nested_path(temp_dir):
    filename = os.path.join(temp_dir, "test.note")
    output = temp_dir

    with open(filename, "w") as f:
        _ = f.write("test content")

    config = Config(
        output_path_template="notes/{{ctime.strftime('%Y')}}/{{ctime.strftime('%m')}}/{{file_basename}}",
        output_filename_template="{{file_basename}}.md",
        prompt="TO_MARKDOWN_TEMPLATE",
        title_prompt="TO_TEXT_TEMPLATE",
        template="{{markdown}}",
        model="mock-model",
        api_key="mock-key",
    )

    expected_path = os.path.join(
        output,
        "notes",
        datetime.fromtimestamp(os.path.getctime(filename)).strftime("%Y"),
        datetime.fromtimestamp(os.path.getctime(filename)).strftime("%m"),
        "test",
    )

    with patch("sn2md.importer.check_metadata_file") as mock_check_metadata:
        verify_metadata_file(config, output, filename)
        mock_check_metadata.assert_called_once_with(expected_path, filename)
