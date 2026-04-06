"""
ReAct Agent - Hoàn chỉnh với vòng lặp Thought-Action-Observation
"""

import re
import json
import logging
from typing import List, Dict, Any, Optional
from src.core.llm_provider import LLMProvider

# Simple logger fallback nếu chưa có telemetry module
try:
    from src.telemetry.logger import logger
except ImportError:
    class _SimpleLogger:
        def log_event(self, event, data=None):
            logging.info(f"[{event}] {data}")
    logger = _SimpleLogger()


class ReActAgent:
    """
    ReAct Agent: Thought → Action → Observation → ... → Final Answer
    """

    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 7):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.history = []

    def get_system_prompt(self) -> str:
        tool_descriptions = "\n".join(
            [f"- {t['name']}: {t['description']}\n  Example: {t['name']}({t.get('args_example','')})"
             for t in self.tools]
        )
        return f"""You are a helpful hotel booking assistant. You have access to the following tools:

{tool_descriptions}

Always follow this format STRICTLY:

Thought: <your reasoning about what to do next>
Action: <tool_name>(<key="value", ...>)
Observation: <result of the action - provided by the system>
... (repeat Thought/Action/Observation as many times as needed)
Final Answer: <your final response to the user in a friendly, clear way>

Rules:
- Use tools whenever you need real data (search, book, cancel, look up).
- Parse arguments carefully from the user's message.
- After receiving an Observation, decide if you need another action or can answer.
- Always end with "Final Answer:" once you have enough information.
- Be friendly and speak in the same language as the user.
- For dates, always use YYYY-MM-DD format.
"""

    def run(self, user_input: str) -> str:
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})

        # Build conversation: accumulate full context across steps
        messages_so_far = user_input
        steps = 0
        full_trace = []

        while steps < self.max_steps:
            # ── Step 1: Ask LLM for next Thought + Action ──
            result = self.llm.generate(messages_so_far, system_prompt=self.get_system_prompt())
            response_text = result["content"]
            full_trace.append(f"[Step {steps+1}]\n{response_text}")

            # ── Step 2: Check for Final Answer ──
            if "Final Answer:" in response_text:
                final = response_text.split("Final Answer:")[-1].strip()
                logger.log_event("AGENT_END", {"steps": steps + 1, "status": "final_answer"})
                self._print_trace(full_trace)
                return final

            # ── Step 3: Parse Action ──
            action_match = re.search(r"Action:\s*(\w+)\((.*)?\)", response_text, re.DOTALL)
            if not action_match:
                # No action found - let LLM continue
                messages_so_far += f"\n{response_text}\nObservation: No action detected. Please provide a Final Answer or call a tool."
                steps += 1
                continue

            tool_name = action_match.group(1).strip()
            args_str = action_match.group(2).strip()

            # ── Step 4: Execute Tool ──
            observation = self._execute_tool(tool_name, args_str)

            # ── Step 5: Append Observation to context ──
            messages_so_far += f"\n{response_text}\nObservation: {observation}"
            full_trace.append(f"Observation: {observation}")
            steps += 1

        # Max steps reached
        logger.log_event("AGENT_END", {"steps": steps, "status": "max_steps_reached"})
        self._print_trace(full_trace)
        return "Xin lỗi, tôi không thể hoàn thành yêu cầu trong số bước cho phép. Vui lòng thử lại với yêu cầu cụ thể hơn."

    def _execute_tool(self, tool_name: str, args_str: str) -> str:
        """Parse arguments and call the matching tool function."""
        for tool in self.tools:
            if tool["name"] == tool_name:
                fn = tool.get("function")
                if fn is None:
                    return f"Tool '{tool_name}' has no implementation."
                try:
                    kwargs = self._parse_args(args_str)
                    return fn(**kwargs)
                except TypeError as e:
                    return json.dumps({"error": f"Wrong arguments for {tool_name}: {str(e)}"})
                except Exception as e:
                    return json.dumps({"error": f"Tool error: {str(e)}"})
        return json.dumps({"error": f"Tool '{tool_name}' not found."})

    def _parse_args(self, args_str: str) -> Dict[str, Any]:
        """
        Parse key=value argument string into a dict.
        Handles: strings ("value"), integers, floats.
        Example: 'city="Hanoi", checkin="2025-08-01", num_rooms=2'
        """
        kwargs = {}
        if not args_str.strip():
            return kwargs

        # Match key="value" or key=number patterns
        pattern = re.findall(r'(\w+)\s*=\s*("(?:[^"\\]|\\.)*"|\d+\.?\d*)', args_str)
        for key, value in pattern:
            value = value.strip()
            if value.startswith('"') and value.endswith('"'):
                kwargs[key] = value[1:-1]  # strip quotes
            else:
                try:
                    kwargs[key] = int(value)
                except ValueError:
                    try:
                        kwargs[key] = float(value)
                    except ValueError:
                        kwargs[key] = value
        return kwargs

    def _print_trace(self, trace: List[str]) -> None:
        """Print the full reasoning trace for debugging."""
        print("\n" + "="*60)
        print("🔍 AGENT REASONING TRACE")
        print("="*60)
        for line in trace:
            print(line)
        print("="*60 + "\n")