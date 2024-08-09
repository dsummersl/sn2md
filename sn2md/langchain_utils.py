import base64
import io

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from PIL.Image import Image

TO_MARKDOWN_TEMPLATE = """
###
Context (what the last couple lines of the previous page were converted to markdown):
{context}
###
Convert the following image to markdown:
- If a diagram or image appears on the page, and is a simple diagram that the mermaid diagramming tool can achieve, create a mermaid codeblock of it.
- When it is unclear what an image is, don't output anything for it.
- Assume text is not in a codeblock. Do not wrap any text in codeblocks.
- Use $$, $ style math blocks for math equations.
"""

TO_TEXT_TEMPLATE = """
Convert the following image to text.
- If the image does not appear to be text, output a brief description (no more than 4 words), prepended with "Image: "
"""

chat = ChatOpenAI(model="gpt-4o-mini")


def pil_to_base64(image: Image) -> str:
    image_buffer = io.BytesIO()
    image.save(image_buffer, format="PNG")
    
    image_buffer.seek(0)
    return base64.b64encode(image_buffer.read()).decode("utf-8")


def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def convert_image(text: str, b64_image: str) -> str:
    result = chat.invoke(
        [
            HumanMessage(
                content=[
                    {
                        "type": "text",
                        "text": text
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "data:image/png;base64," + b64_image
                        },
                    },
                ]
            )
        ]
    )
    return str(result.content)


def image_to_markdown(path: str, context: str) -> str:
    return convert_image(TO_MARKDOWN_TEMPLATE.format(context=context), encode_image(path))


def image_to_text(image: Image) -> str:
    return convert_image(TO_TEXT_TEMPLATE, pil_to_base64(image))
