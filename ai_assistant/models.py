from dataclasses import dataclass
from typing import Any


@dataclass
class ToolResult:
    name: str
    data: Any


@dataclass
class AssistantConfig:
    api_key: str = ""
    model: str = "openrouter/free"
    base_url: str = "https://openrouter.ai/api/v1/chat/completions"
    timeout_seconds: int = 30


@dataclass
class ChatMessage:
    role: str
    content: str
