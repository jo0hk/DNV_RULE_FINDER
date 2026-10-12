"""
llm.py — LLM API를 호출하는 부분만 모아 둔 파일
"""
import os

import config 

KEY_NAMES = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
}
DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-5-5",
    "openai": "gpt-6.1-sol",
    "gemini": "gemini-3.5-flash-lite",
}


def pick_provider():
    """.env에 LLM_PROVIDER가 있으면 그것을, 없으면 키가 채워진 회사를 고른다"""
    chosen = os.getenv("LLM_PROVIDER", "").strip().lower()
    if chosen:
        return chosen
    for provider, key_name in KEY_NAMES.items():
        if os.getenv(key_name):
            return provider
    return None 


PROVIDER = pick_provider()
MODEL = os.getenv("LLM_MODEL") or DEFAULT_MODELS.get(PROVIDER)


def chat(system, user):
    """system(역할·규칙)과 user(질문) 글을 보내고, 모델의 답변 글을 돌려받는다"""
    if PROVIDER == "anthropic":
        import anthropic
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(block.text for block in response.content if block.type == "text")

    if PROVIDER == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.responses.create(model=MODEL, instructions=system, input=user)
        return response.output_text

    if PROVIDER == "gemini":
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        response = client.models.generate_content(
            model=MODEL,
            contents=user,
            config=types.GenerateContentConfig(
                system_instruction=system,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            ),
        )
        return response.text

    raise SystemExit(f"알 수 없는 LLM_PROVIDER 입니다: {PROVIDER} (anthropic / openai / gemini 중 하나)")
