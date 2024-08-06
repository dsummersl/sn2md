import pytest
from unittest.mock import patch, mock_open
import base64
from sn2md.langchain_utils import encode_image, image_to_markdown

@patch("builtins.open", new_callable=mock_open, read_data=b"test_image_data")
def test_encode_image(mock_file):
    expected_result = base64.b64encode(b"test_image_data").decode("utf-8")
    result = encode_image("dummy_path")
    assert result == expected_result

@patch("sn2md.langchain_utils.encode_image", return_value="encoded_image_data")
@patch("sn2md.langchain_utils.chat.invoke")
def test_image_to_markdown(mock_chat_invoke, mock_encode_image):
    mock_chat_invoke.return_value.content = "mocked_markdown"
    result = image_to_markdown("dummy_path", "dummy_context")
    assert result == "mocked_markdown"
    mock_encode_image.assert_called_once_with("dummy_path")
    mock_chat_invoke.assert_called_once()

