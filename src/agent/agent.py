import os
import re
from typing import List, Dict, Any, Optional
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger


class ReActAgent:

    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.history = []
        self.user_context = ""  # Can be set by caller to include user profile/preferences
        self.tool_map = self._build_tool_map(tools)

    def _build_tool_map(self, tools: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        tool_map: Dict[str, Dict[str, Any]] = {}
        for raw_tool in tools:
            if not isinstance(raw_tool, dict):
                continue
            name = str(raw_tool.get("name", "")).strip()
            if not name:
                continue
            description = str(raw_tool.get("description", "")).strip() or "No description provided."
            fn = (
                raw_tool.get("callable")
                or raw_tool.get("func")
                or raw_tool.get("function")
                or raw_tool.get("fn")
            )
            tool_map[name] = {"name": name, "description": description, "callable": fn}
        return tool_map

    def get_system_prompt(self) -> str:
        if self.tool_map:
            tool_descriptions = "\n".join(
                [f"- {t['name']}: {t['description']}" for t in self.tool_map.values()]
            )
        else:
            tool_descriptions = "- No tools available."

        user_context_section = f"\n{self.user_context}" if self.user_context else ""

        return f"""
You are a travel and hotel assistant. You have access to the following tools:
{tool_descriptions}
{user_context_section}

IMPORTANT: You MUST use tools whenever the question involves:
- Distance or travel between cities → use get_distance
- Finding or recommending hotels → use search_hotels
- Hotel details → use get_hotel_details
- Hotel reviews → use get_hotel_reviews
- Booking a room → use book_hotel
- Checking or cancelling a booking → use get_booking_info or cancel_booking

Never answer travel or hotel questions from memory. Always call the relevant tool first.

Use the following format:
Thought: your line of reasoning and which tool to call.
Action: tool_name(argument1, argument2)
Observation: result of the tool call.
... (repeat Thought/Action/Observation as needed)
Final Answer: your final response to the user, based on the tool results.

Rules:
- Always start with a Thought.
- If NO tool is relevant, respond with ONLY: Final Answer: <your answer>
- Always end with Final Answer once you have enough information.
"""

    def _extract_final_answer(self, llm_text: str) -> Optional[str]:
        match = re.search(r"Final\s*Answer\s*:\s*(.*)", llm_text, flags=re.IGNORECASE | re.DOTALL)
        if not match:
            return None
        return match.group(1).strip()

    def _extract_action(self, llm_text: str) -> Optional[Dict[str, str]]:
        action_match = re.search(
            r"Action\s*:\s*([a-zA-Z_][\w]*)\((.*)\)", llm_text, flags=re.IGNORECASE | re.DOTALL
        )
        if not action_match:
            return None
        return {
            "tool_name": action_match.group(1).strip(),
            "args":      action_match.group(2).strip(),
        }

    def run(self, user_input: str) -> str:
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})

        self.history.append({"role": "user", "content": user_input})
        final_answer = None
        steps = 0

        while steps < self.max_steps:
            result = self.llm.generate(self.history, system_prompt=self.get_system_prompt())
            self.history.append({"role": "assistant", "content": result})
            logger.log_event("LLM_OUTPUT", {"step": steps, "output": result})

            # 1. Explicit "Final Answer:" line
            final_answer = self._extract_final_answer(result)
            if final_answer:
                break

            # 2. Action -> tool call -> observation
            action = self._extract_action(result)
            if action:
                observation = self._execute_tool(action["tool_name"], action["args"])
                logger.log_event("TOOL_CALL", {
                    "tool": action["tool_name"],
                    "args": action["args"],
                    "result": observation,
                })
                self.history.append({
                    "role":    "user",
                    "content": f"Observation: {observation}",
                })
            else:
                # ✅ No Action and no Final Answer: the LLM gave a plain reply.
                # Treat it as the final answer instead of looping forever.
                final_answer = result.strip()
                break

            steps += 1

        if final_answer is None:
            final_answer = "I could not finish within max steps."

        logger.log_event("AGENT_END", {"steps": steps, "final_answer": final_answer})
        return final_answer

    def _execute_tool(self, tool_name: str, args: str) -> str:
        tool = self.tool_map.get(tool_name)
        if not tool:
            return f"Tool '{tool_name}' not found."
        fn = tool.get("callable")
        if not callable(fn):
            return f"Tool '{tool_name}' is not executable."
        try:
            parsed_args = [a.strip().strip('"').strip("'") for a in args.split(",") if a.strip()]
            return str(fn(*parsed_args))
        except Exception as exc:
            logger.log_event("TOOL_ERROR", {"tool": tool_name, "error": str(exc)})
            return f"Tool '{tool_name}' execution failed: {exc}"
