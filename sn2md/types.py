from typing import TypedDict


class Config(TypedDict):
    prompt: str
    title_prompt: str
    template: str
    model: str
    openai_api_key: str
