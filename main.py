"""
main.py - Chạy Hotel Booking Agent
Usage: python main.py
"""

import os
from dotenv import load_dotenv
from src.core.openai_provider import OpenAIProvider
from src.agent.agent import ReActAgent
from src.tools.hotel_tools import HOTEL_TOOLS

load_dotenv()  # Đọc API key từ .env

# ── Màu terminal ──────────────────────────────────────────
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

BANNER = f"""
{CYAN}{BOLD}╔══════════════════════════════════════════════╗
║   🏨  HOTEL BOOKING AI AGENT  🏨              ║
║   Powered by OpenAI + ReAct Framework        ║
╚══════════════════════════════════════════════╝{RESET}

{YELLOW}Gợi ý câu hỏi:{RESET}
  • Tìm khách sạn ở Hà Nội từ 2025-08-01 đến 2025-08-05
  • Tìm khách sạn 5 sao ở Đà Nẵng, giá dưới 500$/đêm
  • Đặt phòng tại HN001 cho Nguyen Van A từ 2025-08-01 đến 2025-08-03
  • Xem chi tiết khách sạn SGN001
  • Huỷ đặt phòng BK12345
  • exit / quit để thoát

"""

def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Lỗi: Chưa đặt OPENAI_API_KEY trong file .env")
        print("   Thêm dòng:  OPENAI_API_KEY=sk-...")
        return

    # Khởi tạo LLM + Agent
    llm = OpenAIProvider(model_name="gpt-4o", api_key=api_key)
    agent = ReActAgent(llm=llm, tools=HOTEL_TOOLS, max_steps=7)

    print(BANNER)

    while True:
        try:
            user_input = input(f"{CYAN}Bạn:{RESET} ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nTạm biệt! 👋")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "thoat", "thoát"):
            print("Tạm biệt! 👋")
            break

        print(f"\n{YELLOW}⏳ Đang xử lý...{RESET}\n")
        answer = agent.run(user_input)
        print(f"{GREEN}{BOLD}🤖 Agent:{RESET} {answer}\n")
        print("-" * 60)


if __name__ == "__main__":
    main()