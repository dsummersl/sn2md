import logging
import os
from typing import Callable
from unittest.mock import patch

from sn2md.types import ImageExtractor

import supernotelib as sn
from supernotelib import color
from supernotelib.converter import ImageConverter, VisibilityOverlay

logger = logging.getLogger(__name__)


def load_notebook(path: str) -> sn.Notebook:
    return sn.load_notebook(path)


def _create_color_bytearray_with_fallback(self, mode, colormap, color_code, length):
    """Backport of RattaRleX2Decoder's fallback to the base RattaRleDecoder:
    title regions contain anti-aliased grayscale codes absent from the base
    colormap; use the raw code value instead of crashing on a None lookup."""
    if mode == color.MODE_RGB:
        c = colormap.get(color_code)
        if c is not None:
            r, g, b = color.get_rgb(c)
        else:
            r, g, b = (color_code, color_code, color_code)
        return bytearray((r, g, b,)) * length
    c = colormap.get(color_code)
    if c is None:
        c = color_code
    return bytearray((c,)) * length


def convert_pages_to_pngs(
    converter: ImageConverter,
    total: int,
    path: str,
    save_func: Callable,
    visibility_overlay: dict[str, VisibilityOverlay],
) -> list[str]:
    file_name = path + "/" + os.path.basename(path) + ".png"
    basename, extension = os.path.splitext(file_name)
    max_digits = len(str(total))
    files = []
    for i in range(total):
        numbered_filename = basename + "_" + str(i).zfill(max_digits) + extension
        img = converter.convert(i, visibility_overlay)
        save_func(img, numbered_filename)
        files.append(numbered_filename)
    return files


def convert_notebook_to_pngs(notebook: sn.Notebook, path: str) -> list[str]:
    converter = ImageConverter(notebook)
    bg_visibility = VisibilityOverlay.DEFAULT
    vo = sn.converter.build_visibility_overlay(background=bg_visibility)

    def save(img, file_name):
        img.save(file_name, format="PNG")

    return convert_pages_to_pngs(converter, notebook.get_total_pages(), path, save, vo)


def convert_binary_to_image(notebook, title):
    page = notebook.get_page(title.get_page_number())
    binary = title.get_content()

    image_converter = sn.converter.ImageConverter(notebook)
    decoder = image_converter.find_decoder(page)
    titlerect = title.metadata["TITLERECT"].split(",")
    # TODO ideally decoder would support decoding these titles directly - make a PR on supernotelib!
    with (
        patch.object(notebook, "get_width") as width_mock,
        patch.object(notebook, "get_height") as height_mock,
        patch.object(
            type(decoder),
            "_create_color_bytearray",
            _create_color_bytearray_with_fallback,
        ),
    ):
        width_mock.return_value = int(titlerect[2])
        height_mock.return_value = int(titlerect[3])
        return image_converter._create_image_from_decoder(decoder, binary)


class NotebookExtractor(ImageExtractor):
    def extract_images(self, filename: str, output_path: str) -> list[str]:
        notebook = load_notebook(filename)
        return convert_notebook_to_pngs(notebook, output_path)

    def get_notebook(self, filename: str) -> sn.Notebook | None:
        return load_notebook(filename)
