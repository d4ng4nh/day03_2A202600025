# chatbot.py

import os
from dotenv import load_dotenv
from openai import OpenAI

from src.tools.geo_tools import tool_schema as geo_tool_schema
from src.tools.hotel_tools import (
    search_hotels, get_hotel_details,
    book_hotel, cancel_booking, get_booking_info,
    HOTEL_TOOLS,
)
from src.tools.get_hotel_reviews import get_hotel_reviews
from src.agent.agent import ReActAgent

load_dotenv()

# ── LLMProvider ───────────────────────────────────────────────────────────────

class LLMProvider:
    def __init__(self, client: OpenAI, model: str):
        self.client     = client
        self.model_name = model

    def generate(self, history: list, system_prompt: str = "") -> str:
        system_msg = [{"role": "system", "content": system_prompt}] if system_prompt else []
        response = self.client.chat.completions.create(
            model    = self.model_name,
            messages = system_msg + history,
        )
        return response.choices[0].message.content


# ── Logger stub ───────────────────────────────────────────────────────────────

class _SimpleLogger:
    def log_event(self, event: str, data: dict):
        print(f"[LOG] {event}: {data}")

import src.telemetry.logger as _log_module
_log_module.logger = _SimpleLogger()


# ── Tool Registry ─────────────────────────────────────────────────────────────
# Every tool needs: "name", "description", and one of "fn"/"function"/"callable"
# agent._build_tool_map() already handles all three key names.

tools = [
    # 1. Geo distance tool (already uses "fn" key)
    geo_tool_schema,

    # 2. Hotel tools (already use "function" key via HOTEL_TOOLS list)
    *HOTEL_TOOLS,

    # 3. Hotel reviews tool (defined inline here)
    {
        "name":        "get_hotel_reviews",
        "description": "Get customer review summary and average rating for a hotel by its ID (e.g. HCM001, HAN002, DAD003).",
        "fn":          get_hotel_reviews,
    },
]


# ── Bootstrap ─────────────────────────────────────────────────────────────────

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
llm           = LLMProvider(openai_client, model="gpt-4o")
agent         = ReActAgent(llm, tools, max_steps=6)


# ── Chat loop ─────────────────────────────────────────────────────────────────

print("Chatbot ready. Type 'exit' to quit.")
print("Tools loaded:", [t["name"] for t in tools], "\n")

while True:
    try:
        user_input = input("You: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye!")
        break

    if not user_input:
        continue

    if user_input.lower() in {"exit", "quit"}:
        print("Goodbye!")
        break

    agent.history = []          # reset history each turn
    reply = agent.run(user_input)
    print(f"Bot: {reply}\n")