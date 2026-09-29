import json
import os
import urllib.error
import urllib.request
from typing import Any

from .models import AssistantConfig


def load_env_file(path=".env"):
    values = {}
    if not os.path.exists(path):
        return values
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def load_config(base_dir=None):
    base_dir = base_dir or os.getcwd()
    env = load_env_file(os.path.join(base_dir, ".env"))
    api_key = os.getenv("OPENROUTER_API_KEY", env.get("OPENROUTER_API_KEY", ""))
    model = os.getenv("OPENROUTER_MODEL", env.get("OPENROUTER_MODEL", "openrouter/free"))
    return AssistantConfig(api_key=api_key, model=model)


class OpenRouterClient:
    def __init__(self, config: AssistantConfig):
        self.config = config

    @property
    def configured(self):
        return bool(self.config.api_key)

    def chat(self, messages, tools=None):
        if not self.configured:
            raise RuntimeError("API key not configured")
        payload = {"model": self.config.model, "messages": messages}
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.config.base_url,
            data=data,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost",
                "X-Title": "SmartWarehouse AI Assistant",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            if exc.code == 401:
                raise RuntimeError("The AI Assistant API key was rejected.") from exc
            if exc.code == 429:
                raise RuntimeError("The free AI request limit has been reached temporarily.") from exc
            raise RuntimeError(f"AI service error ({exc.code}).") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise RuntimeError("The AI service is currently unreachable.") from exc
