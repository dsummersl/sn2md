import base64

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

TO_MARKDOWN_TEMPLATE = """
###
Context (what the last couple lines of the previous page were converted to markdown):
{context}
###
Convert the following page to markdown:
- If a diagram or image appears on the page, and is a simple diagram that the mermaid diagramming tool can achieve, create a mermaid codeblock of it.
- When it is unclear what an image is, don't output anything for it.
- Assume text is not in a codeblock. Do not wrap any text in codeblocks.
- Use $$, $ style math blocks for math equations.
"""

chat = ChatOpenAI(model="gpt-4o-mini")


def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def image_to_markdown(path: str, context: str) -> str:
    result = chat.invoke(
        [
            HumanMessage(
                content=[
                    {
                        "type": "text",
                        "text": TO_MARKDOWN_TEMPLATE.format(context=context),
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "data:image/png;base64," + encode_image(path)
                        },
                    },
                ]
            )
        ]
    )
    return str(result.content)
