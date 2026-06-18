from unittest.mock import MagicMock, patch

import pytest
import supernotelib as sn

from pathlib import Path

from sn2md.importers.note import (convert_notebook_to_pngs,
                                   convert_pages_to_pngs, load_notebook)

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures"


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


def test_load_real_notebook_fixture(tmp_path):
    fixture = FIXTURE_DIR / "20260618_074222.note"
    assert fixture.exists(), f"Fixture not found: {fixture}"

    notebook = load_notebook(str(fixture))
    assert notebook is not None
    assert notebook.get_total_pages() > 0

    pngs = convert_notebook_to_pngs(notebook, str(tmp_path))
    assert len(pngs) == notebook.get_total_pages()

    for png_path in pngs:
        assert Path(png_path).exists()
        assert Path(png_path).stat().st_size > 0
