import base64
from unittest.mock import mock_open, patch, Mock

import pytest

from sn2md.langchain_utils import encode_image, image_to_markdown


@patch("builtins.open", new_callable=mock_open, read_data=b"test_image_data")
def test_encode_image(mock_file):
    expected_result = base64.b64encode(b"test_image_data").decode("utf-8")
    result = encode_image("dummy_path")
    assert result == expected_result


@patch("sn2md.langchain_utils.encode_image", return_value="encoded_image_data")
@patch("sn2md.langchain_utils.OpenAI")
def test_image_to_markdown(openai_mock, mock_encode_image):
    mock_result = Mock()
    mock_choice = Mock()
    mock_choice.message.content = "mocked_markdown"
    mock_result.choices = [mock_choice]
    openai_mock.return_value.chat.completions.create.return_value = mock_result
    result = image_to_markdown("dummy_path", "dummy_context", "dummy_key", "dummy_model")
    assert result == "mocked_markdown"
    mock_encode_image.assert_called_once_with("dummy_path")
    openai_mock.assert_called_once()
