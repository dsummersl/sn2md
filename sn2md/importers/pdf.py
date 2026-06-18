import os
import pymupdf
from supernotelib import Notebook
from sn2md.types import ImageExtractor


class PDFExtractor(ImageExtractor):
    def extract_images(self, filename: str, output_path: str) -> list[str]:
        file_name = output_path + "/" + os.path.basename(output_path) + ".png"
        basename, extension = os.path.splitext(file_name)
        doc = pymupdf.open(filename)
        max_digits = len(str(doc.page_count))
        files = []
        for page_num in range(doc.page_count):
            page = doc[page_num]
            numbered_filename = basename + "_" + str(page_num).zfill(max_digits) + extension
            pixmap = page.get_pixmap(dpi=150)
            pixmap.save(numbered_filename)
            files.append(numbered_filename)
        return files

    def get_notebook(self, filename: str) -> Notebook | None:
        # TODO: this is correct, but really we're talking about metadata of this specific extractor type - for notebooks its one thing, for PDFs its another...
        return None
