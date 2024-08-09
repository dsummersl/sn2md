import os
from unittest.mock import MagicMock, patch

import pytest
import supernotelib as sn

from sn2md.supernote_utils import (convert_notebook_to_pngs,
                                   convert_pages_to_pngs, load_notebook)


@pytest.fixture
def mock_notebook():
    notebook = MagicMock(spec=sn.Notebook)
    notebook.get_total_pages.return_value = 3
    return notebook

def test_load_notebook():
    with patch("sn2md.supernote_utils.sn.load_notebook") as mock_load:
        mock_load.return_value = "mock_notebook"
        result = load_notebook("fake_path")
        mock_load.assert_called_once_with("fake_path")
        assert result == "mock_notebook"

def test_convert_pages_to_pngs(mock_notebook):
    mock_converter = MagicMock()
    mock_save_func = MagicMock()
    visibility_overlay = {"default": MagicMock()}
    result = convert_pages_to_pngs(mock_converter, 3, "fake_path", mock_save_func, visibility_overlay)
    assert len(result) == 3
    assert result[0] == "fake_path/fake_path_0.png"
    assert result[1] == "fake_path/fake_path_1.png"
    assert result[2] == "fake_path/fake_path_2.png"
    mock_save_func.assert_called()

def test_convert_notebook_to_pngs(mock_notebook):
    with patch("sn2md.supernote_utils.ImageConverter") as MockImageConverter:
        mock_converter_instance = MockImageConverter.return_value
        mock_converter_instance.convert.return_value = MagicMock()
        with patch("sn2md.supernote_utils.sn.converter.build_visibility_overlay") as mock_build_vo:
            mock_build_vo.return_value = {"default": MagicMock()}
            result = convert_notebook_to_pngs(mock_notebook, "fake_path")
            assert len(result) == 3
            assert result[0] == "fake_path/fake_path_0.png"
            assert result[1] == "fake_path/fake_path_1.png"
            assert result[2] == "fake_path/fake_path_2.png"
