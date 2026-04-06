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


# ── User Profile (Memory System) ─────────────────────────────────────────────

class UserProfile:
    """Tracks user preferences and details for the current session"""
    def __init__(self):
        self.preferences = {}  # hotel preferences
        self.bookings = []     # list of booking IDs
        self.visited_hotels = set()  # hotels user has asked about

    def to_context(self) -> str:
        """Format profile as context string for the agent"""
        context = "User Profile:\n"
        if self.preferences:
            context += f"- Preferences: {self.preferences}\n"
        if self.bookings:
            context += f"- Active Bookings: {', '.join(self.bookings)}\n"
        if self.visited_hotels:
            context += f"- Hotels Previously Viewed: {', '.join(sorted(self.visited_hotels))}\n"
        return context if context != "User Profile:\n" else ""


user_profile = UserProfile()

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

    # Extract and store details from user input for future reference
    user_input_lower = user_input.lower()
    if "budget" in user_input_lower or "price" in user_input_lower:
        user_profile.preferences["mentioned_budget"] = True
    if "5 star" in user_input_lower or "five star" in user_input_lower:
        user_profile.preferences["star_preference"] = 5
    elif "4 star" in user_input_lower or "four star" in user_input_lower:
        user_profile.preferences["star_preference"] = 4

    # Pass user context to agent before running (includes memory from conversation)
    agent.user_context = user_profile.to_context()

    # Keep conversation history across turns (memory enabled)
    reply = agent.run(user_input)
    print(f"Bot: {reply}\n")