import os
from typing import Callable
from unittest.mock import patch

import supernotelib as sn
from supernotelib.converter import ImageConverter, VisibilityOverlay


def load_notebook(path: str) -> sn.Notebook:
    return sn.load_notebook(path)


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
    # TODO ideally decoder would support decoding these titles directly - make a PR on supernotelib!
    with patch('supernotelib.decoder.fileformat') as ff_mock:
        titlerect = title.metadata['TITLERECT'].split(',')
        ff_mock.PAGE_WIDTH = int(titlerect[2])
        ff_mock.PAGE_HEIGHT = int(titlerect[3])
        return image_converter._create_image_from_decoder(decoder, binary)

