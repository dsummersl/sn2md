import base64
import io

from openai import OpenAI
from PIL.Image import Image

TO_MARKDOWN_TEMPLATE = """###
Context (the last few lines of markdown from the previous page):
{context}
###
Convert the image to markdown:
- If there is a simple diagram that the mermaid syntax can achieve, create a mermaid codeblock of it.
- When it is unclear what an image is, don't output anything for it.
- Use $$, $ latex math blocks for math equations.
- Support Obsidian syntaxes and dataview "field:: value" syntax.
- Do not wrap text in codeblocks.
"""

TO_TEXT_TEMPLATE = """
Convert the following image to text.
- If the image does not appear to be text, output a brief description (no more than 4 words), prepended with "Image: "
"""


def pil_to_base64(image: Image) -> str:
    image_buffer = io.BytesIO()
    image.save(image_buffer, format="PNG")
    
    image_buffer.seek(0)
    return base64.b64encode(image_buffer.read()).decode("utf-8")


def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def convert_image(text: str, b64_image: str, openai_api_key: str, model: str) -> str:
    chat_client = OpenAI(api_key=openai_api_key)
    messages = [
        {"role": "user",
         "content": [
             {
                 "type": "text",
                 "text": text
             },
             {
                 "type": "image_url",
                 "image_url": {
                 "url": "data:image/png;base64," + b64_image
                 }
             }
         ]
         }
    ]
    response = chat_client.chat.completions.create(model = model, messages=messages)
    return response.choices[0].message.content


def image_to_markdown(path: str, context: str, openai_api_key: str, model: str, prompt: str) -> str:
    return convert_image(
        prompt.format(context=context),
        encode_image(path),
        openai_api_key,
        model
    )


def image_to_text(image: Image, openai_api_key: str, model: str) -> str:
    return convert_image(
        TO_TEXT_TEMPLATE,
        pil_to_base64(image),
        openai_api_key,
        model
    )
