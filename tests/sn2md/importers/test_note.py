from unittest.mock import MagicMock, patch

import pytest
import supernotelib as sn
from supernotelib import color

from sn2md.importers.note import (_create_color_bytearray_with_fallback,
                                   convert_notebook_to_pngs,
                                   convert_pages_to_pngs, load_notebook)


@pytest.fixture
def mock_notebook():
    notebook = MagicMock(spec=sn.Notebook)
    notebook.get_total_pages.return_value = 3
    return notebook

def test_load_notebook():
    with patch("sn2md.importers.note.sn.load_notebook") as mock_load:
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
    with patch("sn2md.importers.note.ImageConverter") as MockImageConverter:
        mock_converter_instance = MockImageConverter.return_value
        mock_converter_instance.convert.return_value = MagicMock()
        with patch("sn2md.importers.note.sn.converter.build_visibility_overlay") as mock_build_vo:
            mock_build_vo.return_value = {"default": MagicMock()}
            result = convert_notebook_to_pngs(mock_notebook, "fake_path")
            assert len(result) == 3
            assert result[0] == "fake_path/fake_path_0.png"
            assert result[1] == "fake_path/fake_path_1.png"
            assert result[2] == "fake_path/fake_path_2.png"


def test_color_bytearray_fallback_known_grayscale():
    # A code present in the colormap delegates to its mapped value.
    colormap = {0x61: 0x00}
    result = _create_color_bytearray_with_fallback(None, "L", colormap, 0x61, 3)
    assert result == bytearray((0x00,)) * 3


def test_color_bytearray_fallback_unknown_grayscale():
    # An unknown code uses the raw code value instead of crashing on None.
    result = _create_color_bytearray_with_fallback(None, "L", {}, 0x7F, 4)
    assert result == bytearray((0x7F,)) * 4


def test_color_bytearray_fallback_unknown_rgb():
    # In RGB mode an unknown code becomes a (code, code, code) gray triple.
    result = _create_color_bytearray_with_fallback(None, color.MODE_RGB, {}, 0x42, 2)
    assert result == bytearray((0x42, 0x42, 0x42)) * 2
