import os
from typing import Optional, Any
from openai import OpenAI


class DeepSeekClient:
    def __init__(self, api_key: Optional[str] = None):
        if api_key is None:
            api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError(
                "DeepSeek API Key 未设置，请设置 DEEPSEEK_API_KEY 环境变量"
            )

        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        self.model = "deepseek-chat"

    def chat(
        self, messages: list, temperature: float = 0.7, max_tokens: int = 4096
    ) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    def chat_with_functions(
        self, messages: list, functions: list, function_call: str = "auto"
    ) -> dict:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=functions,
            tool_choice=function_call if function_call != "auto" else "auto",
            temperature=0.0,
            max_tokens=4096,
        )

        message = response.choices[0].message

        result = {"content": message.content, "function_call": None, "tool_calls": []}

        if message.tool_calls:
            for call in message.tool_calls:
                result["tool_calls"].append(
                    {
                        "id": call.id,
                        "function": {
                            "name": call.function.name,
                            "arguments": call.function.arguments,
                        },
                    }
                )

        return result

    def chat_basic(
        self, messages: list, temperature: float = 0.0, max_tokens: int = 4096
    ) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content
