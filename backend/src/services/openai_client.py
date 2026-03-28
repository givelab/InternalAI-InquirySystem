"""
OpenAI API の薄いラッパー。
LangChain 等のフレームワークは使用せず openai ライブラリを直接使う。
"""

from openai import OpenAI

from src.settings import settings

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.openai_api_key)
    return _client


def chat_completion(messages: list[dict[str, str]]) -> str:
    """
    messages: OpenAI Chat Completions API 形式のリスト
      [{"role": "system"|"user"|"assistant", "content": "..."}]
    """
    response = _get_client().chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,  # type: ignore[arg-type]
        temperature=0.3,
    )
    return response.choices[0].message.content or ""
