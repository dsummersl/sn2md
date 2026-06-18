import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from sn2md.importers.pdf import PDFExtractor


@pytest.fixture
def pdf_file():
    # Create a temporary PDF file for testing
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        tmp.write(b'fake pdf content')
        return tmp.name


@pytest.fixture
def output_dir():
    # Create a temporary directory for output
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


@patch('pymupdf.open')
def test_extract_images(mock_open, pdf_file, output_dir):
    # Arrange
    extractor = PDFExtractor()
    
    # Mock PDF document with 2 pages
    mock_doc = MagicMock()
    mock_doc.page_count = 2
    
    # Mock pages
    mock_page1 = MagicMock()
    mock_page1.number = 0
    mock_page2 = MagicMock()
    mock_page2.number = 1
    
    mock_doc.__getitem__.side_effect = lambda i: [mock_page1, mock_page2][i]
    mock_open.return_value = mock_doc

    # Mock pixmaps
    mock_pixmap1 = MagicMock()
    mock_pixmap2 = MagicMock()
    mock_page1.get_pixmap.return_value = mock_pixmap1
    mock_page2.get_pixmap.return_value = mock_pixmap2

    # Act
    result = extractor.extract_images(pdf_file, output_dir)

    # Assert
    assert len(result) == 2
    expected_base = os.path.join(output_dir, os.path.basename(output_dir))
    assert result == [
        f"{expected_base}_0.png",
        f"{expected_base}_1.png"
    ]
    
    # Verify mocks were called correctly
    mock_open.assert_called_once_with(pdf_file)
    mock_page1.get_pixmap.assert_called_once_with(dpi=150)
    mock_page2.get_pixmap.assert_called_once_with(dpi=150)
    mock_pixmap1.save.assert_called_once_with(f"{expected_base}_0.png")
    mock_pixmap2.save.assert_called_once_with(f"{expected_base}_1.png")


def test_get_notebook():
    extractor = PDFExtractor()
    assert extractor.get_notebook("any_file.pdf") is None
