import json

from .api_client import OpenRouterClient, load_config
from .models import ChatMessage
from .system_prompt import SYSTEM_PROMPT
from .tools import build_tools, openai_tool_specs, local_answer


class WarehouseAssistant:
    def __init__(self, warehouse_tab, base_dir=None):
        self.adapter = __import__("ai_assistant.tools", fromlist=["WarehouseToolAdapter"]).WarehouseToolAdapter(warehouse_tab)
        self.tools = build_tools(self.adapter)
        self.client = OpenRouterClient(load_config(base_dir))
        self.history = []

    @property
    def online(self):
        return self.client.configured

    def clear(self):
        self.history.clear()

    def _execute_tool(self, name, arguments):
        fn = self.tools.get(name)
        if not fn:
            return {"error": f"Tool {name} is not registered."}
        try:
            return fn(**arguments)
        except Exception as exc:
            return {"error": f"Tool execution failed: {type(exc).__name__}: {exc}"}

    def ask(self, question):
        fallback = local_answer(question, self.adapter)
        if not self.online:
            return fallback or "AI Assistant Offline\n\nAPI key not configured. The warehouse simulation can still be used normally. I can answer common status questions locally."
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + self.history[-12:] + [{"role": "user", "content": question}]
        for _ in range(4):
            try:
                response = self.client.chat(messages, openai_tool_specs())
            except RuntimeError as exc:
                return fallback or f"The AI service is unavailable: {exc}\n\nThe warehouse simulation can still be used normally."
            choice = response.get("choices", [{}])[0]
            message = choice.get("message", {})
            tool_calls = message.get("tool_calls") or []
            if not tool_calls:
                answer = message.get("content") or "I could not produce a response."
                self.history.extend([{"role": "user", "content": question}, {"role": "assistant", "content": answer}])
                return answer
            messages.append(message)
            for call in tool_calls:
                fn = call.get("function", {})
                name = fn.get("name", "")
                try:
                    args = json.loads(fn.get("arguments") or "{}")
                except json.JSONDecodeError:
                    args = {}
                result = self._execute_tool(name, args)
                messages.append({"role": "tool", "tool_call_id": call.get("id", name), "name": name,
                                 "content": json.dumps(result, default=str)})
        return "The assistant reached its tool-call limit before completing the answer."
